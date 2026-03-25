from __future__ import annotations

from app.rag.core.config import QDRANT_COLLECTION
from app.rag.retrieval.retrieval import (
  FilterValue,
  QdrantRetrievalService,
  RetrievalRequest,
  RetrievedChunk,
)

_retrieval_service: QdrantRetrievalService | None = None

def _get_retrieval_service() -> QdrantRetrievalService:
  global _retrieval_service
  if _retrieval_service is None:
    _retrieval_service = QdrantRetrievalService(collection_name=QDRANT_COLLECTION)
  return _retrieval_service

def run_research_vectordatabase(
    query: str,
    symbol: str | None = None,
    top_k: int = 8,
    sparse_top_k: int = 20,
    alpha: float = 0.5,
    extra_filters: dict[str, FilterValue] | None = None
) -> list[RetrievedChunk]:
  filters = dict(extra_filters or {})
  if symbol:
    _ = filters.setdefault("symbol", symbol.upper())

  request = RetrievalRequest(
    query=query,
    top_k=top_k,
    sparse_top_k=sparse_top_k,
    alpha=alpha,
    filters=filters
  )

  retrieval_service = _get_retrieval_service()
  return retrieval_service.retrieve(request)