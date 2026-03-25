
from pydantic import BaseModel, Field


class SignalRequest(BaseModel):
  query: str = Field(..., description="User request")
  symbol: str = Field(..., description="Ticket symbol, e.g. APPL")
  horizon: str = Field("swing", description="swing | intraday | position")

class SignalResponse(BaseModel):
  symbol: str
  signal: str
  confidence: float = Field(..., ge=0, le=1)
  reasoning: str
  warning: str | None = None
  error: str | None = None