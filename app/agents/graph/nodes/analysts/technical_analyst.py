from __future__ import annotations

from app.agents.graph.schemas import AnalystOutput, Signal
from app.agents.graph.state import WorkerState
from app.agents.services.technicals.technicals import run_technicals_analysis
from app.agents.services.technicals.technicals_reasoning import generate_technical_narrative
from app.observability.tracing import observe


@observe(name="agents.graph.nodes.analysts.technicals_analyst_node")
def technicals_analyst_node(state: WorkerState) -> dict[str, list[AnalystOutput]]:
    symbol = state["input"].symbol
    horizon = state["input"].horizon
    query = state["input"].query

    try:
        decision, metrics = run_technicals_analysis(symbol=symbol, horizon=horizon)

        fallback_reasoning = (
            f"Technicals for {symbol} ({horizon}): signal={decision.signal.value}, "
            f"confidence={decision.confidence:.2f}, score={decision.score:.2f}, "
            f"bullish_votes={decision.votes_bullish}, bearish_votes={decision.votes_bearish}. "
            f"Rule-based rationale: {decision.reasoning}. Query context: {query}"
        )

        narrative = generate_technical_narrative(
            symbol=symbol,
            horizon=horizon,
            signal=decision.signal,
            confidence=decision.confidence,
            metrics=metrics,
        )

        if narrative is None:
            reasoning = fallback_reasoning
            metrics["status"] = "fallback"
        else:
            risks_text = ", ".join(narrative.key_risks[:3]) if narrative.key_risks else "n/a"
            reasoning = (
                f"{narrative.summary}\n\n"
                f"Bull case: {narrative.bull_case}\n"
                f"Bear case: {narrative.bear_case}\n"
                f"Key risks: {risks_text}\n\n"
                f"Deterministic decision: signal={decision.signal.value}, "
                f"confidence={decision.confidence:.2f}."
            )
            metrics["llm_reasoning_status"] = "ok"

        return {
            "analyst_outputs": [
                AnalystOutput(
                    analyst="technicals",
                    signal=decision.signal,
                    confidence=decision.confidence,
                    reasoning=reasoning,
                    metrics={"technical_score": decision.score},
                )
            ]
        }
    except Exception as error:
        return {
            "analyst_outputs": [
                AnalystOutput(
                    analyst="technicals",
                    signal=Signal.HOLD,
                    confidence=0.50,
                    reasoning=f"Error generating technical narrative: {error}",
                    metrics={
                        "technical_score": 0.0,
                        "status": "fallback",
                        "llm_reasoning_status": "not_run",
                    },
                )
            ]
        }
