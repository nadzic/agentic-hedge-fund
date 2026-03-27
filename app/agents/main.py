from __future__ import annotations

import sys
from pathlib import Path
from typing import Protocol, cast

# Allow running both:
# - python -m app.agents.main
# - python app/agents/main.py
if __package__ is None or __package__ == "":
    sys.path.append(str(Path(__file__).resolve().parents[2]))

from app.agents.graph.schemas import RiskLimits, SignalInput
from app.agents.graph.state import HedgeFundState
from app.agents.graph.workflow import build_graph
from pydantic import BaseModel
import json
from typing import Any

def _to_jsonable(value: Any) -> Any:
    """Recursively convert Pydantic/models/containers to JSON-serializable objects."""
    if isinstance(value, BaseModel):
        return value.model_dump(mode="json")
    if isinstance(value, dict):
        return {str(k): _to_jsonable(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_to_jsonable(v) for v in value]
    if isinstance(value, tuple):
        return [_to_jsonable(v) for v in value]
    return value
def _print_json(title: str, payload: Any) -> None:
    print(f"\n=== {title} ===")
    print(json.dumps(_to_jsonable(payload), indent=2, ensure_ascii=False))


class _GraphRunner(Protocol):
    def invoke(self, input: HedgeFundState, /) -> HedgeFundState: ...


def main() -> None:
    graph = cast(_GraphRunner, cast(object, build_graph()))
    state: HedgeFundState = {
        "input": SignalInput(
            query="Should I buy AAPL for a swing trade?",
            symbol="AAPL",
            horizon="swing",
        ),
        "risk_limits": RiskLimits(min_confidence=0.60, max_position_size=0.10),
        "analyst_tasks": [],
        "analyst_outputs": [],
        "suggestion": None,
        "warning": None,
        "error": None,
    }

    # 1) Step-by-step trace (delta updates after each node)
    for idx, chunk in enumerate(cast(Any, graph).stream(state, stream_mode="updates"), start=1):
         _print_json(f"STREAM UPDATE #{idx}", chunk)

    # 2) Final state snapshot
    result: HedgeFundState = graph.invoke(state)
    _print_json("FINAL STATE", result)

    suggestion = result.get("suggestion")
    print("=== AI Hedge Fund MVP ===")
    print("analyst_outputs_len:", len(result.get("analyst_outputs", [])))
    print("warning:", result.get("warning"))
    print("error:", result.get("error"))
    if suggestion is None:
        print("suggestion: None")
    else:
        _print_json("FINAL SUGGESTION", suggestion)


if __name__ == "__main__":
    main()