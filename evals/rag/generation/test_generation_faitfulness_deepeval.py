import pytest
from deepeval import assert_test
from deepeval.metrics import FaithfulnessMetric
from deepeval.test_case import LLMTestCase

from evals.rag.generation.helpers import generate_answer, load_generation_cases

@pytest.mark.parametrize("case", load_generation_cases(), ids=lambda case: case["id"])
def test_generation_faitfulness(case) -> None:

  payload = case["input"]

  answer = generate_answer(
    query=payload["query"],
    symbol=payload["symbol"],
    horizon=payload["horizon"],
    retrieved_chunks=payload["retrieved_chunks"],
  )

  retrieval_context = [chunk["text"] for chunk in payload["retrieved_chunks"] if chunk.get("text")]

  test_case = LLMTestCase(
    input=payload["query"],
    actual_output=answer,
    retrieval_context=retrieval_context,
  )

  metric = FaithfulnessMetric()

  assert_test(test_case, [metric])

