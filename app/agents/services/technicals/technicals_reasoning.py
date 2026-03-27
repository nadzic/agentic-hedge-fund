from __future__ import annotations

from pydantic import BaseModel, Field

from app.agents.graph.schemas import Signal
from app.agents.services.llm import get_llm


class TechnicalNarrative(BaseModel):
    summary: str = Field(..., description="2-3 sentence summary of current technical picture.")
    bull_case: str = Field(..., description="One bullish argument from the indicators.")
    bear_case: str = Field(..., description="One bearish argument from the indicators.")
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
    return f"""
You are a technical analyst assistant.

Task:
- Explain the current technical setup for {symbol} on horizon={horizon}
- Use ONLY provided metrics
- Do NOT invent data
- Keep explanations concise and practical
Deterministic decision from rule engine:
- signal={signal.value}
- confidence={confidence:.2f}
Metrics:
- close={metrics.get("close")}
- rsi14={metrics.get("rsi14")}
- macd={metrics.get("macd")}
- macd_signal={metrics.get("macd_signal")}
- macd_hist={metrics.get("macd_hist")}
- ema200={metrics.get("ema200")}
- bb_upper={metrics.get("bb_upper")}
- bb_mid={metrics.get("bb_mid")}
- bb_lower={metrics.get("bb_lower")}
- technical_score={metrics.get("technical_score")}
- votes_bullish={metrics.get("votes_bullish")}
- votes_bearish={metrics.get("votes_bearish")}
Output must match the structured schema exactly.
""".strip()

def generate_technical_narrative(
  *, 
  symbol: str,
  horizon: str,
  signal: Signal,
  confidence: float,
  metrics: dict[str, float | int | str],
) -> TechnicalNarrative | None:
    """
    Returns structured LLM narrative.
    If model/provider does not support structured output or call fails, returns None.
    """
    prompt = _build_prompt(
        symbol=symbol,
        horizon=horizon,
        signal=signal,
        confidence=confidence,
        metrics=metrics,
    )
    try:
        llm = get_llm()
        structured_llm = llm.with_structured_output(TechnicalNarrative)
        response = structured_llm.invoke(prompt)
        if isinstance(response, TechnicalNarrative):
            return response
        return None
    except Exception:
        return None