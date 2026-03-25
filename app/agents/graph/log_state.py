import logging
from collections.abc import Mapping

from app.agents.graph.state import HedgeFundState, WorkerState

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def log_state(
  node: str,
  state: HedgeFundState | WorkerState | Mapping[str, object],
  keys: list[str] | None = None,
) -> None:
  if keys is None:
    keys = ["input", "analyst_tasks", "analyst_outputs", "suggestion", "warning", "error"]
  new_dict_state = {k: v for k, v in state.items() if k in keys}
  logger.info(f"[{node}] state: {new_dict_state}")