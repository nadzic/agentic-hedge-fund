from __future__ import annotations
import json
from typing import Any
from langchain.tools import tool
from app.observability.tracing import observe
from app.rag.core.config import QDRANT_COLLECTION
from app.rag.retrieval.retrieval import (
    FilterValue,
    QdrantRetrievalService,
    RetrievalRequest,
)
_retrieval_service: QdrantRetrievalService | None = None

def _get_retrieval_service() -> QdrantRetrievalService:
    global _retrieval_service
    if _retrieval_service is None:
        _retrieval_service = QdrantRetrievalService(collection_name=QDRANT_COLLECTION)
    return _retrieval_service


@tool
@observe(name="agents.tools.rag_tool")
def rag_tool(
    query: str,
    symbol: str | None = None,
    top_k: int = 8,
    sparse_top_k: int = 20,
    alpha: float = 0.5,
    extra_filters: dict[str, FilterValue] | None = None,
) -> str:
    """
    Retrieve vector DB context and return compact JSON for agent usage.
    """
    try:
        filters = dict(extra_filters or {})
        if symbol:
            _ = filters.setdefault("symbol", symbol.upper())
        request = RetrievalRequest(
            query=query,
            top_k=top_k,
            sparse_top_k=sparse_top_k,
            alpha=alpha,
            filters=filters,
        )
        chunks = _get_retrieval_service().retrieve(request)
        compact_chunks: list[dict[str, Any]] = []
        for idx, chunk in enumerate(chunks[:8], start=1):
            metadata = chunk.metadata or {}
            compact_chunks.append(
                {
                    "rank": idx,
                    "score": chunk.score,
                    "text": chunk.text[:600],
                    "source_id": metadata.get("source_id"),
                    "source_type": metadata.get("source_type"),
                    "symbol": metadata.get("symbol"),
                    "url": metadata.get("url"),
                }
            )
        payload = {
            "status": "ok",
            "query": query,
            "symbol": symbol.upper() if symbol else None,
            "count": len(compact_chunks),
            "chunks": compact_chunks,
        }
        return json.dumps(payload)
    except Exception as exc:
        return json.dumps(
            {
                "status": "error",
                "query": query,
                "symbol": symbol.upper() if symbol else None,
                "count": 0,
                "chunks": [],
                "error": str(exc),
            }
        )