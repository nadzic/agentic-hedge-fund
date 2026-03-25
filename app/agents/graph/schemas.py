from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field

AnalystName = Literal["fundamentals", "technicals", "valuation", "sentiment"]

class AnalystTask(BaseModel):
  analyst: AnalystName

class Signal(str, Enum): # type: Literal["buy", "sell", "hold", "no_trade"]
  BUY = "buy"
  SELL = "sell"
  HOLD = "hold"
  NO_TRADE = "no_trade"

class SignalInput(BaseModel):
  query: str = Field(..., description="User request")
  symbol: str = Field(..., description="Ticker, e.g. APPL")
  horizon: str = Field("swing", description="swing | intraday | position")

class RiskLimits(BaseModel):
  min_confidence: float = Field(0.60, gt=0, le=1)
  max_position_size: float = Field(0.10, gt=0, le=1)

class SuggestionOutput(BaseModel):
  symbol: str
  signal: Signal
  confidence: float = Field(..., ge=0, le=1)
  reasoning: str
  suggested_position_pct: float = Field(..., ge=0, le=1)
  stop_loss_pct: float | None = Field(None, ge=0, le=1)
  take_profit_pct: float | None = Field(None, ge=0, le=2)
  disclaimer: str = "Educational output only. Not financial advice."

class AnalystOutput(BaseModel):
  analyst: AnalystName
  signal: Signal
  confidence: float = Field(..., ge=0, le=1)
  reasoning: str
  metrics: dict[str, float | int | str]