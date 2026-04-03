# RAG Eval Structure

This folder organizes RAG evaluation assets into three layers:

- `retrieval`: Measures document/chunk retrieval quality (before LLM answer generation).
- `generation`: Measures answer quality from fixed retrieved context.
- `e2e`: Measures full pipeline quality from user query to final response.

## Folder Layout

- `datasets/retrieval/retrieval_golden_v1.json`
- `datasets/generation/generation_golden_v1.json`
- `datasets/e2e/rag_query_golden_v1.json`
- `test_retrieval_eval.py`
- `test_generation_eval.py`
- `test_e2e_eval.py`

## Why split by layers

- Faster debugging: isolate retrieval failures from generation failures.
- Cleaner ownership: each layer can have separate quality gates.
- Better stability: generation tests can run on deterministic fixed context.

## Typical flow

1. Validate dataset contracts with `pytest evals/rag -q --no-cov`.
2. Run retrieval evals and inspect misses / irrelevant chunks.
3. Run generation evals with frozen context and score grounding quality.
4. Run e2e evals to verify real user-path behavior.
