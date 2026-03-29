from abc import ABC, abstractmethod

from pydantic import BaseModel, Field

from app.observability.tracing import observe
from app.rag.retrieval.retrieval import RetrievedChunk


class RerankingRequest(BaseModel):
  query: str
  retrieved_chunks: list[RetrievedChunk]
  top_k: int = Field(10, ge=1, le=50)

class RerankingService(ABC):
  @abstractmethod
  def rerank(self, request: RerankingRequest) -> list[RetrievedChunk]:
    raise NotImplementedError

class CrossEncoderRerankingService(RerankingService):
  """ 
  Cross -encoder model-based reranker (consdering query and retrieved chunks)
  Default:
    - BAAI/bge-reranker-base
  """

  def __init__(self, model_name: str = "BAAI/bge-reranker-base") -> None:
    try:
      from sentence_transformers import CrossEncoder
    except ImportError as exc:
      raise ImportError(
          "Model reranker requires sentence-transformers. "
          "Install with: uv add sentence-transformers"
      ) from exc

    self.model: CrossEncoder = CrossEncoder(model_name)

  @observe(name="rag.reranking.cross_encoder.rerank")
  def rerank(self, request: RerankingRequest) -> list[RetrievedChunk]:
    chunks = request.retrieved_chunks
    if not chunks:
      return []

    # Build (query, chunk) pairs for cross-encoder scoring
    pairs = [(
      request.query,
      chunk.text,
    ) for chunk in chunks]
    scores = self.model.predict(pairs)

    # Score by model score descending
    ranked = sorted(
        zip(scores, chunks, strict=False),
        key=lambda x: float(x[0]),
        reverse=True,
    )

    return [chunk for _, chunk in ranked[:request.top_k]]
    