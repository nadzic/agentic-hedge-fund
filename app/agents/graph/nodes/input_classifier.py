from __future__ import annotations

import re

from app.agents.graph.state import HedgeFundState
from app.observability.tracing import observe

ALLOWED_HORIZONS = {
  "intraday",
  "swing",
  "position",
}

def _is_valid_symbol(symbol: str) -> bool:
  # 1-5 chars, uppercase latter only (simple first-pass guard)
  return re.match(r"^[A-Z]{1,5}$", symbol) is not None

@observe(name="agents.graph.nodes.input_classifier.input_classifier_node")
def input_classifier_node(state: HedgeFundState) -> dict[str, object | None]:
  input_data = state["input"]

  symbol = input_data.symbol.strip().upper()
  horizon = input_data.horizon.strip().lower()
  query = input_data.query.strip()

  missing_fields: list[str] = []

  if not _is_valid_symbol(symbol):
    missing_fields.append("valid symbol (e.g. AAPL, MSFT, GOOGL, META, NVDA, TSLA, AMZN, etc.)")
  if len(query) < 15:
    missing_fields.append("input inquiry shoudl be at least 15 characters")
  if horizon not in ALLOWED_HORIZONS:
    missing_fields.append("valid horizon (intraday | swing | position)")

  if missing_fields:
    clarification_question = (
      "Need additional clarification on the input. "
      "Please provide the following information: "
      f"{', '.join(missing_fields)}. "
      "Example: Please analyze NVDA for swing trading."
    )
    return {
      "is_input_valid": False,
      "missing_fields": missing_fields,
      "clarification_question": clarification_question,
      "warning": "Input classifier: missing fields",
      "error" : "input_validation_failed"
    }

  input_data.symbol = symbol
  input_data.horizon = horizon

  return {
    "input": input_data,
    "is_input_valid": True,
    "missing_fields": [],
    "clarification_question": None,
    "warning": None,
    "error": None,
  }

def route_after_classification(state: HedgeFundState) -> str:
  if state["is_input_valid"]:
    return "market_research_agent"
  else:
    return "request_clarification"

  