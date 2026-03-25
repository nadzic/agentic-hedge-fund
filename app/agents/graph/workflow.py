from langgraph.graph import END, START, StateGraph

from app.agents.graph.nodes import (
    assign_workers,
    fundamentals_analyst_node,
    orchestrator_node,
    risk_manager_node,
    sentiment_analyst_node,
    synthesizer_node,
    technicals_analyst_node,
    valuation_analyst_node,
)
from app.agents.graph.state import HedgeFundState


def build_graph():
    graph = StateGraph(HedgeFundState)

    graph.add_node("orchestrator", orchestrator_node)
    graph.add_node("fundamentals_analyst_node", fundamentals_analyst_node)
    graph.add_node("technicals_analyst_node", technicals_analyst_node)
    graph.add_node("valuation_analyst_node", valuation_analyst_node)
    graph.add_node("sentiment_analyst_node", sentiment_analyst_node)
    graph.add_node("synthesizer", synthesizer_node)
    graph.add_node("risk_manager", risk_manager_node)

    graph.add_edge(START, "orchestrator")
    graph.add_conditional_edges(
        "orchestrator",
        assign_workers,
        [
            "fundamentals_analyst_node",
            "technicals_analyst_node",
            "valuation_analyst_node",
            "sentiment_analyst_node",
        ],
    )
    graph.add_edge("fundamentals_analyst_node", "synthesizer")
    graph.add_edge("technicals_analyst_node", "synthesizer")
    graph.add_edge("valuation_analyst_node", "synthesizer")
    graph.add_edge("sentiment_analyst_node", "synthesizer")
    graph.add_edge("synthesizer", "risk_manager")
    graph.add_edge("risk_manager", END)

    return graph.compile()




