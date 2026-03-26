from __future__ import annotations

from app.agents.graph.state import HedgeFundState
from app.observability.tracing import observe

@observe(name="agents.graph.nodes.risk_manager.risk_manager_node")
def risk_manager_node(state: HedgeFundState) -> dict[str, object | None]:
    """Apply risk constraints (placeholder pass-through)."""
    suggestion = state.get("suggestion")
    return {"suggestion": suggestion, "warning": None, "error": None}
