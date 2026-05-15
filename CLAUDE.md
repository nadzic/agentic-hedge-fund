# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

### Backend

```bash
uv sync --extra dev          # install all dependencies including dev
uv run uvicorn app.main:app --reload --app-dir .   # run dev server

uv run ruff check .          # lint
uv run ruff check --fix .    # lint + autofix
uv run basedpyright --level error .   # type check

uv run pytest -q             # full test suite (same as CI)
uv run pytest -q -m unit     # fast unit tests only
uv run pytest -q -m "integration or e2e"
uv run pytest -q tests/path/to/test_file.py::test_name   # single test
```

### Frontend (`app/frontend`)

```bash
npm install && npm run dev   # install + start dev server
npm run lint                 # ESLint
npm run typecheck            # tsc --noEmit
npm run format:write         # Prettier fix
npm run test                 # Vitest (run once)
npm run test:watch           # Vitest watch mode
```

### All CI checks locally

```bash
./run_ci_checks.sh           # runs frontend + python checks
```

### Evals

```bash
# Contract tests (run in CI):
uv run pytest -q evals/rag/generation/test_generation_dataset_contract_v2.py

# LLM evals (require OPENAI_API_KEY, run on schedule in CI):
uv run pytest -q evals/rag/generation/test_generation_faitfulness_deepeval.py \
  evals/rag/generation/test_generation_relevancy_deepeval.py \
  evals/rag/generation/test_generation_correctness_custom_deepeval.py
```

## Architecture

### Request flow

```
POST /api/v1/signals/analyze
  → signal_service.run_signal_stream_sync()
    → LangGraph: symbol_resolver → input_classifier
        → [invalid] request_clarification → END
        → [valid]   market_research_agent (RAG + insider)
                      → orchestrator → [analyst fan-out]
                            fundamentals / technicals / valuation / sentiment
                          → synthesizer → risk_manager → END
```

The graph is defined in `app/agents/graph/workflow.py`. Shared state between all nodes is `HedgeFundState` (TypedDict) in `app/agents/graph/state.py`. `analyst_outputs` uses `Annotated[list, operator.add]` so parallel analyst nodes can safely write to the same list.

### Agent layer (`app/agents/`)

- `graph/nodes/` — one file per graph node; analysts live in `nodes/analysts/`
- `graph/schemas.py` — Pydantic models for `SignalInput`, `AnalystOutput`, `SuggestionOutput`, `RiskLimits`
- `services/<domain>/` — each analyst domain has its own `data_client`, `scoring`, `<domain>_reasoning` modules
- `services/llm.py` — `get_llm()` factory; driven by `LLM_PROVIDER` + `LLM_MODEL_NAME` env vars (supports `openai` and `anthropic`)
- `tools/` — LangChain tools wrapping RAG and insider signal for use inside agent nodes

### RAG layer (`app/rag/`)

`RagQueryPipeline` (in `pipelines/query_pipeline.py`) composes three steps:
1. **Retrieval** — hybrid search (dense + sparse) against Qdrant (`retrieval/retrieval.py`)
2. **Reranking** — optional cross-encoder reranker (`reranking/reranking.py`), default model `BAAI/bge-reranker-base`, local model stored in `models/reranker/`
3. **Generation** — LLM call with retrieved context (`generation/generation.py`)

Ingestion pipeline is in `pipelines/ingest_index_pipeline.py`; it supports PDF and URL sources. Qdrant collection name and indexing config live in `rag/core/`.

### API layer (`app/api/`)

`app/main.py` → `app/api/router.py` mounts routes under `/api/v1`. Each route module under `app/api/routes/` calls a service in `app/services/`. Schemas (request/response models) live in `app/api/schemas/`.

The analyze route (`routes/analyze.py`) streams SSE updates — each LangGraph node emits a `{"type": "update", "payload": {"node": ..., "update": ...}}` event; the final event is `{"type": "final", "payload": SignalResponse}`.

Rate limiting uses Supabase RPC (`check_and_increment_usage_limit`) — SQL schema is in `app/api/supabase_rate_limit.sql`. Anonymous users are tracked via signed cookie (`RATE_LIMIT_COOKIE_SECRET`).

### Observability

All key pipeline steps are decorated with `@observe` (re-exported from `app/observability/tracing.py`). This maps to Langfuse when `LANGFUSE_PUBLIC_KEY` and `LANGFUSE_SECRET_KEY` are set; otherwise it is a no-op. LangChain calls are traced via `CallbackHandler` injected into `get_llm()`.

### Frontend (`app/frontend/`)

Next.js 16 + React 19. **This version of Next.js has breaking changes** — read `node_modules/next/dist/docs/` before writing any new Next.js-specific code. Supabase SSR client handles auth; auth routes are `sign-in/`, `sign-up/`, and `app/api/auth/`. Voice transcription is a proxy route at `app/api/transcribe` forwarding to ElevenLabs.

## Testing strategy

Three pytest markers enforced with `--strict-markers`: `unit`, `integration`, `e2e`. Tests live in `tests/api/` and `tests/agents/` mirroring the source layout. Coverage threshold is **85%** on `app.main`, `app.api.router`, `app.api.routes.meta`, and `app.api.routes.analyze`.

`evals/` contains LLM quality evaluations using `deepeval`. Contract tests (dataset schema checks) run in every CI build; LLM-graded evals run nightly or on manual dispatch.

## Environment

Copy `sample.env` to `.env`. Required for backend: `OPENAI_API_KEY` (or provider key), `LLM_PROVIDER`, `LLM_MODEL_NAME`, `QDRANT_URL`. Required for auth/rate-limiting: `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_ROLE_KEY`, `RATE_LIMIT_COOKIE_SECRET`. Frontend `.env.local` needs `NEXT_PUBLIC_API_URL`, `NEXT_PUBLIC_SUPABASE_URL`, `NEXT_PUBLIC_SUPABASE_ANON_KEY`, `ELEVENLABS_API_KEY`.
