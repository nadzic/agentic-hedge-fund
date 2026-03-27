from __future__ import annotations

from pydantic import BaseModel, Field

from app.agents.graph.schemas import Signal
from app.agents.services.llm import get_llm

class FundamentalNarrative(BaseModel):
    summary: str = Field(..., description="2-3 sentence summary of current fundamental picture.")
    bull_case: str = Field(..., description="One bullish argument from the fundamentals.")
    bear_case: str = Field(..., description="One bearish argument from the fundamentals.")
    key_risks: list[str] = Field(
        default_factory=list,
        description="Up to 3 practical risks/uncertainties.",
    )

def _build_prompt(
    *,
    symbol: str,
    horizon: str,
    signal: Signal,
    confidence: float,
    metrics: dict[str, float | int | str],
) -> str:
    metric_lines = "\n".join(f"- {key}: {value}" for key, value in metrics.items())
    return f"""
You are a fundamentals analyst assistant.

Task:
- Explain the current fundamental setup for {symbol} on horizon={horizon}
Use ONLY the provided metrics.
Do not invent values.
Keep it concise and practical.
Symbol: {symbol}
Horizon: {horizon}
Deterministic decision:
- signal={signal.value}
- confidence={confidence:.2f}
Metrics:
{metric_lines}
Return output strictly using the required schema.
""".strip()

def generate_fundamental_narrative(
    *,
    symbol: str,
    horizon: str,
    signal: Signal,
    confidence: float,
    metrics: dict[str, float | int | str],
) -> FundamentalNarrative | None:
    prompt = _build_prompt(
        symbol=symbol,
        horizon=horizon,
        signal=signal,
        confidence=confidence,
        metrics=metrics,
    )
    try:
        llm = get_llm()
        structured_llm = llm.with_structured_output(FundamentalNarrative)
        response = structured_llm.invoke(prompt)
        if isinstance(response, FundamentalNarrative):
            return response
        return None
    except Exception:
        return None