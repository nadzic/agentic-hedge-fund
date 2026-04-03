import json
from pathlib import Path
from typing import Any

DATASET_PATH = Path(__file__).parent / "datasets" / "e2e" / "rag_query_golden_v1.json"
ALLOWED_HORIZONS = {"intraday", "swing", "position"}


def _load_dataset() -> list[dict[str, Any]]:
    with DATASET_PATH.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def test_e2e_dataset_structure() -> None:
    cases = _load_dataset()
    assert len(cases) >= 4

    ids: set[str] = set()
    for case in cases:
        case_id = case["id"]
        assert case_id not in ids
        ids.add(case_id)

        payload = case["input"]
        assert isinstance(payload["query"], str)
        assert len(payload["query"].strip()) >= 15

        symbol = payload.get("symbol")
        if symbol is not None:
            assert isinstance(symbol, str)
            assert symbol.strip()

        horizon = payload.get("horizon")
        if horizon is not None:
            assert horizon in ALLOWED_HORIZONS

        expected_behavior = case.get("expected_behavior")
        assert isinstance(expected_behavior, str)
        assert expected_behavior.strip()
