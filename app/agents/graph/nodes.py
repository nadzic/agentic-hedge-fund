from app.agents.graph.schemas import SuggestionOutput, AnalystOutput, AnalystTask, Signal
from app.agents.graph.state import HedgeFundState, WorkerState
from app.agents.graph.log_state import log_state
from langgraph.types import Send



def orchestrator_node(state: HedgeFundState) -> dict:
  log_state("orchestrator:in", state)
  # add our tasks
  """
  Prepare analyst tasks and optionally validate input.
  TODO:
  - Validate symbol/horizon
  - Dynamic analyst selection by horizon/query
  """
  tasks = [
    AnalystTask(analyst="fundamentals"),
    AnalystTask(analyst="technicals"),
    AnalystTask(analyst="valuation"),
    AnalystTask(analyst="sentiment"),
  ]
  return {"analyst_tasks": tasks, "warning": None, "error": None}


def assign_workers(state: HedgeFundState):
    """
    Fan-out analyst tasks.
    NOTE: pass input so worker can build analyst-specific query.
    """
    return [
        Send("analyst_worker_node", {"analyst_task": analyst_task})
        for analyst_task in state["analyst_tasks"]
    ]

def analyst_worker_node(state: WorkerState) -> dict:
  """
  Worker pipeline placeholder.
  TODO real pipeline:
    1) build analyst query
    2) run research tool (retrieval + optional rerank)
    3) run generation tool
    4) map to AnalystOutput
  """
  analyst_name = state["analyst_task"].analyst

  if analyst_name == "fundamentals":
    out = AnalystOutput(
      analyst=analyst_name,
      signal=Signal.BUY,
      confidence=0.95,
      reasoning="The fundamentals of the company are strong.",
      metrics={},
    )
  elif analyst_name == "technicals":
    out = AnalystOutput(
      analyst=analyst_name,
      signal=Signal.BUY,
      confidence=0.95,
      reasoning="The technicals of the company are strong.",
      metrics={},
    )
  elif analyst_name == "valuation":
    out = AnalystOutput(
      analyst=analyst_name,
      signal=Signal.BUY,
      confidence=0.95,
      reasoning="The valuation of the company is strong.",
      metrics={},
    )
  # Sentiment
  else:
    out = AnalystOutput(
      analyst=analyst_name,
      signal=Signal.HOLD,
      confidence=0.50,
      reasoning="The fundamentals of the company are neutral.",
      metrics={},
    )

  return {"analyst_outputs": [out]}

def fundamentals_analyst_node(state: WorkerState) -> None:
  raise NotImplementedError("Fundamentals analyst node not implemented")

def technicals_analyst_node(state: WorkerState) -> None:
  raise NotImplementedError("Technicals analyst node not implemented")

def valuation_analyst_node(state: WorkerState) -> None:
  raise NotImplementedError("Valuation analyst node not implemented")

def sentiment_analyst_node(state: WorkerState) -> None:
  raise NotImplementedError("Sentiment analyst node not implemented")

ANALYST_NODES = {
  "fundamentals": fundamentals_analyst_node,
  "technicals": technicals_analyst_node,
  "valuation": valuation_analyst_node,
  "sentiment": sentiment_analyst_node,
}

def synthesizer_node(state: HedgeFundState) -> dict:
  """
  Combine analyst outputs into final suggestion.
  TODO:
  - Weighted voting by confidence
  - Better confidence aggregation
  - Reasoning summarization
  """
  outputs = state.get("analyst_outputs", [])
  symbol = state["input"].symbol


  if not outputs:
      return {
          "suggestion": SuggestionOutput(
              symbol=symbol,
              signal=Signal.NO_TRADE,
              confidence=0.0,
              reasoning="No analyst outputs available.",
              suggested_position_pct=0.0,
              stop_loss_pct=None,
              take_profit_pct=None,
          )
      }

  # Placeholder: simple majority-ish default
  reasoning = " | ".join(
      f"{o.analyst}:{o.signal.value}({o.confidence:.2f})" for o in outputs
  )

  return {
    "suggestion": SuggestionOutput(
      symbol=symbol,
      signal=Signal.BUY, # TODO: Implement weighted voting by confidence
      confidence=0.95, # TODO: Implement better confidence aggregation
      reasoning=reasoning,
      suggested_position_pct=0.10,
      stop_loss_pct=0.05,
      take_profit_pct=0.20,
      disclaimer="Educational output only. Not financial advice.",
    )
  }

def risk_manager_node(state: HedgeFundState) -> dict:
  suggestion = state.get("suggestion")

  return {"suggestion": suggestion, "warning": None, "error": None}

  