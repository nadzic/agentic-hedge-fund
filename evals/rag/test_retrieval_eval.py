import json
from pathlib import Path
from typing import Any

DATASET_PATH = Path(__file__).parent / "datasets" / "retrieval" / "retrieval_golden_v1.json"
ALLOWED_HORIZONS = {"intraday", "swing", "position"}


def _load_dataset() -> list[dict[str, Any]]:
    with DATASET_PATH.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def test_retrieval_dataset_structure() -> None:
    cases = _load_dataset()
    assert len(cases) >= 3

    ids: set[str] = set()
    for case in cases:
        case_id = case["id"]
        assert case_id not in ids
        ids.add(case_id)

        payload = case["input"]
        assert isinstance(payload["query"], str)
        assert payload["query"].strip()

        symbol = payload.get("symbol")
        if symbol is not None:
            assert isinstance(symbol, str)
            assert symbol.strip()

        horizon = payload.get("horizon")
        if horizon is not None:
            assert horizon in ALLOWED_HORIZONS

        top_k = payload.get("top_k")
        if top_k is not None:
            assert isinstance(top_k, int)
            assert 1 <= top_k <= 50


def test_retrieval_expected_contract() -> None:
    cases = _load_dataset()
    for case in cases:
        expected = case["expected_retrieval"]
        assert isinstance(expected["min_chunks"], int)
        assert expected["min_chunks"] >= 0

        assert isinstance(expected["must_include_any_source_ids"], list)
        assert all(isinstance(value, str) for value in expected["must_include_any_source_ids"])

        assert isinstance(expected["max_irrelevant_chunks"], int)
        assert expected["max_irrelevant_chunks"] >= 0
