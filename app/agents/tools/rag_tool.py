from __future__ import annotations

from typing import Literal

from langchain.tools import tool
from pydantic import BaseModel

from app.observability.tracing import observe
from app.rag.core.config import QDRANT_COLLECTION
from app.rag.retrieval.retrieval import (
    FilterValue,
    QdrantRetrievalService,
    RetrievalRequest,
)

_retrieval_service: QdrantRetrievalService | None = None

class RagChunk(BaseModel):
    rank: int
    score: float | None
    text: str
    source_id: str | None = None
    source_type: str | None = None
    symbol: str | None = None
    url: str | None = None

class RagToolResult(BaseModel):
    status: Literal["ok", "error"]
    query: str
    symbol: str | None
    count: int
    chunks: list[RagChunk]
    error: str | None = None

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
    requested_symbol = symbol.upper() if symbol else None
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
        compact_chunks: list[RagChunk] = []
        for idx, chunk in enumerate(chunks[:8], start=1):
            metadata = chunk.metadata or {}
            chunk_symbol = str(metadata.get("symbol"))
            if chunk_symbol:
                source_id = str(metadata.get("source_id")) if metadata.get("source_id") else None
                source_type = (
                    str(metadata.get("source_type")) if metadata.get("source_type") else None
                )
                compact_chunks.append(
                    RagChunk(
                        rank=idx,
                        score=chunk.score,
                        text=chunk.text[:600],
                        source_id=source_id,
                        source_type=source_type,
                        symbol=chunk_symbol,
                        url=str(metadata.get("url")) if metadata.get("url") else None,
                    )
                )
        return RagToolResult(
            status="ok",
            query=query,
            symbol=requested_symbol,
            count=len(compact_chunks),
            chunks=compact_chunks,
        ).model_dump_json()
    except Exception as exc:
        return RagToolResult(
            status="error",
            query=query,
            symbol=requested_symbol,
            count=0,
            chunks=[],
            error=str(exc),
        ).model_dump_json()