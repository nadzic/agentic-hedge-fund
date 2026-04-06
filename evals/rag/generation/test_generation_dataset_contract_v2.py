from .helpers import load_generation_cases

ALLOWED_HORIZONS = {"swing", "position", "intraday"}


def test_generation_dataset_structure_v2() -> None:
    cases = load_generation_cases()
    assert len(cases) >= 3

    seen_ids: set[str] = set()

    for case in cases:
        # Validate case ID
        case_id = case["id"]
        assert isinstance(case_id, str), "Case ID must be a string"
        assert case_id.strip(), "Case ID must not be empty"
        assert case_id not in seen_ids, f"Duplicate case ID: {case_id}"
        seen_ids.add(case_id)

        # Validate category
        category = case["category"]
        assert isinstance(category, str), "Category must be a string"
        assert category.strip(), "Category must not be empty"

        # Validate input payload
        payload = case["input"]
        query = payload["query"]
        symbol = payload["symbol"]
        horizon = payload["horizon"]
        retrieved_chunks = payload["retrieved_chunks"]

        assert isinstance(query, str), "Query must be a string"
        assert query.strip(), "Query must not be empty"
        assert isinstance(symbol, str), "Symbol must be a string"
        assert symbol.strip(), "Symbol must not be empty"
        assert horizon in ALLOWED_HORIZONS, f"Invalid horizon: {horizon}"
        assert isinstance(retrieved_chunks, list), "Retrieved chunks must be a list"

        for chunk in retrieved_chunks:
            assert isinstance(chunk, dict), "Each chunk must be a dict"
            text = chunk["text"]
            assert isinstance(text, str), "Chunk text must be a string"
            assert text.strip(), "Chunk text must not be empty"

            source_id = chunk.get("source_id")
            if source_id is not None:
                assert isinstance(source_id, str), "source_id must be a string if present"
                assert source_id.strip(), "source_id must not be empty if present"

        # Validate expected output
        expected_output = case["expected_output"]
        assert isinstance(expected_output, str), "Expected output must be a string"
        assert expected_output.strip(), "Expected output must not be empty"

        # Validate expected_generation
        expected_generation = case["expected_generation"]
        allow_idk = expected_generation["allow_idk"]
        assert isinstance(allow_idk, bool), "allow_idk must be a boolean"
