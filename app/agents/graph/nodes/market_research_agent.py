from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any

from app.agents.graph.state import HedgeFundState
from app.agents.tools import insider_tool, rag_tool
from app.observability.tracing import observe


def _safe_json(raw: str | None) -> dict[str, Any] | None:
    if not raw:
        return None
    try:
        parsed = json.loads(raw)
    except Exception:
        return None
    return parsed if isinstance(parsed, dict) else None


def _extract_rag_context(payload: dict[str, Any] | None) -> tuple[str | None, list[str]]:
    if not payload or payload.get("status") != "ok":
        return None, []

    chunks = payload.get("chunks")
    if not isinstance(chunks, list) or not chunks:
        return None, []

    lines: list[str] = []
    citations: list[str] = []
    for chunk in chunks[:5]:
        if not isinstance(chunk, dict):
            continue
        text = str(chunk.get("text", "")).strip()
        rank = chunk.get("rank")
        if text:
            lines.append(f"[{rank}] {text}")
        citation = str(chunk.get("source_id") or chunk.get("url") or "").strip()
        if citation and citation not in citations:
            citations.append(citation)

    context = "\n\n".join(lines).strip() or None
    return context, citations


@observe(name="agents.graph.nodes.market_research_agent.market_research_agent")
def market_research_agent(state: HedgeFundState) -> Mapping[str, object | None]:
    symbol = state["input"].symbol.upper().strip()
    query = state["input"].query

    try:
        warnings: list[str] = []

        rag_raw: str | None = None
        try:
            rag_raw = str(
                rag_tool.invoke(
                    {
                        "query": query,
                        "symbol": symbol,
                        "top_k": 6,
                        "sparse_top_k": 12,
                        "alpha": 0.5,
                    }
                )
            )
        except Exception as exc:
            warnings.append(f"rag_tool failed: {exc}")

        insider_raw: str | None = None
        try:
            insider_raw = str(insider_tool.invoke({"symbol": symbol, "lookback_days": 30}))
        except Exception as exc:
            warnings.append(f"insider_tool failed: {exc}")

        rag_payload = _safe_json(rag_raw)
        insider_payload = _safe_json(insider_raw)
        rag_context, rag_citations = _extract_rag_context(rag_payload)

        if rag_payload and rag_payload.get("status") == "error":
            warnings.append(f"rag_tool error: {rag_payload.get('error')}")

        if insider_payload and insider_payload.get("status") == "ok":
            insider_line = (
                "Insider context: "
                f"score={insider_payload.get('score')}, "
                f"confidence={insider_payload.get('confidence')}, "
                f"reasoning={insider_payload.get('reasoning')}"
            )
            rag_context = f"{rag_context}\n\n{insider_line}" if rag_context else insider_line
        elif insider_payload and insider_payload.get("status") == "error":
            warnings.append(f"insider_tool error: {insider_payload.get('error')}")

        return {
            "rag_context": rag_context,
            "rag_citations": rag_citations,
            "warning": " | ".join(warnings) if warnings else None,
            "error": None,
        }
    except Exception as exc:
        return {
            "rag_context": state.get("rag_context"),
            "rag_citations": state.get("rag_citations", []),
            "warning": f"market_research_agent fallback: {exc}",
            "error": None,
        }