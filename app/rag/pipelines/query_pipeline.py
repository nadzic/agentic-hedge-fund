from __future__ import annotations

from app.agents.services.llm import get_llm
from app.rag.reranking.reranking import RerankingService
from app.rag.generation.generation import (
  GenerationRequest,
  GenerationService,
  LLMGenerationService,
)
from app.rag.reranking.reranking import RerankingRequest
from app.rag.retrieval.retrieval import (
  QdrantRetrievalService,
  RetrievalRequest,
  RetrievalService,
)
from app.rag.pipelines.types import QueryPipelineRequest, QueryPipelineResult


class RagQueryPipeline:
  def __init__(
    self,
    retrieval_service: RetrievalService,
    generation_service: GenerationService,
    reranking_service: RerankingService,
    rerank_enabled: bool = True,
    rerank_top_k: int = 10,
  ) -> None:
    self.retrieval_service = retrieval_service
    self.generation_service = generation_service
    self.reranking_service = reranking_service
    self.rerank_enabled = rerank_enabled
    self.rerank_top_k = rerank_top_k
    
  @classmethod
  def default(cls, collection_name: str,
    reranking_service: RerankingService,
    rerank_enabled: bool = True,
    rerank_top_k: int = 10,
  ) -> "RagQueryPipeline":
    retrieval_service = QdrantRetrievalService(collection_name=collection_name)
    generation_service = LLMGenerationService(llm=get_llm())
    return cls(
      retrieval_service=retrieval_service,
      generation_service=generation_service,
      reranking_service=reranking_service,
      rerank_enabled=rerank_enabled,
      rerank_top_k=rerank_top_k,
    )

  def run(self, request: QueryPipelineRequest) -> QueryPipelineResult:
    filters = dict(request.extra_filters or {})
    _ = filters.setdefault("symbol", request.symbol.upper())

    retrieval_request = RetrievalRequest(
      query=request.query,
      top_k=request.top_k,
      sparse_top_k=request.sparse_top_k,
      alpha=request.alpha,
      filters=filters
    )
    chunks = self.retrieval_service.retrieve(retrieval_request)

    if self.rerank_enabled and self.reranking_service is not None and chunks:
      rerank_k = min(self.rerank_top_k, len(chunks))
      chunks = self.reranking_service.rerank(
        request=RerankingRequest(
          query=request.query,
          retrieved_chunks=chunks,
          top_k=rerank_k,
        )
      )

    generation_request = GenerationRequest(
      query=request.query,
      symbol=request.symbol.upper(),
      horizon=request.horizon,
      retrieved_chunks=chunks,
      max_context_chunks=request.max_context_chunks
    )
    generation_response = self.generation_service.generate(generation_request)

    return QueryPipelineResult(
      answer=generation_response.answer,
      confidence=generation_response.confidence,
      citations=generation_response.citations,
      reasoning=generation_response.reasoning,
      retrieved_chunks=chunks,
    )
