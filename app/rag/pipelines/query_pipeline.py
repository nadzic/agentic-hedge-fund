from __future__ import annotations

from app.agents.services.llm import get_llm
from app.observability.tracing import observe
from app.rag.generation.generation import (
  GenerationRequest,
  GenerationResponse,
  GenerationService,
  LLMGenerationService,
)
from app.rag.pipelines.types import QueryPipelineRequest, QueryPipelineResult
from app.rag.reranking.reranking import RerankingRequest, RerankingService
from app.rag.retrieval.retrieval import (
  QdrantRetrievalService,
  RetrievalRequest,
  RetrievalService,
  RetrievedChunk,
)


class RagQueryPipeline:
  def __init__(
    self,
    retrieval_service: RetrievalService,
    generation_service: GenerationService,
    reranking_service: RerankingService | None = None,
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
    reranking_service: RerankingService | None = None,
    rerank_enabled: bool = True,
    rerank_top_k: int = 10,
  ) -> RagQueryPipeline:
    retrieval_service = QdrantRetrievalService(collection_name=collection_name)
    generation_service = LLMGenerationService(llm=get_llm())
    return cls(
      retrieval_service=retrieval_service,
      generation_service=generation_service,
      reranking_service=reranking_service,
      rerank_enabled=rerank_enabled,
      rerank_top_k=rerank_top_k,
    )

  @observe(name="rag.query.pipeline.run")
  def run(self, request: QueryPipelineRequest) -> QueryPipelineResult:
    chunks = self._retrieve(request)

    if self.rerank_enabled and self.reranking_service is not None and chunks:
      chunks = self._rerank(query=request.query, chunks=chunks)

    generation_response = self._generate(request=request, chunks=chunks)

    return QueryPipelineResult(
      answer=generation_response.answer,
      confidence=generation_response.confidence,
      citations=generation_response.citations,
      reasoning=generation_response.reasoning,
      retrieved_chunks=chunks,
    )

  @observe(name="rag.query.pipeline.retrieve")
  def _retrieve(self, request: QueryPipelineRequest) -> list[RetrievedChunk]:
    filters = dict(request.extra_filters or {})
    _ = filters.setdefault("symbol", request.symbol.upper())

    retrieval_request = RetrievalRequest(
      query=request.query,
      top_k=request.top_k,
      sparse_top_k=request.sparse_top_k,
      alpha=request.alpha,
      filters=filters
    )
    return self.retrieval_service.retrieve(retrieval_request)

  @observe(name="rag.query.pipeline.rerank")
  def _rerank(self, query: str, chunks: list[RetrievedChunk]) -> list[RetrievedChunk]:
    if self.reranking_service is None or not chunks:
      return chunks
    rerank_k = min(self.rerank_top_k, len(chunks))
    return self.reranking_service.rerank(
      request=RerankingRequest(
        query=query,
        retrieved_chunks=chunks,
        top_k=rerank_k,
      )
    )

  @observe(name="rag.query.pipeline.generate")
  def _generate(
    self,
    request: QueryPipelineRequest,
    chunks: list[RetrievedChunk],
  ) -> GenerationResponse:
    generation_request = GenerationRequest(
      query=request.query,
      symbol=request.symbol.upper(),
      horizon=request.horizon,
      retrieved_chunks=chunks,
      max_context_chunks=request.max_context_chunks
    )
    return self.generation_service.generate(generation_request)
