from __future__ import annotations

from pydantic import BaseModel, Field

from app.rag.core.config import MIN_DOC_CHARS, PROCESSED_JSONL_PATH, QDRANT_COLLECTION
from app.rag.retrieval.retrieval import FilterValue, RetrievedChunk


class IngestIndexRequest(BaseModel):
  pdf_paths: list[str] = Field(default_factory=list)
  pdf_recursive: bool = False
  urls: list[str] = Field(default_factory=list)
  min_chars: int = Field(MIN_DOC_CHARS, ge=1)
  snapshot_path: str = PROCESSED_JSONL_PATH
  collection_name: str = QDRANT_COLLECTION


class IngestIndexResult(BaseModel):
  input_count: int
  transformed_count: int
  dropped_empty_or_short: int
  dropped_challenge_or_junk: int
  indexed_count: int
  snapshot_path: str
  collection_name: str


class QueryPipelineRequest(BaseModel):
  query: str
  symbol: str
  horizon: str = "swing"
  top_k: int = Field(8, ge=1, le=50)
  sparse_top_k: int = Field(20, ge=1, le=200)
  alpha: float = Field(0.5, ge=0.0, le=1.0)
  max_context_chunks: int = Field(5, ge=1, le=30)
  extra_filters: dict[str, FilterValue] | None = None


class QueryPipelineResult(BaseModel):
  answer: str
  confidence: float | None = None
  citations: list[str] = Field(default_factory=list)
  reasoning: str | None = None
  retrieved_chunks: list[RetrievedChunk] = Field(default_factory=list)
