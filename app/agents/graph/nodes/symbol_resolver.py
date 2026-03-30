from __future__ import annotations

import re

from app.agents.graph.schemas import SignalInput
from app.agents.graph.state import HedgeFundState
from app.observability.tracing import observe

_SYMBOL_PATTERN = re.compile(r"^[A-Z]{1,5}$")
_QUERY_SYMBOL_PATTERN = re.compile(r"\b[A-Z]{1,5}\b")

# Deterministic company-name aliases for common demo symbols.
_COMPANY_TO_TICKER = {
    "nvidia": "NVDA",
    "nvidia corporation": "NVDA",
    "apple": "AAPL",
    "microsoft": "MSFT",
    "tesla": "TSLA",
    "amazon": "AMZN",
    "meta": "META",
    "facebook": "META",
    "google": "GOOGL",
    "alphabet": "GOOGL",
}


def _is_valid_symbol(value: str) -> bool:
    return _SYMBOL_PATTERN.match(value) is not None


def _resolve_symbol_from_query(query: str) -> str:
    # Prefer explicit ticker tokens in the query first.
    candidates = _QUERY_SYMBOL_PATTERN.findall(query)
    if candidates:
        return candidates[-1].upper()

    normalized = query.lower()
    for company_name, ticker in _COMPANY_TO_TICKER.items():
        if re.search(rf"\b{re.escape(company_name)}\b", normalized):
            return ticker
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

    resolved_symbol = _resolve_symbol_from_query(input_data.query)
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
