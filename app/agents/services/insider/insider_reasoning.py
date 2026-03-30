from __future__ import annotations

from pydantic import BaseModel, Field

from app.agents.graph.schemas import Signal
from app.agents.services.llm import get_llm

class InsiderNarrative(BaseModel):
  summary: str = Field(..., description="2-3 sentence summary of insider trading activity.")
  bull_case: str = Field(..., description="One bullish argument from the insider trading activity.")
  bear_case: str = Field(..., description="One bearish argument from the insider trading activity.")