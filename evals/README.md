# AI Eval Datasets

This folder stores versioned golden datasets and dataset integrity checks for AI evaluation.

## Files

- `datasets/signals_analyze_golden_v1.json`: Golden cases for `POST /api/v1/signals/analyze`.
- `test_signals_analyze_eval.py`: Dataset contract checks for analyze golden set.
- `test_rag_query_eval.py`: Dataset contract checks for RAG query e2e golden set (`evals/rag/datasets/e2e`).

## RAG layered structure

RAG evals are also organized by layer under `evals/rag`:

- `retrieval`: retrieval quality for relevant chunks/documents
- `generation`: response quality given fixed retrieved context
- `e2e`: full pipeline quality from user query to final answer

See `evals/rag/README.md` for the full structure and conventions.

## Agents minimal structure

Agent evals are available under `evals/agents` with minimal folders for:

- `datasets` (`nodes`, `graph`, `e2e`)
- `runners`
- `metrics`
- `configs`

See `evals/agents/README.md` for details and next steps.

## Why this exists

- Keep AI eval inputs versioned and reviewable in git.
- Separate AI eval assets from regular unit/integration tests.
- Create a stable baseline before adding live quality gates.

## Run checks

```bash
uv run pytest -q evals --no-cov
uv run pytest -q evals/rag --no-cov
uv run pytest -q evals/agents --no-cov
```

## Next step

Add live scoring runners that execute each case against API endpoints and compute:

- quality pass rate
- high-severity pass rate
- latency (p50/p95)
- top failure reasons
