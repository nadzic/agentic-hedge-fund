from typing import Any
from app.api.schemas.signal import SignalRequest
from app.agents.graph.workflow import build_graph
from app.agents.graph.state import HedgeFundState
from app.agents.graph.schemas import SignalInput
from app.agents.graph.schemas import RiskLimits

def run_graph_sync(request: SignalRequest) -> dict[str, Any] | Any:
  graph = build_graph() 

  state: HedgeFundState = {
    "input": SignalInput(
      query=request.query,
      symbol=request.symbol,
      horizon=request.horizon,
    ),
    "risk_limits": RiskLimits(
      min_confidence=0.60,
      max_position_size=0.10,
    ),
    "analyst_tasks": [],
    "analyst_outputs": [],
    "suggestion": None,
    "warning": None,
    "error": None,
  }

  result = graph.invoke(state)
  return result