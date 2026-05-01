from pydantic import BaseModel
from typing import Optional

class Source(BaseModel):
    title: str
    url: str
    snippet: Optional[str] = None
    source_type: Optional[str] = None
    reliability_score: Optional[float] = None
    relevance_score: Optional[float] = None
    recency_score: Optional[float] = None
    final_source_score: Optional[float] = None
    reason: Optional[str] = None