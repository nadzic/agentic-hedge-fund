import json
from pathlib import Path
from typing import Any

DATASET_PATH = Path(__file__).parent / "datasets" / "generation" / "generation_golden_v1.json"
ALLOWED_HORIZONS = {"intraday", "swing", "position"}


def _load_dataset() -> list[dict[str, Any]]:
    with DATASET_PATH.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def test_generation_dataset_structure() -> None:
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
        assert isinstance(payload["symbol"], str)
        assert payload["symbol"].strip()
        assert payload["horizon"] in ALLOWED_HORIZONS

        chunks = payload["retrieved_chunks"]
        assert isinstance(chunks, list)
        for chunk in chunks:
            assert isinstance(chunk["text"], str)
            assert chunk["text"].strip()

            source_id = chunk.get("source_id")
            if source_id is not None:
                assert isinstance(source_id, str)
                assert source_id.strip()


def test_generation_expected_contract() -> None:
    cases = _load_dataset()
    for case in cases:
        expected = case["expected_generation"]
        assert isinstance(expected["must_mention_any"], list)
        assert expected["must_mention_any"]
        assert all(isinstance(value, str) and value.strip() for value in expected["must_mention_any"])

        assert isinstance(expected["must_not_mention_any"], list)
        assert all(isinstance(value, str) for value in expected["must_not_mention_any"])

        assert isinstance(expected["min_citations"], int)
        assert expected["min_citations"] >= 0

        assert isinstance(expected["allow_idk"], bool)
