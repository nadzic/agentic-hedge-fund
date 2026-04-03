import json
from pathlib import Path
from typing import Any

DATASET_PATH = Path(__file__).parent / "datasets" / "nodes" / "nodes_golden_v1.json"
ALLOWED_NODES = {
    "symbol_resolver",
    "input_classifier",
    "market_research_agent",
    "synthesizer",
    "risk_manager",
}
ALLOWED_HORIZONS = {"intraday", "swing", "position"}


def _load_dataset() -> list[dict[str, Any]]:
    with DATASET_PATH.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def test_nodes_dataset_contract() -> None:
    cases = _load_dataset()
    assert len(cases) >= 3

    ids: set[str] = set()
    for case in cases:
        case_id = case["id"]
        assert case_id not in ids
        ids.add(case_id)

        assert case["node"] in ALLOWED_NODES
        assert isinstance(case["category"], str)
        assert case["category"].strip()

        payload = case["input"]
        assert isinstance(payload["query"], str)
        assert payload["query"].strip()

        symbol = payload.get("symbol")
        if symbol is not None:
            assert isinstance(symbol, str)

        horizon = payload.get("horizon")
        if horizon is not None:
            assert horizon in ALLOWED_HORIZONS

        expected_behavior = case["expected_behavior"]
        assert isinstance(expected_behavior, str)
        assert expected_behavior.strip()
