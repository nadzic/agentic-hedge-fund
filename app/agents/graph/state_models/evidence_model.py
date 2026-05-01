from pydantic import BaseModel
from typing import Optional, List

class EvidenceItem(BaseModel):
    claim: str
    category: str
    source_url: str
    source_type: str
    period: Optional[str] = None
    metric: Optional[str] = None
    value: Optional[str] = None
    comparison_type: Optional[str] = None

    evidence_strength: Optional[str] = None
    fact_or_interpretation: Optional[str] = None
    confidence: Optional[float] = None
    reason: Optional[str] = None

    inclusion_score: Optional[float] = None
    used_for: Optional[List[str]] = None