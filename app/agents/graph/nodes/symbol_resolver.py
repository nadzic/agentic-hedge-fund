from __future__ import annotations

import re

from app.agents.graph.schemas import SignalInput
from app.agents.graph.state import HedgeFundState
from app.agents.services.insider.finnhub_client import search_symbol_by_company_name
from app.observability.tracing import observe

_SYMBOL_PATTERN = re.compile(r"^[A-Z]{1,5}$")
_QUERY_SYMBOL_PATTERN = re.compile(r"\b[A-Z]{1,5}\b")
_STOP_WORDS = {
    "please",
    "analyze",
    "analyse",
    "for",
    "the",
    "a",
    "an",
    "in",
    "on",
    "about",
    "to",
    "and",
    "swing",
    "intraday",
    "position",
    "trading",
    "trade",
    "stock",
    "what",
    "should",
    "would",
    "could",
    "can",
    "is",
    "it",
    "my",
    "me",
    "do",
    "you",
    "today",
    "now",
    "best",
    "idea",
}


def _is_valid_symbol(value: str) -> bool:
    return _SYMBOL_PATTERN.match(value) is not None


def _extract_lookup_candidates(query: str) -> list[str]:
    tokens = re.findall(r"[A-Za-z][A-Za-z0-9&.-]*", query.lower())
    filtered = [token for token in tokens if token not in _STOP_WORDS]
    if not filtered:
        return []

    candidates: list[str] = []
    joined = " ".join(filtered).strip()
    if joined:
        candidates.append(joined)

    for token in filtered:
        if len(token) >= 3 and token not in candidates:
            candidates.append(token)
    return candidates


def _resolve_symbol_from_query(query: str, raw_symbol: str) -> str:
    # Prefer explicit ticker tokens in the query first.
    candidates = _QUERY_SYMBOL_PATTERN.findall(query)
    if candidates:
        return candidates[-1].upper()

    symbol_from_input = raw_symbol.strip()
    if symbol_from_input:
        resolved = search_symbol_by_company_name(symbol_from_input)
        if resolved:
            return resolved

    lookup_candidates = _extract_lookup_candidates(query)
    for lookup_query in lookup_candidates:
        resolved = search_symbol_by_company_name(lookup_query)
        if resolved:
            return resolved

    return ""


@observe(name="agents.graph.nodes.symbol_resolver.symbol_resolver_node")
def symbol_resolver_node(state: HedgeFundState) -> dict[str, object | None]:
    input_data = state["input"]
    symbol = input_data.symbol.strip().upper()

    if _is_valid_symbol(symbol):
        return {
            "input": input_data,
            "warning": state.get("warning"),
        }

    resolved_symbol = _resolve_symbol_from_query(input_data.query, input_data.symbol)
    if not resolved_symbol:
        return {
            "input": input_data,
            "warning": state.get("warning"),
        }

    normalized_input = SignalInput(
        query=input_data.query,
        symbol=resolved_symbol,
        horizon=input_data.horizon,
    )
    return {
        "input": normalized_input,
        "warning": state.get("warning"),
    }
