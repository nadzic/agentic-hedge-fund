from __future__ import annotations

from app.agents.graph.state import HedgeFundState


def risk_manager_node(state: HedgeFundState) -> dict[str, object | None]:
    """Apply risk constraints (placeholder pass-through)."""
    suggestion = state.get("suggestion")
    return {"suggestion": suggestion, "warning": None, "error": None}
