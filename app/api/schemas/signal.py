
from typing import Literal

from pydantic import BaseModel, Field


class SignalRequest(BaseModel):
  query: str = Field(..., min_length=15, description="User request")
  symbol: str = Field(..., description="Ticket symbol, e.g. APPL")
  horizon: Literal["intraday", "swing", "position"] = "swing"

class SignalResponse(BaseModel):
  symbol: str
  signal: str
  confidence: float = Field(..., ge=0, le=1)
  reasoning: str
  warning: str | None = None
  error: str | None = None