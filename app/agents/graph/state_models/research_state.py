from typing import TypedDict, List, Dict, Any, Optional

class ResearchState(TypedDict):
    user_query: str

    company_name: Optional[str]
    ticker: Optional[str]
    exchange: Optional[str]

    search_plan: List[Dict[str, Any]]
    raw_sources: List[Dict[str, Any]]
    ranked_sources: List[Dict[str, Any]]

    evidence_items: List[Dict[str, Any]]
    classified_evidence: List[Dict[str, Any]]
    selected_evidence: List[Dict[str, Any]]
    discarded_evidence: List[Dict[str, Any]]

    final_brief: Dict[str, Any]
    errors: List[str]