from __future__ import annotations

from app.agents.graph.log_state import log_state
from app.agents.graph.nodes.common import placeholder_output
from app.agents.graph.schemas import AnalystOutput
from app.agents.graph.state import WorkerState
from app.observability.tracing import observe


@observe(name="agents.graph.nodes.analysts.fundamentals_analyst_node")
def fundamentals_analyst_node(state: WorkerState) -> dict[str, list[AnalystOutput]]:
    log_state("fundamentals:in", state, keys=["analyst_task"])
    return placeholder_output(
        analyst="fundamentals",
        reasoning="Placeholder: fundamentals analyst logic not implemented yet.",
    )


@observe(name="agents.graph.nodes.analysts.technicals_analyst_node")
def technicals_analyst_node(state: WorkerState) -> dict[str, list[AnalystOutput]]:
    log_state("technicals:in", state, keys=["analyst_task"])
    return placeholder_output(
        analyst="technicals",
        reasoning="Placeholder: technicals analyst logic not implemented yet.",
    )


@observe(name="agents.graph.nodes.analysts.valuation_analyst_node")
def valuation_analyst_node(state: WorkerState) -> dict[str, list[AnalystOutput]]:
    log_state("valuation:in", state, keys=["analyst_task"])
    return placeholder_output(
        analyst="valuation",
        reasoning="Placeholder: valuation analyst logic not implemented yet.",
    )


@observe(name="agents.graph.nodes.analysts.sentiment_analyst_node")
def sentiment_analyst_node(state: WorkerState) -> dict[str, list[AnalystOutput]]:
    log_state("sentiment:in", state, keys=["analyst_task"])
    return placeholder_output(
        analyst="sentiment",
        reasoning="Placeholder: sentiment analyst logic not implemented yet.",
    )
