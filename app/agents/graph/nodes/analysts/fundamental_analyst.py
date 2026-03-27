from app.agents.services.fundamentals.fundamentals import run_fundamentals_analysis
from app.agents.services.fundamentals.fundamentals_reasoning import generate_fundamental_narrative
from app.agents.graph.schemas import AnalystOutput, Signal
from app.agents.graph.state import WorkerState
from app.observability.tracing import observe

@observe(name="agents.graph.nodes.analysts.fundamentals_analyst_node")
def fundamentals_analyst_node(state: WorkerState) -> dict[str, list[AnalystOutput]]:
    symbol = state["input"].symbol
    horizon = state["input"].horizon
    query = state["input"].query
    try:
        decision, metrics = run_fundamentals_analysis(symbol=symbol, horizon=horizon)
        fallback_reasoning = (
            f"Fundamentals for {symbol} ({horizon}): signal={decision.signal.value}, "
            f"confidence={decision.confidence:.2f}, score={decision.score:.2f}. "
            f"{decision.reasoning}. Query context: {query}"
        )
        narrative = generate_fundamental_narrative(
            symbol=symbol,
            horizon=horizon,
            signal=decision.signal,
            confidence=decision.confidence,
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
                f"Deterministic decision: signal={decision.signal.value}, confidence={decision.confidence:.2f}."
            )
            metrics["llm_reasoning_status"] = "ok"
        return {
            "analyst_outputs": [
                AnalystOutput(
                    analyst="fundamentals",
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
                    analyst="fundamentals",
                    signal=Signal.HOLD,
                    confidence=0.50,
                    reasoning=f"Fundamentals fallback due to error: {exc}",
                    metrics={
                        "fundamental_score": 0.0,
                        "status": "fallback",
                        "llm_reasoning_status": "not_run",
                    },
                )
            ]
        }