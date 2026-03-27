from __future__ import annotations

from app.agents.graph.schemas import AnalystOutput, Signal
from app.agents.graph.state import WorkerState
from app.observability.tracing import observe

from .fundamental_analyst import fundamentals_analyst_node
from .technical_analyst import technicals_analyst_node


def _mock_is_bullish_or_bearish(query: str) -> tuple[bool, bool]:
    lower_query = query.lower()
    has_bullish_keywords = any(
        keyword in lower_query
        for keyword in ["bullish", "buy", "up", "positive", "growth", "opportunity", "potential"]
    )
    has_bearish_keywords = any(
        keyword in lower_query
        for keyword in ["bearish", "sell", "down", "negative", "decline", "risk", "concern"]
    )
    return has_bullish_keywords, has_bearish_keywords


@observe(name="agents.graph.nodes.analysts.valuation_analyst_node")
def valuation_analyst_node(state: WorkerState) -> dict[str, list[AnalystOutput]]:
    symbol = state["input"].symbol
    query = state["input"].query

    has_bullish_keywords, has_bearish_keywords = _mock_is_bullish_or_bearish(query)

    if has_bullish_keywords:
        signal = Signal.BUY
        confidence = 0.70
    elif has_bearish_keywords:
        signal = Signal.SELL
        confidence = 0.30
    else:
        signal = Signal.HOLD
        confidence = 0.50

    reasoning = (
        f"Based on the query: {query}, the analyst is {signal.value} "
        f"with a confidence of {confidence:.2f}. The symbol is {symbol}."
    )

    return {
        "analyst_outputs": [
            AnalystOutput(
                analyst="valuation",
                signal=signal,
                confidence=confidence,
                reasoning=reasoning,
                metrics={"valuation_score": confidence},
            )
        ]
    }


@observe(name="agents.graph.nodes.analysts.sentiment_analyst_node")
def sentiment_analyst_node(state: WorkerState) -> dict[str, list[AnalystOutput]]:
    symbol = state["input"].symbol
    query = state["input"].query

    has_bullish_keywords, has_bearish_keywords = _mock_is_bullish_or_bearish(query)

    if has_bullish_keywords:
        signal = Signal.BUY
        confidence = 0.85
    elif has_bearish_keywords:
        signal = Signal.SELL
        confidence = 0.15
    else:
        signal = Signal.HOLD
        confidence = 0.50

    reasoning = (
        f"Based on the query: {query}, the analyst is {signal.value} "
        f"with a confidence of {confidence:.2f}. The symbol is {symbol}."
    )

    return {
        "analyst_outputs": [
            AnalystOutput(
                analyst="sentiment",
                signal=signal,
                confidence=confidence,
                reasoning=reasoning,
                metrics={"sentiment_score": confidence},
            )
        ]
    }


__all__ = [
    "fundamentals_analyst_node",
    "sentiment_analyst_node",
    "technicals_analyst_node",
    "valuation_analyst_node",
]
