# Agentic Hedge Fund

[![CI](https://github.com/nadzic/agentic-hedge-fund/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/nadzic/agentic-hedge-fund/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/python-3.11%2B-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white)
![Next.js](https://img.shields.io/badge/Next.js-000000?logo=next.js&logoColor=white)
![LangGraph](https://img.shields.io/badge/LangGraph-agent%20orchestration-1C3C3C)
![Qdrant](https://img.shields.io/badge/Qdrant-vector%20search-DC244C)

An AI-native, multi-agent research assistant for stock trade ideas.

The project turns one user prompt into a structured signal by combining:
- analyst-specialized agents,
- retrieval-augmented market context,
- risk constraints,
- and a production-style API + frontend.

## Portfolio Overview

### Problem

Retail-style stock analysis is often fragmented: one tool for charts, another for news, another for valuation, and no consistent risk layer.

### Solution

This project provides a single pipeline that:
1. understands and validates user intent,
2. gathers context (RAG + insider signals),
3. runs multiple analyst agents in parallel,
4. synthesizes a final recommendation,
5. enforces risk thresholds before returning output.

### Why it is interesting

- Multi-agent orchestration with clear node boundaries (`LangGraph`).
- Retrieval + tool-augmented reasoning in one flow.
- End-to-end system design (backend, frontend, auth, voice input, CI).
- Practical API contract and reproducible local environment.

## What I Built

### Backend intelligence pipeline

- `symbol_resolver` infers/normalizes ticker symbol from user input.
- `input_classifier` validates query, symbol and horizon.
- `request_clarification` returns graceful no-trade + explanation for bad inputs.
- `market_research_agent` enriches state with:
  - RAG context from indexed documents,
  - insider-trading summary signal.
- Analyst fan-out nodes:
  - fundamentals,
  - technicals,
  - valuation,
  - sentiment.
- `synthesizer` combines analyst outputs into one proposal.
- `risk_manager` clamps/guards final output using risk limits.

### Product-facing features

- FastAPI endpoints for analysis, RAG query, and ingestion.
- Metadata endpoint `GET /api/v1/meta/model` for runtime model transparency.
- Next.js chat-style frontend for analysis workflow.
- Supabase authentication (`/sign-in`, `/sign-up`, OAuth callback).
- Voice dictation + transcription via `POST /api/transcribe` (ElevenLabs proxy route).

## System Flow

`request -> symbol_resolver -> input_classifier -> clarification OR research -> analyst fan-out -> synthesizer -> risk_manager -> response`

## API Surface

- `GET /api/v1/health`
- `GET /api/v1/meta/model`
- `POST /api/v1/signals/analyze`
- `POST /api/v1/rag/query`
- `POST /api/v1/rag/ingest-index`

Example analyze request:

```json
{
  "query": "Should I buy NVDA for a swing trade?",
  "symbol": "NVDA",
  "horizon": "swing"
}
```

Example analyze response shape:

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

## Tech Stack

### Backend

- Python 3.11
- FastAPI + Uvicorn
- LangGraph / LangChain
- LlamaIndex
- Qdrant
- yfinance + external APIs (optional, key-dependent)

### Frontend

- Next.js 16
- React 19
- TypeScript
- Supabase SSR client

### Tooling

- `uv` for Python dependency management
- Docker + Docker Compose
- Ruff + BasedPyright + Pytest
- GitHub Actions CI

## Run Locally

### 1) Backend

```bash
uv sync
uv run uvicorn app.main:app --reload --app-dir .
```

Create `.env` (copy `.env.example` or `sample.env`) and configure at least:
- `OPENAI_API_KEY` (or another configured provider key),
- `LLM_PROVIDER`,
- `LLM_MODEL_NAME`,
- `QDRANT_URL`,
- `ALLOWED_ORIGINS`.

Optional:
- `ANTHROPIC_API_KEY`
- `FINNHUB_API_KEY`
- `LANGFUSE_PUBLIC_KEY`
- `LANGFUSE_SECRET_KEY`

### 2) Frontend

```bash
cd app/frontend
npm install
npm run dev
```

Set `app/frontend/.env.local`:
- `NEXT_PUBLIC_API_URL` (default `http://localhost:8000/api/v1`)
- `NEXT_PUBLIC_SUPABASE_URL`
- `NEXT_PUBLIC_SUPABASE_ANON_KEY`
- `ELEVENLABS_API_KEY` (required for voice transcription)

### 3) Full stack with Docker

```bash
docker compose up --build
```

Useful URLs:
- API docs: `http://localhost:8000/docs`
- API health: `http://localhost:8000/api/v1/health`
- Frontend: `http://localhost:3000`
- Qdrant: `http://localhost:6333`

## Project Structure

```text
app/
  agents/
    graph/
      nodes/
    services/
      fundamentals/
      technicals/
      valuation/
      sentiment/
      insider/
  api/
    routes/
    schemas/
  rag/
    ingestion/
    indexing/
    retrieval/
    generation/
    reranking/
    pipelines/
  frontend/
    src/
      app/
      components/
      lib/
```

## Quality

CI checks on push to `main`:
- Ruff lint
- BasedPyright type checks
- Pytest (when tests exist)
- Python compile smoke checks
- Docker build

## TODOs

- jobs, workers, queues for ingestion and indexing
- fallback models
- try out smaller models for classification and routing and just bigger models for final generation
- fallback when api fails, default safe response
- llm provider orchestration to easy replace models 

## Disclaimer

Educational/research project. Not financial advice.
