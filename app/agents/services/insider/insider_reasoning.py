from __future__ import annotations

from pydantic import BaseModel, Field

from app.agents.services.llm import get_llm


class InsiderNarrative(BaseModel):
    summary: str = Field(..., description="2-3 sentence summary of insider trading activity.")
    bull_case: str = Field(..., description="One bullish argument from insider activity.")
    bear_case: str = Field(..., description="One bearish argument from insider activity.")
    key_risks: list[str] = Field(default_factory=list, description="Up to 3 practical risks.")


def _build_prompt(
    *,
    symbol: str,
    horizon: str,
    score: float,
    confidence: float,
    metrics: dict[str, float | int | str],
) -> str:
    metric_lines = "\n".join(f"- {key}: {value}" for key, value in metrics.items())

    return f"""
You are an insider trading analyst assistant.

Task:
- Explain insider trading activity for {symbol} on horizon={horizon}
- Use ONLY the provided metrics
- Do NOT invent external information
- Keep output concise and practical

Deterministic decision from rule engine:
- insider_score={score:.2f}
- confidence={confidence:.2f}

Metrics:
{metric_lines}

Return output strictly matching the required schema.
""".strip()


def generate_insider_narrative(
    *,
    symbol: str,
    score: float,
    horizon: str,
    confidence: float,
    metrics: dict[str, float | int | str],
) -> InsiderNarrative | None:
    prompt = _build_prompt(
        symbol=symbol,
        score=score,
        confidence=confidence,
        metrics=metrics,
        horizon=horizon,
    )
    try:
        llm = get_llm()
        structured_llm = llm.with_structured_output(InsiderNarrative)
        response = structured_llm.invoke(prompt)
        if isinstance(response, InsiderNarrative):
            return response
        return None
    except Exception:
        return None