from __future__ import annotations

from app.rag.core.config import QDRANT_COLLECTION, RERANK_ENABLED, RERANK_TOP_K
from app.rag.pipelines.ingest_index_pipeline import IngestIndexPipeline
from app.rag.pipelines.query_pipeline import RagQueryPipeline
from app.rag.reranking.reranking import CrossEncoderRerankingService

_ingest_index_pipeline: IngestIndexPipeline | None = None
_query_pipeline: RagQueryPipeline | None = None


def get_ingest_index_pipeline() -> IngestIndexPipeline:
  global _ingest_index_pipeline
  if _ingest_index_pipeline is None:
    _ingest_index_pipeline = IngestIndexPipeline()
  return _ingest_index_pipeline


def get_query_pipeline() -> RagQueryPipeline:
  global _query_pipeline
  if _query_pipeline is None:
    reranker = CrossEncoderRerankingService()
    _query_pipeline = RagQueryPipeline.default(
        collection_name=QDRANT_COLLECTION,
        reranking_service=reranker,
        rerank_enabled=RERANK_ENABLED,
        rerank_top_k=RERANK_TOP_K,
    )
  return _query_pipeline
