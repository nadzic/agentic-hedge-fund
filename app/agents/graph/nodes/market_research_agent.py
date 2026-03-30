from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage

from app.agents.graph.state import HedgeFundState
from app.agents.services.llm import get_llm
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
    horizon = state["input"].horizon
    query = state["input"].query

    try:
        llm = get_llm().bind_tools([rag_tool, insider_tool])
        messages: list[Any] = [
            SystemMessage(
                content=(
                    "You are a market research tool-routing agent. "
                    "Decide if you should call rag_tool and/or insider_tool. "
                    "Use rag_tool for evidence and filing/news context. "
                    "Use insider_tool for insider buy/sell flow context. "
                    "You may call none, one, or both."
                )
            ),
            HumanMessage(content=f"Symbol: {symbol}\nHorizon: {horizon}\nQuery: {query}"),
        ]

        rag_raw: str | None = None
        insider_raw: str | None = None

        for _ in range(4):
            ai_message = llm.invoke(messages)
            messages.append(ai_message)

            tool_calls = getattr(ai_message, "tool_calls", None) or []
            if not tool_calls:
                break

            for call in tool_calls:
                tool_name = str(call.get("name", ""))
                tool_args = call.get("args")
                args = tool_args if isinstance(tool_args, dict) else {}
                args.setdefault("symbol", symbol)

                if tool_name == "rag_tool":
                    observation = str(rag_tool.invoke(args))
                    rag_raw = observation
                elif tool_name == "insider_tool":
                    observation = str(insider_tool.invoke(args))
                    insider_raw = observation
                else:
                    observation = json.dumps(
                        {"status": "error", "error": f"unknown tool {tool_name}"}
                    )

                messages.append(
                    ToolMessage(
                        content=observation,
                        tool_call_id=str(call.get("id", "tool_call")),
                    )
                )

        rag_payload = _safe_json(rag_raw)
        insider_payload = _safe_json(insider_raw)
        rag_context, rag_citations = _extract_rag_context(rag_payload)

        if insider_payload and insider_payload.get("status") == "ok":
            insider_line = (
                "Insider context: "
                f"score={insider_payload.get('score')}, "
                f"confidence={insider_payload.get('confidence')}, "
                f"reasoning={insider_payload.get('reasoning')}"
            )
            rag_context = f"{rag_context}\n\n{insider_line}" if rag_context else insider_line

        return {
            "rag_context": rag_context,
            "rag_citations": rag_citations,
            "warning": None,
            "error": None,
        }
    except Exception as exc:
        return {
            "rag_context": state.get("rag_context"),
            "rag_citations": state.get("rag_citations", []),
            "warning": f"market_research_agent fallback: {exc}",
            "error": None,
        }