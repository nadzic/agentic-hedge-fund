from __future__ import annotations

import sys
from pathlib import Path

# Allow running both:
# - python -m app.agents.main
# - python app/agents/main.py
if __package__ is None or __package__ == "":
    sys.path.append(str(Path(__file__).resolve().parents[2]))

from app.agents.graph.schemas import RiskLimits, SignalInput
from app.agents.graph.state import HedgeFundState
from app.agents.graph.workflow import build_graph


def main() -> None:
    graph = build_graph()
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

    result = graph.invoke(state)

    suggestion = result.get("suggestion")
    print("=== AI Hedge Fund MVP ===")
    print("analyst_outputs_len:", len(result.get("analyst_outputs", [])))
    print("warning:", result.get("warning"))
    print("error:", result.get("error"))
    if suggestion is None:
        print("suggestion: None")
    else:
        print("suggestion:", suggestion.model_dump(mode="json"))


if __name__ == "__main__":
    main()