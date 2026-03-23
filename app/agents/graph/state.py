from typing import Annotated, Optional, TypedDict
import operator
from app.agents.graph.schemas import SignalInput, AnalystTask, RiskLimits, SuggestionOutput, AnalystOutput
 
class HedgeFundState(TypedDict):
  # user/request input
  input: SignalInput

  # optional risk limits
  risk_limits: Optional[RiskLimits]

  # Node outputs
  suggestion: Optional[SuggestionOutput]

  # analyst tasks
  analyst_tasks: list[AnalystTask]

  # diagnostics
  warning: Optional[str]
  error: Optional[str]

  # analyst outputs
  analyst_outputs: Annotated[list[AnalystOutput], operator.add]

class WorkerState(TypedDict):
  analyst_task: AnalystTask
  analyst_outputs: Annotated[list[AnalystOutput], operator.add]