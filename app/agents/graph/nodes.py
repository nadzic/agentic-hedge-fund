from app.agents.graph.schemas import SuggestionOutput, AnalystOutput, AnalystTask, Signal
from app.agents.graph.state import HedgeFundState, WorkerState
from langgraph.types import Send


def orchestrator_node(state: HedgeFundState) -> dict:
  # add our tasks
  tasks = [
    AnalystTask(analyst="fundamentals"),
    AnalystTask(analyst="technicals"),
    AnalystTask(analyst="valuation"),
    AnalystTask(analyst="sentiment"),
  ]
  return {"analyst_tasks": tasks, "warning": None, "error": None}


def assign_workers(state: HedgeFundState):
    return [
        Send("analyst_worker_node", {"analyst_task": analyst_task})
        for analyst_task in state["analyst_tasks"]
    ]

def analyst_worker_node(state: WorkerState) -> dict:
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

def synthesizer_node(state: HedgeFundState) -> dict:
  # TODO: Implement synthesis logic
  return {"suggestion": SuggestionOutput(
    symbol=state["input"].symbol,
    signal=Signal.BUY,
    confidence=0.95,
    reasoning="The fundamentals of the company are strong.",
    suggested_position_pct=0.10,
    stop_loss_pct=0.05,
    take_profit_pct=0.20,
    disclaimer="Educational output only. Not financial advice.",
  )}

def risk_manager_node(state: HedgeFundState) -> dict:
  suggestion = state.get("suggestion")

  return {"suggestion": suggestion, "warning": None, "error": None}

  