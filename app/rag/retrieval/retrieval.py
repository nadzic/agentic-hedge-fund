from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from llama_index.core import VectorStoreIndex
from llama_index.core.vector_stores import FilterOperator, MetadataFilter, MetadataFilters
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.vector_stores.qdrant import QdrantVectorStore
from pydantic import BaseModel, Field
from qdrant_client import QdrantClient


class RetrievalRequest(BaseModel):
  query: str
  # Keep high top_k for downstream reranking
  top_k: int = Field(30, ge=1, le=50)
  filters: dict[str, Any] | None = None
  sparse_top_k: int = Field(30, ge=1, le=200)
  alpha: float = Field(0.5, ge=0.0, le=1.0)

class RetrievedChunk(BaseModel):
  text: str
  score: float | None = None
  source_id: str | None = None
  source_type: str | None = None
  doc_hash: str | None = None
  metadata: dict[str, Any] = Field(default_factory=dict)

class RetrievalService(ABC):
  @abstractmethod
  def retrieve(self, request: RetrievalRequest) -> list[RetrievedChunk]:
    raise NotImplementedError("Subclasses must implement this method")

class QdrantRetrievalService(RetrievalService):
  def __init__(
    self, 
    collection_name: str,
    qdrant_url: str = "http://localhost:6333",
    api_key: str = "",
    embedding_model: str = "text-embedding-3-small",
    sparse_model: str = "Qdrant/bm25"
  ):

    self.collection_name = collection_name
    self.client = QdrantClient(url=qdrant_url, api_key=api_key)
    self.embedding_model = OpenAIEmbedding(model=embedding_model)

    # 1) Qdrant vector store
    self.vector_store = QdrantVectorStore(
      client=self.client,
      collection_name=self.collection_name,
      enable_hybrid=True,
      fastembed_sparse_model=sparse_model,
      batch_size=20
    )

    # 2) Vector store index
    self.index = VectorStoreIndex.from_vector_store(
      vector_store=self.vector_store,
      embed_model=self.embedding_model,
    )
  
  @staticmethod
  def _to_llama_filters(raw_filters: dict[str, Any] | None) -> MetadataFilters | None:
    if not raw_filters:
        return None
    return MetadataFilters(
        filters=[
            MetadataFilter(key=k, operator=FilterOperator.EQ, value=v)
            for k, v in raw_filters.items()
        ]
    )

  def retrieve(self, request: RetrievalRequest) -> list[RetrievedChunk]:
    llama_filters = self._to_llama_filters(request.filters)

    retriever = self.index.as_retriever(
      vector_store_query_mode="hybrid",
      similarity_top_k=request.top_k,
      sparse_top_k=request.sparse_top_k,
      alpha=request.alpha,
      filters=llama_filters
    )
    results = retriever.retrieve(request.query)

    chunks: list[RetrievedChunk] = []
    for result in results:
      metadata = result.node.metadata or {}
      chunks.append(
          RetrievedChunk(
          text=result.node.get_content(),
          score=result.score,
          source_id=metadata.get("source_id"),
          source_type=metadata.get("source_type"),
          doc_hash=metadata.get("doc_hash"),
          metadata=metadata
        )
      )
    return chunks

def main() -> None:
  # Local smoke test for retrieval
  from app.rag.core.config import QDRANT_COLLECTION

  req = RetrievalRequest(
    query="What were NVIDIA gross margins in Q3 FY25?",
    top_k=5,
    sparse_top_k=20,
    alpha=0.5,
    filters={"source_name": "nvidia"}
  )

  retrieval_service = QdrantRetrievalService(collection_name=QDRANT_COLLECTION)
  results = retrieval_service.retrieve(req)

  print(f"Retrieved {len(results)} chunks")
  for index, chunk in enumerate(results, start=1):
    print(f"\nChunk {index}:")
    print(f"Score: {chunk.score}")
    print(f"Source ID: {chunk.source_id}")
    print(f"Source Type: {chunk.source_type}")
    print(f"Doc Hash: {chunk.doc_hash}")
    print(f"Metadata: {chunk.metadata}")
    print(f"Text: {chunk.text}")

if __name__ == "__main__":
  main()