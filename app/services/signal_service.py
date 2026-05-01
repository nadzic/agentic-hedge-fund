from collections.abc import Iterator
from typing import Any, Protocol, cast

from pydantic import BaseModel

from app.agents.graph.schemas import RiskLimits, SignalInput
from app.agents.graph.state import HedgeFundState
from app.agents.graph.workflow import build_graph
from app.api.schemas.signal import SignalRequest, SignalResponse
from app.observability.tracing import observe


class _GraphRunner(Protocol):
  def invoke(self, input: HedgeFundState, /) -> HedgeFundState: ...


def _initial_state(request: SignalRequest) -> HedgeFundState:
  return {
    "input": SignalInput(
      query=request.query,
      symbol=(request.symbol or "").strip(),
      horizon=(request.horizon or "").strip(),
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


def _run_graph_sync(request: SignalRequest) -> HedgeFundState:
  graph = cast(_GraphRunner, cast(object, build_graph()))
  return graph.invoke(_initial_state(request))


def _to_jsonable(value: Any) -> Any:
  if isinstance(value, BaseModel):
    return value.model_dump(mode="json")
  if isinstance(value, dict):
    return {str(k): _to_jsonable(v) for k, v in value.items()}
  if isinstance(value, list):
    return [_to_jsonable(v) for v in value]
  if isinstance(value, tuple):
    return [_to_jsonable(v) for v in value]
  return value


def _merge_stream_update(state: HedgeFundState, update: dict[str, Any]) -> HedgeFundState:
  for key, value in update.items():
    if (
      key in {"analyst_outputs", "analyst_tasks", "rag_citations", "missing_fields"}
      and isinstance(value, list)
      and isinstance(state.get(key), list)
    ):
      state[key] = [*state[key], *value]
      continue
    state[key] = value
  return state


@observe(name="api.signal.analyze.stream")
def run_signal_stream_sync(request: SignalRequest) -> Iterator[dict[str, Any]]:
  graph = cast(Any, build_graph())
  latest_state = _initial_state(request)

  for chunk in graph.stream(latest_state, stream_mode="updates"):
    chunk_payload = cast(dict[str, dict[str, Any]], chunk)
    for node_name, update in chunk_payload.items():
      latest_state = _merge_stream_update(latest_state, update)
      yield {
        "type": "update",
        "payload": {
          "node": node_name,
          "update": _to_jsonable(update),
        },
      }

  suggestion = latest_state.get("suggestion")
  if suggestion is None:
    raise ValueError("No suggestion found")

  final_response = SignalResponse(
    symbol=suggestion.symbol,
    signal=suggestion.signal,
    confidence=suggestion.confidence,
    reasoning=suggestion.reasoning,
    warning=latest_state.get("warning"),
    error=latest_state.get("error"),
  )
  yield {
    "type": "final",
    "payload": final_response.model_dump(mode="json"),
  }


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