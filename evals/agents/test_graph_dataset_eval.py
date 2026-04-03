import json
from pathlib import Path
from typing import Any

DATASET_PATH = Path(__file__).parent / "datasets" / "graph" / "graph_golden_v1.json"
ALLOWED_HORIZONS = {"intraday", "swing", "position"}


def _load_dataset() -> list[dict[str, Any]]:
    with DATASET_PATH.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def test_graph_dataset_contract() -> None:
    cases = _load_dataset()
    assert len(cases) >= 2

    ids: set[str] = set()
    for case in cases:
        case_id = case["id"]
        assert case_id not in ids
        ids.add(case_id)

        assert isinstance(case["category"], str)
        assert case["category"].strip()

        payload = case["input"]
        assert isinstance(payload["query"], str)
        assert len(payload["query"].strip()) >= 5

        symbol = payload.get("symbol")
        if symbol is not None:
            assert isinstance(symbol, str)

        horizon = payload.get("horizon")
        if horizon is not None:
            assert horizon in ALLOWED_HORIZONS

        route = case["expected_route"]
        assert isinstance(route, list)
        assert route
        assert all(isinstance(step, str) and step.strip() for step in route)

        terminal = case["expected_terminal"]
        assert isinstance(terminal, str)
        assert terminal.strip()
