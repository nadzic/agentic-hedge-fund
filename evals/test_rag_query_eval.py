import json
from collections import Counter
from pathlib import Path
from typing import Any

DATASET_PATH = Path(__file__).parent / "datasets" / "rag_query_golden_v1.json"
ALLOWED_HORIZONS = {"intraday", "swing", "position"}


def _load_dataset() -> list[dict[str, Any]]:
    with DATASET_PATH.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def test_rag_golden_dataset_structure() -> None:
    cases = _load_dataset()
    assert len(cases) == 12

    counts = Counter(case["category"] for case in cases)
    assert counts["normal"] == 5
    assert counts["edge_sparse_context"] == 1
    assert counts["edge_missing_symbol"] == 1
    assert counts["edge_ambiguous_query"] == 1
    assert counts["edge_noisy_input"] == 1
    assert counts["adversarial_prompt_injection"] == 1
    assert counts["adversarial_non_public_data"] == 1
    assert counts["adversarial_confidence_hack"] == 1


def test_rag_golden_dataset_request_contract() -> None:
    cases = _load_dataset()
    ids: set[str] = set()
    for case in cases:
        case_id = case["id"]
        assert case_id not in ids
        ids.add(case_id)

        payload = case["input"]
        assert isinstance(payload["query"], str)
        assert len(payload["query"]) >= 15

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
