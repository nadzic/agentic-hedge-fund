from __future__ import annotations

from app.agents.graph.schemas import Signal, SuggestionOutput
from app.agents.graph.state import HedgeFundState
from app.observability.tracing import observe

@observe(name="agents.graph.nodes.synthesizer.synthesizer_node")
def synthesizer_node(state: HedgeFundState) -> dict[str, SuggestionOutput]:
    """Combine analyst outputs into one suggestion (placeholder)."""
    outputs = state.get("analyst_outputs", [])
    symbol = state["input"].symbol

    if not outputs:
        return {
            "suggestion": SuggestionOutput(
                symbol=symbol,
                signal=Signal.NO_TRADE,
                confidence=0.0,
                reasoning="No analyst outputs available.",
                suggested_position_pct=0.0,
                stop_loss_pct=None,
                take_profit_pct=None,
            )
        }

    reasoning = " | ".join(f"{o.analyst}:{o.signal.value}({o.confidence:.2f})" for o in outputs)
    return {
        "suggestion": SuggestionOutput(
            symbol=symbol,
            signal=Signal.BUY,
            confidence=0.95,
            reasoning=reasoning,
            suggested_position_pct=0.10,
            stop_loss_pct=0.05,
            take_profit_pct=0.20,
            disclaimer="Educational output only. Not financial advice.",
        )
    }
