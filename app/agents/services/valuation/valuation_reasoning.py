from __future__ import annotations
from pydantic import BaseModel, Field
from app.agents.graph.schemas import Signal
from app.agents.services.llm import get_llm
class ValuationNarrative(BaseModel):
    summary: str = Field(..., description="2-3 sentence valuation summary.")
    bull_case: str = Field(..., description="One valuation-based bullish argument.")
    bear_case: str = Field(..., description="One valuation-based bearish argument.")
    key_risks: list[str] = Field(default_factory=list, description="Up to 3 risks.")
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
You are a valuation analyst assistant.
Task:
- Explain valuation setup for {symbol} on horizon={horizon}
- Use ONLY provided metrics
- Do NOT invent data
- Keep output concise and practical
Deterministic decision from rule engine:
- signal={signal.value}
- confidence={confidence:.2f}
Metrics:
{metric_lines}
Return output strictly matching the required schema.
""".strip()
def generate_valuation_narrative(
    *,
    symbol: str,
    horizon: str,
    signal: Signal,
    confidence: float,
    metrics: dict[str, float | int | str],
) -> ValuationNarrative | None:
    prompt = _build_prompt(
        symbol=symbol,
        horizon=horizon,
        signal=signal,
        confidence=confidence,
        metrics=metrics,
    )
    try:
        llm = get_llm()
        structured_llm = llm.with_structured_output(ValuationNarrative)
        response = structured_llm.invoke(prompt)
        if isinstance(response, ValuationNarrative):
            return response
        return None
    except Exception:
        return None