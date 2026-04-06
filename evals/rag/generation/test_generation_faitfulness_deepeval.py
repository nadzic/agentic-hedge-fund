import os

import pytest
from deepeval import assert_test
from deepeval.metrics import FaithfulnessMetric
from deepeval.test_case import LLMTestCase

from .helpers import generate_answer, load_generation_cases

os.environ.setdefault("DEEPEVAL_PER_ATTEMPT_TIMEOUT_SECONDS_OVERRIDE", "180")
os.environ.setdefault("DEEPEVAL_PER_TASK_TIMEOUT_SECONDS_OVERRIDE", "420")
EVAL_MODEL = os.getenv("DEEPEVAL_EVAL_MODEL", "gpt-4o-mini")

@pytest.mark.parametrize("case", load_generation_cases(), ids=lambda case: case["id"])
def test_generation_faitfulness(case) -> None:

  payload = case["input"]
  if str(case.get("category", "")).startswith("adversarial"):
    pytest.skip("Faithfulness is noisy for adversarial refusal cases; use correctness/policy eval instead.")

  answer = generate_answer(
    query=payload["query"],
    symbol=payload["symbol"],
    horizon=payload["horizon"],
    retrieved_chunks=payload["retrieved_chunks"],
  )

  retrieval_context = [chunk["text"] for chunk in payload["retrieved_chunks"] if chunk.get("text")]
  if not retrieval_context:
    pytest.skip("Faithfulness is not applicable when retrieval context is empty.")

  test_case = LLMTestCase(
    input=payload["query"],
    actual_output=answer,
    retrieval_context=retrieval_context,
  )

  metric = FaithfulnessMetric(threshold=0.70, model=EVAL_MODEL)

  assert_test(test_case, [metric], run_async=False)

