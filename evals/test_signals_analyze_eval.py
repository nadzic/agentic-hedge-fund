import json
from collections import Counter
from pathlib import Path
from typing import Any

DATASET_PATH = Path(__file__).parent / "datasets" / "signals_analyze_golden_v1.json"
ALLOWED_HORIZONS = {"intraday", "swing", "position"}


def _load_dataset() -> list[dict[str, Any]]:
    with DATASET_PATH.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def test_signals_golden_dataset_structure() -> None:
    cases = _load_dataset()
    assert len(cases) == 25

    counts = Counter(case["category"] for case in cases)
    assert counts["normal"] == 12
    assert counts["edge_missing_symbol"] == 4
    assert counts["edge_unclear_horizon"] == 4
    assert counts["adversarial_prompt_injection"] == 1
    assert counts["adversarial_overconfidence"] == 1
    assert counts["adversarial_conflicting_instruction"] == 1
    assert counts["noisy_input"] == 1
    assert counts["adversarial_data_request"] == 1


def test_signals_golden_dataset_request_contract() -> None:
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
