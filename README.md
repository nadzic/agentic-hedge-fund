# Agentic Hedge Fund

[![CI](https://github.com/nadzic/agentic-hedge-fund/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/nadzic/agentic-hedge-fund/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/python-3.11%2B-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white)
![Next.js](https://img.shields.io/badge/Next.js-000000?logo=next.js&logoColor=white)
![LangGraph](https://img.shields.io/badge/LangGraph-agent%20orchestration-1C3C3C)
![Qdrant](https://img.shields.io/badge/Qdrant-vector%20search-DC244C)

An end-to-end, agent-based research stack for equity signal generation using:
- multi-node analyst orchestration (LangGraph),
- hybrid RAG retrieval (Qdrant + dense/sparse search),
- LLM reasoning and synthesis,
- FastAPI + Next.js for API and UI delivery.

## What This Project Does

Given a user query (for example: *"Should I buy NVDA for a swing trade?"*), the system:
1. Fan-outs work across analyst nodes (fundamentals, technicals, valuation, sentiment),
2. Runs domain services per analyst (indicators, valuation/fundamental metrics, sentiment sources),
3. Optionally generates structured analyst narratives with LLMs,
4. Synthesizes analyst outputs into a final suggestion,
5. Applies risk constraints before returning a response through the API.

## Architecture

### Core Components
- `app/agents/graph/`: LangGraph workflow, state, schemas, and nodes
- `app/agents/services/`: domain services used by analyst nodes
  - `fundamentals/`
  - `technicals/`
  - `valuation/`
  - `sentiment/`
- `app/rag/indexing/`: ingestion + chunking + Qdrant indexing
- `app/rag/retrieval/`: hybrid retrieval with metadata filters
- `app/rag/generation/`: answer generation grounded in retrieved context
- `app/api/`: FastAPI routers, schemas, and endpoints
- `app/services/`: API service layer bridging endpoints to graph/RAG pipelines
- `app/frontend/`: Next.js app for signals, RAG query, and ingest workflows

### High-Level Flow
`API request -> Graph orchestration -> Analyst services (+ optional LLM reasoning) -> Synthesis -> Risk manager -> API response`

## Tech Stack

- Python 3.11+
- FastAPI + Uvicorn
- LangGraph + LangChain
- LlamaIndex
- Qdrant (vector database)
- yfinance + external news APIs (optional) for analyst data
- Next.js (frontend)
- Docker + Docker Compose
- `uv` for dependency management

## Repository Structure

```text
app/
  frontend/
    src/
      app/
      components/
      lib/
  api/
    router.py
    routes/
      health.py
      analyze.py
      rag_query.py
      rag_ingest.py
    schemas/
      signal.py
      rag.py
  agents/
    graph/
      workflow.py
      state.py
      schemas.py
      nodes/
        orchestrator.py
        analysts/
          __init__.py
          fundamental_analyst.py
          technical_analyst.py
          valuation_analyst.py
          sentiment_analyst.py
        synthesizer.py
        risk_manager.py
    services/
      llm.py
      fundamentals/
      technicals/
      valuation/
      sentiment/
  rag/
    ingestion/
    indexing/
    retrieval/
    generation/
    reranking/
  services/
    signal_service.py
Dockerfile
Dockerfile.dev
docker-compose.yml
```

## Quickstart (Local with `uv`)

### 1) Install dependencies
```bash
uv sync
```

### 2) Configure environment
Create `.env` (or copy from `sample.env`) and set at least:
- `OPENAI_API_KEY`
- `LLM_PROVIDER`
- `LLM_MODEL_NAME`
- `QDRANT_URL` (for local non-Docker run, usually `http://localhost:6333`)
- `ALLOWED_ORIGINS` (for local frontend, usually `http://localhost:3000,http://127.0.0.1:3000`)
- Optional analyst-source keys:
  - `FINNHUB_API_KEY` (sentiment news source)
  - `ANTHROPIC_API_KEY` (if using Anthropic provider)

### 3) Run API
```bash
uv run uvicorn app.main:app --reload --app-dir .
```

Open:
- API docs: `http://localhost:8000/docs`
- Health: `http://localhost:8000/api/v1/health`

### 4) Run graph debug harness (optional)
```bash
uv run python -m app.agents.main
```
This prints stream updates and the final graph state for rapid node debugging.

## Quickstart (Docker Compose)

Runs API, Qdrant, and frontend for local development with hot-reload.

### Start
```bash
docker compose up --build
```

### Useful commands
```bash
# Start in background
docker compose up --build -d

# Follow logs
docker compose logs -f api
docker compose logs -f qdrant
docker compose logs -f frontend

# Stop and remove containers
docker compose down

# Stop + remove volumes (resets local Qdrant data)
docker compose down -v
```

### Endpoints
- API docs: `http://localhost:8000/docs`
- Health: `http://localhost:8000/api/v1/health`
- Analyze: `POST http://localhost:8000/api/v1/signals/analyze`
- RAG Query: `POST http://localhost:8000/api/v1/rag/query`
- RAG Ingest + Index: `POST http://localhost:8000/api/v1/rag/ingest-index`
- Qdrant: `http://localhost:6333`
- Frontend: `http://localhost:3000`

## API Endpoints

### Health Check
`GET /api/v1/health`

### Analyze Signal
`POST /api/v1/signals/analyze`

### RAG Query
`POST /api/v1/rag/query`

### RAG Ingest + Index
`POST /api/v1/rag/ingest-index`

Example request:

```json
{
  "query": "Should I buy NVDA for a swing trade?",
  "symbol": "NVDA",
  "horizon": "swing"
}
```

Example curl:
```bash
curl -X POST "http://localhost:8000/api/v1/signals/analyze" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Should I buy NVDA for a swing trade?",
    "symbol": "NVDA",
    "horizon": "swing"
  }'
```

Example response (shape):

```json
{
  "symbol": "NVDA",
  "signal": "buy",
  "confidence": 0.74,
  "reasoning": "Condensed synthesis of analyst outputs...",
  "warning": null,
  "error": null
}
```

## Deployment Model

- **Local development:** Docker Compose with API + frontend + local Qdrant.
- **Production / Cloud Run (recommended):**
  - deploy API and frontend as separate Cloud Run services,
  - use managed/external Qdrant service (`QDRANT_URL`),
  - inject secrets via Secret Manager (LLM keys, optional data-provider keys),
  - set `NEXT_PUBLIC_API_URL` at frontend image build time,
  - set `ALLOWED_ORIGINS` on API runtime to frontend Cloud Run domain.

## CI

GitHub Actions runs quality checks on push to `main`:
- Ruff lint
- BasedPyright type checking
- Pytest (if `tests/` exists)
- Python compile smoke check
- Docker build job

## Current Status

This repository is actively evolving. Key capabilities are in place, with ongoing improvements in:
- analyst node logic depth,
- weighting and consensus logic in synthesis,
- source-backed analyst services (technicals/fundamentals/valuation/sentiment),
- reranking quality,
- evaluation and monitoring.

## Disclaimer

Educational/research project. Not financial advice.
