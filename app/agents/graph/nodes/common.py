from __future__ import annotations

from app.agents.graph.schemas import AnalystName, AnalystOutput, Signal


def placeholder_output(analyst: AnalystName, reasoning: str) -> dict[str, list[AnalystOutput]]:
    """Return a consistent placeholder analyst response."""
    out = AnalystOutput(
        analyst=analyst,
        signal=Signal.HOLD,
        confidence=0.5,
        reasoning=reasoning,
        metrics={"status": "placeholder"},
    )
    return {"analyst_outputs": [out]}
