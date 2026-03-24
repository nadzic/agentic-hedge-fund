from __future__ import annotations

from app.agents.graph.schemas import AnalystOutput, Signal


def placeholder_output(analyst: str, reasoning: str) -> dict:
    """Return a consistent placeholder analyst response."""
    out = AnalystOutput(
        analyst=analyst,  # type: ignore[arg-type]
        signal=Signal.HOLD,
        confidence=0.5,
        reasoning=reasoning,
        metrics={"status": "placeholder"},
    )
    return {"analyst_outputs": [out]}
