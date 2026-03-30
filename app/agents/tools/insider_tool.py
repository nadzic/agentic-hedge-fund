from __future__ import annotations

from typing import Literal

from langchain_core.tools import tool

from pydantic import BaseModel, Field
from langchain_core.tools import tool
from app.agents.services.insider.insider import run_insider_analysis

from app.observability.tracing import observe

class InsiderToolResult(BaseModel):
  status: Literal["ok", "error"]
  symbol: str
  loopback_days: int
  score: float | None = None
  confidence: float | None = None
  reasoning: str | None = None
  metrics: dict[str, float | int | str] = Field(default_factory=dict)
  error: str | None = None

@tool
@observe(name="agents.tools.insider_tool")
def insider_tool(symbol: str, lookback_days: int = 30) -> str:
    """
    Fetch insider analysis and return compact JSON for agent usage.
    """
    ticker = symbol.upper().strip()
    try:
        decision, metrics = run_insider_analysis(symbol=ticker, lookback_days=lookback_days)
        return InsiderToolResult(
            status="ok",
            symbol=ticker,
            loopback_days=lookback_days,
            score=decision.score,
            confidence=decision.confidence,
            reasoning=decision.reasoning,
            metrics=metrics,
        ).model_dump_json()
    except Exception as exc:
        return InsiderToolResult(
            status="error",
            symbol=ticker,
            loopback_days=lookback_days,
            error=str(exc),
        ).model_dump_json()
