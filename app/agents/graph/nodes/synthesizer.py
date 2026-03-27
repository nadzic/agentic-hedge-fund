from __future__ import annotations

from app.agents.graph.schemas import Signal, SuggestionOutput
from app.agents.graph.state import HedgeFundState
from app.observability.tracing import observe
from app.agents.graph.schemas import AnalystOutput
from collections import defaultdict

def _choose_signal(outputs: list[AnalystOutput]) -> tuple[Signal, dict[Signal, float]]:
    """Choose the signal that is most confident."""
    score_by_signal: dict[Signal, float] = defaultdict(float)
    for output in outputs:
        score_by_signal[output.signal] += output.confidence

    print(f"Score by signal: {score_by_signal}")

    # Deterministic tie-break order (important for stable behavior)
    priority = [Signal.BUY, Signal.SELL, Signal.HOLD, Signal.NO_TRADE]
    best_signal = max(priority, key=lambda signal: score_by_signal[signal])
    print(f"Best signal: {best_signal}")
    print(f"Score by signal: {score_by_signal}")
    return best_signal, score_by_signal

def _consensus_ratio(outputs: list[AnalystOutput], chosen_signal: Signal) -> float:
    if not outputs:
        return 0.0
    votes = sum(1 for out in outputs if out.signal == chosen_signal)
    return votes / len(outputs)

@observe(name="agents.graph.nodes.synthesizer.synthesizer_node")
def synthesizer_node(state: HedgeFundState) -> dict[str, SuggestionOutput]:
    """Combine analyst outputs into one suggestion (placeholder)."""
    analyst_outputs = state.get("analyst_outputs", [])
    symbol = state["input"].symbol

    if not analyst_outputs:
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

    chosen_signal, score_by_signal = _choose_signal(analyst_outputs)
    avg_conf = sum(out.confidence for out in analyst_outputs) / len(analyst_outputs)
    consensus = _consensus_ratio(analyst_outputs, chosen_signal)

    # Confidence = average confidence adjusted by consensus.
    confidence = max(0.0, min(1.0, avg_conf * (0.5 + 0.5 * consensus)))
    # Base position from confidence (will still be clamped in risk_manager).
    suggested_position = max(0.0, min(0.10, confidence * 0.10))

    # Simple policy for risk params by signal.
    if chosen_signal in (Signal.BUY, Signal.SELL):
        stop_loss_pct = 0.03
        take_profit_pct = 0.08
    else:
        stop_loss_pct = None
        take_profit_pct = None
        suggested_position = 0.0

    reasoning_parts = [
        f"{out.analyst}:{out.signal.value}({out.confidence:.2f})" for out in analyst_outputs
    ]
    reasoning = (
        " | ".join(reasoning_parts)
        + f" || chosen={chosen_signal.value}, avg_conf={avg_conf:.2f}, consensus={consensus:.2f}, "
        + f"scores={{{', '.join(f'{k.value}:{v:.2f}' for k, v in score_by_signal.items())}}}"
    )

    return {
        "suggestion": SuggestionOutput(
            symbol=symbol,
            signal=chosen_signal,
            confidence=confidence,
            reasoning=reasoning,
            suggested_position_pct=suggested_position,
            stop_loss_pct=stop_loss_pct,
            take_profit_pct=take_profit_pct,
            disclaimer="Educational output only. Not financial advice.",
        )
    }
