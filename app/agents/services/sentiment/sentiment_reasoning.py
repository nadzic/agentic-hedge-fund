from __future__ import annotations
from pydantic import BaseModel, Field
from app.agents.graph.schemas import Signal
from app.agents.services.llm import get_llm


class SentimentNarrative(BaseModel):
    summary: str = Field(..., description="2-3 sentence sentiment summary.")
    bull_case: str = Field(..., description="One bullish sentiment argument.")
    bear_case: str = Field(..., description="One bearish sentiment argument.")
    key_risks: list[str] = Field(default_factory=list, description="Up to 3 risks.")


def _build_prompt(
    *,
    symbol: str,
    horizon: str,
    signal: Signal,
    confidence: float,
    query: str,
    metrics: dict[str, float | int | str],
) -> str:
    metric_lines = "\n".join(f"- {key}: {value}" for key, value in metrics.items())
    return f"""
You are a sentiment analyst assistant.
Task:
- Explain sentiment setup for {symbol} on horizon={horizon}
- Use ONLY the provided query and metrics
- Do NOT invent external data
- Keep output concise and practical
Deterministic decision from rule engine:
- signal={signal.value}
- confidence={confidence:.2f}
User query:
{query}
Metrics:
{metric_lines}
Return output strictly matching the required schema.
""".strip()

def generate_sentiment_narrative(
    *,
    symbol: str,
    horizon: str,
    signal: Signal,
    confidence: float,
    query: str,
    metrics: dict[str, float | int | str],
) -> SentimentNarrative | None:
    prompt = _build_prompt(
        symbol=symbol,
        horizon=horizon,
        signal=signal,
        confidence=confidence,
        query=query,
        metrics=metrics,
    )
    try:
        llm = get_llm()
        structured_llm = llm.with_structured_output(SentimentNarrative)
        response = structured_llm.invoke(prompt)
        if isinstance(response, SentimentNarrative):
            return response
        return None
    except Exception:
        return None