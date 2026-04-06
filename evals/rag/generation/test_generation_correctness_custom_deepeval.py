import pytest
from deepeval import assert_test
from deepeval.metrics import GEval
from deepeval.test_case import LLMTestCase, LLMTestCaseParams

from evals.rag.generation.helpers import generate_answer, load_generation_cases

@pytest.mark.parametrize("case", load_generation_cases(), ids=lambda case: case["id"])
def test_generation_correctness(case) -> None:
    payload = case["input"]

    answer = generate_answer(
        query=payload["query"],
        symbol=payload["symbol"],
        horizon=payload["horizon"],
        retrieved_chunks=payload.get("retrieved_chunks", []),
    )

    test_case = LLMTestCase(
        input=payload["query"],
        actual_output=answer,
        expected_output=case["expected_output"],
    )

    correctness_metric = GEval(
        name="correctness",
        criteria=(
            "Determine whether the actual output correctly answers the user's question "
            "based on the expected output. Reward accurate, complete, and appropriately cautious answers. "
            "Penalize contradictions, missing key facts, fabricated specifics, and compliance failures."
        ),
        evaluation_params=[
            LLMTestCaseParams.INPUT,
            LLMTestCaseParams.ACTUAL_OUTPUT,
            LLMTestCaseParams.EXPECTED_OUTPUT,
        ],
        threshold=0.65,
    )

    assert_test(test_case, [correctness_metric])