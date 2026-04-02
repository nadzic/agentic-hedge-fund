# AI Eval Datasets

This folder stores versioned golden datasets and dataset integrity checks for AI evaluation.

## Files

- `datasets/signals_analyze_golden_v1.json`: Golden cases for `POST /api/v1/signals/analyze`.
- `datasets/rag_query_golden_v1.json`: Golden cases for `POST /api/v1/rag/query`.
- `test_signals_analyze_eval.py`: Dataset contract checks for analyze golden set.
- `test_rag_query_eval.py`: Dataset contract checks for RAG golden set.

## Why this exists

- Keep AI eval inputs versioned and reviewable in git.
- Separate AI eval assets from regular unit/integration tests.
- Create a stable baseline before adding live quality gates.

## Run checks

```bash
uv run pytest -q evals --no-cov
```

## Next step

Add live scoring runners that execute each case against API endpoints and compute:

- quality pass rate
- high-severity pass rate
- latency (p50/p95)
- top failure reasons
