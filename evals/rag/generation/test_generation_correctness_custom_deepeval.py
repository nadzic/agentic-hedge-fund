import os

import pytest
from deepeval import assert_test
from deepeval.metrics import GEval
from deepeval.test_case import LLMTestCase, LLMTestCaseParams

from .helpers import generate_answer, load_generation_cases

os.environ.setdefault("DEEPEVAL_PER_ATTEMPT_TIMEOUT_SECONDS_OVERRIDE", "180")
os.environ.setdefault("DEEPEVAL_PER_TASK_TIMEOUT_SECONDS_OVERRIDE", "420")
EVAL_MODEL = os.getenv("DEEPEVAL_EVAL_MODEL", "gpt-4o-mini")

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
        model=EVAL_MODEL,
    )

    assert_test(test_case, [correctness_metric], run_async=False)