from typing import Protocol, cast

from app.agents.graph.schemas import RiskLimits, SignalInput
from app.agents.graph.state import HedgeFundState
from app.agents.graph.workflow import build_graph
from app.api.schemas.signal import SignalRequest


class _GraphRunner(Protocol):
  def invoke(self, input: HedgeFundState, /) -> HedgeFundState: ...


def run_graph_sync(request: SignalRequest) -> HedgeFundState:
  graph = cast(_GraphRunner, cast(object, build_graph()))

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

  return graph.invoke(state)