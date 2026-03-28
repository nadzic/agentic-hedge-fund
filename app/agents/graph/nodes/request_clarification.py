from __future__ import annotations

from app.agents.graph.schemas import Signal, SuggestionOutput
from app.agents.graph.state import HedgeFundState
from app.observability.tracing import observe

@observe(name="agents.graph.nodes.request_clarification.request_clarification_node")
def request_clarification_node(state: HedgeFundState) -> dict[str, object | None]:
    symbol = state["input"].symbol.strip().upper() or "UNKNOWN"
    question = state.get("clarification_question") or "Please provide more details."

    suggestion = SuggestionOutput(
      symbol=symbol,
      signal=Signal.NO_TRADE,
      suggested_position_pct=0.0,
      confidence=0.0,
      stop_loss_pct=None,
      take_profit_pct=None,
      reasoning=f"Request clarification: {question}",
    )

    return {
      "suggestion": suggestion,
      "warning": question,
      "error": "input_validation_failed",
    }