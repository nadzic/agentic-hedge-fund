from __future__ import annotations

from app.agents.graph.schemas import AnalystOutput, Signal
from app.agents.graph.state import WorkerState
from app.agents.services.sentiment.sentiment import run_sentiment_analysis
from app.agents.services.sentiment.sentiment_reasoning import generate_sentiment_narrative
from app.observability.tracing import observe


@observe(name="agents.graph.nodes.analysts.sentiment_analyst_node")
def sentiment_analyst_node(state: WorkerState) -> dict[str, list[AnalystOutput]]:
    symbol = state["input"].symbol
    horizon = state["input"].horizon
    query = state["input"].query
    try:
        decision, metrics = run_sentiment_analysis(
            symbol=symbol,
            horizon=horizon,
            query=query,
        )
        fallback_reasoning = (
            f"Sentiment for {symbol} ({horizon}): signal={decision.signal.value}, "
            f"confidence={decision.confidence:.2f}, score={decision.score:.2f}. "
            f"Rule-based rationale: {decision.reasoning}. Query context: {query}"
        )
        narrative = generate_sentiment_narrative(
            symbol=symbol,
            horizon=horizon,
            signal=decision.signal,
            confidence=decision.confidence,
            query=query,
            metrics=metrics,
        )
        if narrative is None:
            reasoning = fallback_reasoning
            metrics["llm_reasoning_status"] = "fallback"
        else:
            risks_text = ", ".join(narrative.key_risks[:3]) if narrative.key_risks else "n/a"
            reasoning = (
                f"{narrative.summary}\n\n"
                f"Bull case: {narrative.bull_case}\n"
                f"Bear case: {narrative.bear_case}\n"
                f"Key risks: {risks_text}\n\n"
                "Deterministic decision: "
                f"signal={decision.signal.value}, confidence={decision.confidence:.2f}."
            )
            metrics["llm_reasoning_status"] = "ok"
        return {
            "analyst_outputs": [
                AnalystOutput(
                    analyst="sentiment",
                    signal=decision.signal,
                    confidence=decision.confidence,
                    reasoning=reasoning,
                    metrics=metrics,
                )
            ]
        }
    except Exception as exc:
        return {
            "analyst_outputs": [
                AnalystOutput(
                    analyst="sentiment",
                    signal=Signal.HOLD,
                    confidence=0.50,
                    reasoning=f"Sentiment fallback due to error: {exc}",
                    metrics={
                        "sentiment_score": 0.0,
                        "status": "fallback",
                        "llm_reasoning_status": "not_run",
                    },
                )
            ]
        }