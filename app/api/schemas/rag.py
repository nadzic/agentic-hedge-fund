from pydantic import BaseModel, Field


class RagQueryRequest(BaseModel):
  query: str = Field(..., description="User question")
  symbol: str = Field(..., description="Ticker symbol, e.g. NVDA")
  horizon: str = Field("swing", description="swing | intraday | position")
  top_k: int = Field(8, ge=1, le=50)
  sparse_top_k: int = Field(20, ge=1, le=200)
  alpha: float = Field(0.5, ge=0.0, le=1.0)
  max_context_chunks: int = Field(5, ge=1, le=30)


class RagQueryResponse(BaseModel):
  answer: str
  confidence: float | None = None
  citations: list[str] = Field(default_factory=list)
  reasoning: str | None = None


class RagIngestIndexRequest(BaseModel):
  pdf_paths: list[str] = Field(default_factory=list)
  pdf_recursive: bool = False
  urls: list[str] = Field(default_factory=list)
  min_chars: int = Field(300, ge=1)
  snapshot_path: str = Field("app/rag/data/processed/processed_docs.jsonl")
  collection_name: str = Field("company_docs")


class RagIngestIndexResponse(BaseModel):
  input_count: int
  transformed_count: int
  dropped_empty_or_short: int
  dropped_challenge_or_junk: int
  indexed_count: int
  snapshot_path: str
  collection_name: str
