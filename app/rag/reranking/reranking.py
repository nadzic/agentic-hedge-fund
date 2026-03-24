from abc import ABC, abstractmethod

from pydantic import BaseModel, Field

from app.rag.retrieval.retrieval import RetrievedChunk

class RerankingRequest(BaseModel):
  query: str
  retrieved_chunks: list[RetrievedChunk]
  top_k: int = Field(10, ge=1, le=50)

class RerankingService(ABC):
  @abstractmethod
  def rerank(self, request: RerankingRequest) -> list[RetrievedChunk]:
    raise NotImplementedError