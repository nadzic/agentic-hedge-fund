from typing import Protocol, cast

from app.agents.graph.schemas import RiskLimits, SignalInput
from app.agents.graph.state import HedgeFundState
from app.agents.graph.workflow import build_graph
from app.api.schemas.signal import SignalRequest, SignalResponse
from app.observability.tracing import observe


class _GraphRunner(Protocol):
  def invoke(self, input: HedgeFundState, /) -> HedgeFundState: ...


def _run_graph_sync(request: SignalRequest) -> HedgeFundState:
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
    "rag_context": None,
    "rag_citations": [],
    "is_input_valid": False,
    "missing_fields": [],
    "clarification_question": None,
  }

  return graph.invoke(state)


@observe(name="api.signal.analyze")
def run_signal_sync(request: SignalRequest) -> SignalResponse:
  result = _run_graph_sync(request)
  suggestion = result.get("suggestion")
  if suggestion is None:
    raise ValueError("No suggestion found")

  return SignalResponse(
    symbol=suggestion.symbol,
    signal=suggestion.signal,
    confidence=suggestion.confidence,
    reasoning=suggestion.reasoning,
    warning=result.get("warning"),
    error=result.get("error"),
  )