import argparse
import re
import sys
from pathlib import Path

import httpx
from bs4 import BeautifulSoup
from llama_index.core.schema import Document
from llama_index.readers.web import SimpleWebPageReader
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright

try:
    from app.rag.core.config import SOURCE_URLS
    from app.rag.core.constants import CHALLENGE_MARKERS
except ModuleNotFoundError:
    # Allow direct script execution: python app/rag/ingestion/url_ingestion.py
    repo_root = Path(__file__).resolve().parents[3]
    sys.path.append(str(repo_root))
    from app.rag.core.config import SOURCE_URLS
    from app.rag.core.constants import CHALLENGE_MARKERS


def _clean_text(raw_text: str) -> str:
    """Normalize whitespace and drop empty lines."""
    lines = [re.sub(r"\s+", " ", line).strip() for line in raw_text.splitlines()]
    return "\n".join(line for line in lines if line)


def _looks_like_challenge(text: str) -> bool:
    """Detect common anti-bot challenge pages from text markers."""
    lowered = text.lower()
    return any(marker in lowered for marker in CHALLENGE_MARKERS)


def _extract_playwright_text(page) -> str:
    """Extract readable text from likely content containers first."""
    selectors = ("article", "main", "[role='main']", ".article", ".content")
    for selector in selectors:
        try:
            candidate = page.locator(selector).first.inner_text(timeout=3_000).strip()
            if len(candidate) > 200:
                return candidate
        except PlaywrightTimeoutError:
            continue
    return page.locator("body").inner_text().strip()


def _extract_http_text(html: str) -> str:
    """Convert raw HTML into readable text using BeautifulSoup."""
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript", "svg"]):
        tag.decompose()
    root = soup.find("article") or soup.find("main") or soup.body
    if root is None:
        return ""
    return _clean_text(root.get_text(separator="\n", strip=True))


def _save_if_requested(path: str, content: str) -> None:
    """Persist content only when an output path is provided."""
    if not path:
        return
    Path(path).resolve().write_text(content, encoding="utf-8")


def ingest_url(
    url: str,
    text_out: str = "",
    html_out: str = "",
    headless: bool = True,
    manual_wait: int = 0,
    state_file: str = "",
) -> Document:
    """Ingest a URL into a LlamaIndex Document using progressive fallbacks.

    Order:
    1) LlamaIndex web reader
    2) Direct HTTP fetch + HTML parsing
    3) Playwright (best for JS-heavy or protected pages)
    """
    # 1) Fast path: LlamaIndex web reader
    try:
        docs = SimpleWebPageReader(html_to_text=True).load_data([url])
        if docs:
            text = _clean_text(docs[0].text)
            if text and not _looks_like_challenge(text):
                _save_if_requested(text_out, text)
                return Document(text=text, metadata={"source_url": url, "ingestion_method": "web_reader", "source_type": "url", "source_id": url, "source_name": url.split("/")[-1]})
    except Exception:
        # Playwright fallback handles blocked/JS-heavy pages.
        pass

    # 2) HTTP fallback: direct fetch + HTML parsing
    try:
        response = httpx.get(
            url,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
                ),
                "Accept-Language": "en-US,en;q=0.9",
            },
            timeout=30.0,
            follow_redirects=True,
        )
        if response.status_code < 400:
            html = response.text
            text = _extract_http_text(html)
            if text and not _looks_like_challenge(text) and not _looks_like_challenge(html):
                _save_if_requested(html_out, html)
                _save_if_requested(text_out, text)
                return Document(text=text, metadata={"source_url": url, "ingestion_method": "httpx", "source_type": "url", "source_id": url, "source_name": url.split("/")[-1]})
    except Exception:
        pass

    # 3) Robust fallback: Playwright
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        if state_file and Path(state_file).exists():
            # Reuse prior session/cookies to reduce repeated challenge prompts.
            context = browser.new_context(storage_state=str(Path(state_file).resolve()))
        else:
            context = browser.new_context()
        page = context.new_page()

        try:
            _ = page.goto(url, wait_until="domcontentloaded", timeout=60_000)
        except Exception as exc:
            context.close()
            browser.close()
            raise RuntimeError(f"Playwright navigation failed: {exc}") from exc
        try:
            page.wait_for_load_state("networkidle", timeout=10_000)
        except PlaywrightTimeoutError:
            pass

        if manual_wait > 0:
            # Optional wait for manual challenge solving in non-headless mode.
            try:
                page.wait_for_function(
                    "() => !document.title.toLowerCase().includes('just a moment')",
                    timeout=manual_wait * 1000,
                )
            except PlaywrightTimeoutError:
                pass

        html = page.content()
        text = _clean_text(_extract_playwright_text(page))

        if _looks_like_challenge(html) or _looks_like_challenge(text):
            context.close()
            browser.close()
            raise RuntimeError(
                "Challenge page detected. Retry with --no-headless --manual-wait 180 "
                "and solve verification in the opened browser."
            )

        if state_file:
            # Save session for the next run.
            context.storage_state(path=str(Path(state_file).resolve()))
        context.close()
        browser.close()

    _save_if_requested(html_out, html)
    _save_if_requested(text_out, text)
    return Document(text=text, metadata={"source_url": url, "ingestion_method": "playwright", "source_type": "url", "source_id": url, "source_name": url.split("/")[-1]})


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Ingest one URL with LlamaIndex + Playwright fallback.")
    parser.add_argument("--url", default="", help="URL to ingest.")
    parser.add_argument(
        "--url-key",
        default="",
        choices=sorted(SOURCE_URLS.keys()),
        help="Key from app.rag.core.config.SOURCE_URLS.",
    )
    parser.add_argument("--text-out", default="", help="Optional output .txt file.")
    parser.add_argument("--html-out", default="", help="Optional output .html file.")
    parser.add_argument(
        "--headless",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Run browser headless (default: true).",
    )
    parser.add_argument(
        "--manual-wait",
        type=int,
        default=0,
        help="Seconds to wait for manual verification in browser.",
    )
    parser.add_argument(
        "--state-file",
        default="",
        help="Optional Playwright storage state file for session reuse.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if not args.url and not args.url_key:
        raise ValueError("Provide either --url or --url-key.")
    if args.url and args.url_key:
        raise ValueError("Use only one of --url or --url-key.")

    target_url = args.url or SOURCE_URLS[args.url_key]
    doc = ingest_url(
        url=target_url,
        text_out=args.text_out,
        html_out=args.html_out,
        headless=args.headless,
        manual_wait=args.manual_wait,
        state_file=args.state_file,
    )
    print(f"Ingested URL with method: {doc.metadata.get('ingestion_method')}")
    print(f"Characters: {len(doc.text)}")


if __name__ == "__main__":
    main()
