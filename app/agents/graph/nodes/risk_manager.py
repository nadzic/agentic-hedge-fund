from __future__ import annotations

from app.agents.graph.schemas import Signal
from app.agents.graph.state import HedgeFundState
from app.observability.tracing import observe


@observe(name="agents.graph.nodes.risk_manager.risk_manager_node")
def risk_manager_node(state: HedgeFundState) -> dict[str, object | None]:
    """Apply risk constraints (placeholder pass-through)."""
    suggestion = state.get("suggestion")
    limits = state.get("risk_limits")

    if suggestion is None:
        return {"suggestion": None, "warning": "No suggestion to risk-manage.", "error": None}
    
    if limits is None:
        return {"suggestion": suggestion, "warning": "No risk limits provided.", "error": None}

    warnings: list[str] = []

    # Clamo position size to limits.
    if suggestion.suggested_position_pct > limits.max_position_size:
        suggestion.suggested_position_pct = limits.max_position_size
        warnings.append(
            f"Position size clamped to max_position_size={limits.max_position_size:.2f}."
        )

    # confidence guard
    if suggestion.confidence < limits.min_confidence:
        warnings.append(
            f"Confidence clamped to min_confidence={limits.min_confidence:.2f}."
        )
        suggestion.signal = Signal.NO_TRADE
        suggestion.suggested_position_pct = 0.0
        suggestion.confidence = 0.0
        suggestion.stop_loss_pct = None
        suggestion.take_profit_pct = None
        suggestion.reasoning = (
            f"Confidence below min_confidence={limits.min_confidence:.2f}. "
            "No trade suggested."
        )

    warning_text = " | ".join(warnings) if warnings else None

    return {"suggestion": suggestion, "warning": warning_text, "error": None}
