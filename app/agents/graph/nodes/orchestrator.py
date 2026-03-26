from __future__ import annotations

from collections.abc import Mapping

from langgraph.types import Send

from app.agents.graph.log_state import log_state
from app.agents.graph.schemas import AnalystTask
from app.agents.graph.state import HedgeFundState
from app.observability.tracing import observe


@observe(name="agents.graph.nodes.orchestrator.orchestrator_node")
def orchestrator_node(state: HedgeFundState) -> Mapping[str, object | None]:
    """Create analyst tasks for fan-out execution."""
    log_state("orchestrator:in", state)
    tasks = [
        AnalystTask(analyst="fundamentals"),
        AnalystTask(analyst="technicals"),
        AnalystTask(analyst="valuation"),
        AnalystTask(analyst="sentiment"),
    ]
    out = {"analyst_tasks": tasks, "warning": None, "error": None}
    log_state("orchestrator:out", out)
    return out


@observe(name="agents.graph.nodes.orchestrator.assign_workers")
def assign_workers(state: HedgeFundState):
    """Route each task to its analyst-specific node."""
    task_to_node = {
        "fundamentals": "fundamentals_analyst_node",
        "technicals": "technicals_analyst_node",
        "valuation": "valuation_analyst_node",
        "sentiment": "sentiment_analyst_node",
    }
    return [
        Send(task_to_node[task.analyst], {"analyst_task": task})
        for task in state["analyst_tasks"]
    ]
