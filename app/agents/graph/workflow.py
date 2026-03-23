from langgraph.graph import StateGraph, START, END

from app.agents.graph.nodes import orchestrator_node, assign_workers, analyst_worker_node, synthesizer_node, risk_manager_node
from app.agents.graph.state import HedgeFundState

def build_graph():
    graph = StateGraph(HedgeFundState)

    graph.add_node("orchestrator", orchestrator_node)
    graph.add_node("analyst_worker_node", analyst_worker_node)
    graph.add_node("synthesizer", synthesizer_node)
    graph.add_node("risk_manager", risk_manager_node)

    graph.add_edge(START, "orchestrator")
    graph.add_conditional_edges("orchestrator", assign_workers, ["analyst_worker_node"])
    graph.add_edge("analyst_worker_node", "synthesizer")
    graph.add_edge("synthesizer", "risk_manager")
    graph.add_edge("risk_manager", END)

    return graph.compile()




