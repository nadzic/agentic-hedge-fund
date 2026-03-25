# Agentic Hedge Fund

An end-to-end, agent-based research stack for equity signal generation using:
- multi-node analyst orchestration (LangGraph),
- hybrid RAG retrieval (Qdrant + dense/sparse search),
- LLM reasoning and synthesis,
- FastAPI for serving predictions.

This project is designed as a portfolio-grade reference architecture for building production-ready AI research systems.

## What This Project Does

Given a user query (for example: *"Should I buy NVDA for a swing trade?"*), the system:
1. Fan-outs work across analyst nodes (fundamentals, technicals, valuation, sentiment),
2. Retrieves relevant context from a hybrid vector index,
3. Synthesizes analyst outputs into a final suggestion,
4. Applies risk constraints before returning a response through the API.

## Architecture

### Core Components
- `app/agents/graph/`: LangGraph workflow and node orchestration
- `app/rag/indexing/`: ingestion + chunking + Qdrant indexing
- `app/rag/retrieval/`: hybrid retrieval with metadata filters
- `app/rag/generation/`: answer generation grounded in retrieved context
- `app/api/`: FastAPI routers, schemas, and endpoints
- `app/services/`: application service layer bridging API and graph

### High-Level Flow
`API request -> Graph orchestration -> Retrieval (Qdrant) -> Generation -> Synthesis -> Risk manager -> API response`

## Tech Stack

- Python 3.11+
- FastAPI + Uvicorn
- LangGraph + LangChain
- LlamaIndex
- Qdrant (vector database)
- Docker + Docker Compose
- `uv` for dependency management

## Repository Structure

```text
app/
  api/
    router.py
    routes/
      health.py
      analyze.py
    schemas/
      signal.py
  agents/
    graph/
      workflow.py
      state.py
      schemas.py
      nodes/
        orchestrator.py
        analysts.py
        synthesizer.py
        risk_manager.py
        common.py
  rag/
    ingestion/
    indexing/
    retrieval/
    generation/
    reranking/
  services/
    signal_service.py
Dockerfile
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
- `QDRANT_URL` (local default is usually `http://localhost:6333`)

### 3) Run API
```bash
uv run uvicorn app.main:app --reload --app-dir .
```

Open:
- Swagger UI: `http://localhost:8000/docs`

## Quickstart (Docker Compose)

Runs both API and Qdrant for local development:

```bash
docker compose up --build
```

Default endpoints:
- API: `http://localhost:8000`
- Qdrant: `http://localhost:6333`

## API Endpoints

### Health Check
`GET /health`

### Analyze Signal
`POST /signals/analyze`

Example request:

```json
{
  "query": "Should I buy NVDA for a swing trade?",
  "symbol": "NVDA",
  "horizon": "swing"
}
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

- **Local development:** Docker Compose with local Qdrant.
- **Production / Cloud Run:** Deploy API container separately; point `QDRANT_URL` to managed/external Qdrant service.

## Current Status

This repository is actively evolving. Key capabilities are in place, with ongoing improvements in:
- analyst node logic depth,
- synthesis weighting,
- reranking quality,
- evaluation and monitoring.

## Disclaimer

Educational/research project. Not financial advice.
