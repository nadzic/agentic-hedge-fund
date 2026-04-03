import json
from pathlib import Path
from typing import Any

DATASET_PATH = Path(__file__).parent / "datasets" / "e2e" / "e2e_scenarios_v1.json"
ALLOWED_HORIZONS = {"intraday", "swing", "position"}
ALLOWED_SIGNALS = {"buy", "sell", "hold", "no_trade"}


def _load_dataset() -> list[dict[str, Any]]:
    with DATASET_PATH.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def test_e2e_dataset_contract() -> None:
    cases = _load_dataset()
    assert len(cases) >= 2

    ids: set[str] = set()
    for case in cases:
        case_id = case["id"]
        assert case_id not in ids
        ids.add(case_id)

        payload = case["input"]
        assert isinstance(payload["query"], str)
        assert len(payload["query"].strip()) >= 10

        symbol = payload.get("symbol")
        if symbol is not None:
            assert isinstance(symbol, str)

        horizon = payload.get("horizon")
        if horizon is not None:
            assert horizon in ALLOWED_HORIZONS

        expected = case["expected"]
        signal_any_of = expected["signal_any_of"]
        assert isinstance(signal_any_of, list)
        assert signal_any_of
        assert all(signal in ALLOWED_SIGNALS for signal in signal_any_of)

        min_confidence = expected["min_confidence"]
        assert isinstance(min_confidence, (int, float))
        assert 0.0 <= float(min_confidence) <= 1.0

        max_latency_ms = expected["max_latency_ms"]
        assert isinstance(max_latency_ms, int)
        assert max_latency_ms > 0

        forbidden = expected["must_not_include"]
        assert isinstance(forbidden, list)
        assert all(isinstance(item, str) and item.strip() for item in forbidden)
