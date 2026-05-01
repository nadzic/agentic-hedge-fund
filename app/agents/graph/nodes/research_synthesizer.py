from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from app.agents.services.prompt_llm_service import invoke_prompt_json
from app.observability.tracing import observe

_DISCLAIMER = "This is not investment advice."
_MAX_SECTION_ITEMS = 5


def _source_url(ev: dict[str, Any]) -> str:
    return str(ev.get("source_url") or ev.get("source") or "").strip()


def _claim_text(ev: dict[str, Any]) -> str:
    return str(ev.get("claim") or ev.get("text") or "").strip()


def _as_list(value: Any) -> list[str]:
    if isinstance(value, list):
        out: list[str] = []
        for item in value:
            s = str(item).strip()
            if s:
                out.append(s)
        return out
    if value is None:
        return []
    s = str(value).strip()
    return [s] if s else []


def _quality_counts(selected: list[dict[str, Any]]) -> dict[str, int]:
    counts = {"strong": 0, "medium": 0, "weak": 0}
    for ev in selected:
        strength = str(ev.get("evidence_strength") or "").strip().lower()
        if strength in counts:
            counts[strength] += 1
        else:
            counts["weak"] += 1
    return counts


def _format_point(ev: dict[str, Any]) -> str:
    claim = _claim_text(ev)
    if not claim:
        return ""
    strength = str(ev.get("evidence_strength") or "unknown").strip().lower()
    fio = str(ev.get("fact_or_interpretation") or "interpretation").strip().lower()
    source_type = str(ev.get("source_type") or "unknown").strip()
    source = _source_url(ev)
    weak_label = " [WEAK SIGNAL]" if strength == "weak" else ""
    src = f" ({source})" if source else ""
    return f"{claim}{weak_label} [{strength} | {fio} | {source_type}]{src}"


def _unique_non_empty(items: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for item in items:
        key = item.strip().lower()
        if not key or key in seen:
            continue
        seen.add(key)
        out.append(item.strip())
    return out


def _bucket_selected(selected: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    buckets: dict[str, list[dict[str, Any]]] = {
        "what_changed": [],
        "what_matters_now": [],
        "bull_points": [],
        "bear_points": [],
        "what_to_watch_next": [],
    }
    for ev in selected:
        used_for = _as_list(ev.get("used_for"))
        for tag in used_for:
            if tag in buckets:
                buckets[tag].append(ev)
    return buckets


def _sorted_by_inclusion(selected: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(
        selected,
        key=lambda ev: (
            float(ev.get("inclusion_score") or 0.0),
            float(ev.get("confidence") or 0.0),
        ),
        reverse=True,
    )


def _render_section(title: str, points: list[str]) -> str:
    if not points:
        return f"{title}\n- No high-confidence selected evidence."
    bullets = "\n".join(f"- {item}" for item in points[:_MAX_SECTION_ITEMS])
    return f"{title}\n{bullets}"


def _format_citations(evidences: list[dict[str, Any]]) -> list[str]:
    citations: list[str] = []
    for ev in evidences:
        src = _source_url(ev)
        if src and src not in citations:
            citations.append(src)
    return citations


def _llm_synthesize_sections(
    company_name: str,
    symbol: str,
    selected: list[dict[str, Any]],
) -> dict[str, Any]:
    payload_evidences: list[dict[str, Any]] = []
    for ev in selected[:16]:
        payload_evidences.append(
            {
                "claim": _claim_text(ev),
                "source_url": _source_url(ev),
                "source_type": str(ev.get("source_type") or "").strip(),
                "evidence_strength": str(ev.get("evidence_strength") or "").strip(),
                "fact_or_interpretation": str(ev.get("fact_or_interpretation") or "").strip(),
                "used_for": _as_list(ev.get("used_for")),
                "inclusion_score": ev.get("inclusion_score"),
            }
        )

    result = invoke_prompt_json(
        prompt_filename="research_synthesizer.md",
        payload={
            "company_name": company_name,
            "symbol": symbol,
            "selected_evidences": payload_evidences,
        },
        output_schema_hint="""
{
  "executive_summary": "string",
  "what_changed": ["string"],
  "what_matters_most_now": ["string"],
  "bull_points": ["string"],
  "bear_points": ["string"],
  "what_to_watch_next": ["string"],
  "source_notes": ["string"],
  "disclaimer": "string"
}
""".strip(),
    )
    return result if isinstance(result, dict) else {}


@observe(name="agents.graph.nodes.research_synthesizer.research_synthesizer_node")
def research_synthesizer_node(state: Mapping[str, object]) -> dict[str, object | None]:
    """
    Produce a concise structured brief using only selected evidences.

    Output:
    - research_summary: str | None
    - research_citations: list[str]
    """
    try:
        company_name = str(state.get("company_name") or "").strip()
        symbol = str(state.get("symbol") or "").strip().upper()

        selected = state.get("selected_evidences")
        if not isinstance(selected, list):
            selected = state.get("selected_evidence")
        if not isinstance(selected, list) or not selected:
            summary = f"No evidence found for {company_name or symbol or 'the query'}."
            return {
                "research_summary": summary,
                "research_citations": [],
                "warning": state.get("warning"),
                "error": None,
            }

        selected_dicts = [ev for ev in selected if isinstance(ev, dict)]
        ranked = _sorted_by_inclusion(selected_dicts)
        quality = _quality_counts(ranked)

        llm_warning: str | None = None
        llm_sections: dict[str, Any] = {}
        try:
            llm_sections = _llm_synthesize_sections(company_name=company_name, symbol=symbol, selected=ranked)
        except Exception as exc:
            llm_warning = f"research_synthesizer LLM fallback: {exc}"

        if llm_sections:
            executive_summary = str(llm_sections.get("executive_summary") or "").strip()
            what_changed = _unique_non_empty(_as_list(llm_sections.get("what_changed")))
            what_matters = _unique_non_empty(_as_list(llm_sections.get("what_matters_most_now")))
            bull_points = _unique_non_empty(_as_list(llm_sections.get("bull_points")))
            bear_points = _unique_non_empty(_as_list(llm_sections.get("bear_points")))
            watch_next = _unique_non_empty(_as_list(llm_sections.get("what_to_watch_next")))
            source_notes = _unique_non_empty(_as_list(llm_sections.get("source_notes")))
        else:
            buckets = _bucket_selected(ranked)
            executive_candidates = [
                _claim_text(ev)
                for ev in ranked
                if _claim_text(ev) and str(ev.get("evidence_strength") or "").strip().lower() in {"strong", "medium"}
            ][:2]
            if not executive_candidates:
                executive_candidates = [_claim_text(ev) for ev in ranked if _claim_text(ev)][:2]
            executive_summary = (
                "; ".join(executive_candidates)
                if executive_candidates
                else f"Selected evidence for {company_name or symbol or 'the query'} was limited."
            )

            what_changed = _unique_non_empty([_format_point(ev) for ev in buckets["what_changed"]])
            what_matters = _unique_non_empty([_format_point(ev) for ev in buckets["what_matters_now"]])
            bull_points = _unique_non_empty([_format_point(ev) for ev in buckets["bull_points"]])
            bear_points = _unique_non_empty([_format_point(ev) for ev in buckets["bear_points"]])
            watch_next = _unique_non_empty([_format_point(ev) for ev in buckets["what_to_watch_next"]])
            source_notes = _unique_non_empty(
                [
                    f"{str(ev.get('source_type') or 'unknown').strip()}: {_source_url(ev)}"
                    for ev in ranked
                    if _source_url(ev)
                ]
            )

        if not executive_summary:
            executive_summary = f"Selected evidence for {company_name or symbol or 'the query'} was limited."
        if not what_changed:
            what_changed = _unique_non_empty([_format_point(ev) for ev in ranked[:2]])
        if not what_matters:
            what_matters = _unique_non_empty([_format_point(ev) for ev in ranked[2:4]])

        lines: list[str] = [
            f"Company: {company_name or 'Unknown'}",
            f"Ticker: {symbol or 'N/A'}",
            "",
            _render_section("1) Executive summary", [executive_summary]),
            "",
            _render_section("2) What changed in the latest results / reporting", what_changed),
            "",
            _render_section("3) What matters most now", what_matters),
            "",
            _render_section("4) Main bull points", bull_points),
            "",
            _render_section("5) Main bear points", bear_points),
            "",
            _render_section("6) What to watch next", watch_next),
            "",
            "7) Evidence quality summary",
            f"- strong: {quality['strong']}",
            f"- medium: {quality['medium']}",
            f"- weak: {quality['weak']} (clearly labeled when used)",
            "",
            _render_section("8) Source notes", source_notes),
            "",
            "9) Disclaimer",
            f"- {str(llm_sections.get('disclaimer') or _DISCLAIMER).strip()}",
        ]

        summary = "\n".join(lines).strip() or None
        research_brief: dict[str, Any] = {
            "company": company_name or None,
            "ticker": symbol or None,
            "reporting_context": "Latest available reporting context from selected evidence.",
            "executive_summary": executive_summary,
            "what_changed": what_changed[:_MAX_SECTION_ITEMS],
            "what_matters_most_now": what_matters[:_MAX_SECTION_ITEMS],
            "bull_points": bull_points[:_MAX_SECTION_ITEMS],
            "bear_points": bear_points[:_MAX_SECTION_ITEMS],
            "what_to_watch_next": watch_next[:_MAX_SECTION_ITEMS],
            "evidence_quality_summary": quality,
            "source_notes": source_notes[:8],
            "disclaimer": _DISCLAIMER,
        }

        return {
            "research_summary": summary,
            "research_brief": research_brief,
            "research_citations": _format_citations(ranked),
            "warning": " | ".join(
                part for part in [str(state.get("warning") or "").strip(), llm_warning] if part
            )
            or None,
            "error": None,
        }
    except Exception as exc:
        return {
            "research_summary": state.get("research_summary"),
            "research_brief": state.get("research_brief"),
            "research_citations": state.get("research_citations"),
            "warning": f"research_synthesizer fallback: {exc}",
            "error": None,
        }

