from app.api.schemas.rag import (
  RagIngestIndexRequest,
  RagIngestIndexResponse,
  RagQueryRequest,
  RagQueryResponse,
)
from app.rag.pipelines import (
  IngestIndexRequest,
  QueryPipelineRequest,
  get_ingest_index_pipeline,
  get_query_pipeline,
)
from app.observability.tracing import observe


@observe(name="api.rag.ingest_index")
def run_rag_ingest_index_sync(request: RagIngestIndexRequest) -> RagIngestIndexResponse:
  pipeline = get_ingest_index_pipeline()
  result = pipeline.run(
    IngestIndexRequest(
      pdf_paths=request.pdf_paths,
      pdf_recursive=request.pdf_recursive,
      urls=request.urls,
      min_chars=request.min_chars,
      snapshot_path=request.snapshot_path,
      collection_name=request.collection_name,
    )
  )
  return RagIngestIndexResponse(
    input_count=result.input_count,
    transformed_count=result.transformed_count,
    dropped_empty_or_short=result.dropped_empty_or_short,
    dropped_challenge_or_junk=result.dropped_challenge_or_junk,
    indexed_count=result.indexed_count,
    snapshot_path=result.snapshot_path,
    collection_name=result.collection_name,
  )

@observe(name="api.rag.query")
def run_rag_query_sync(request: RagQueryRequest) -> RagQueryResponse:
  pipeline = get_query_pipeline()
  result = pipeline.run(
    QueryPipelineRequest(
      query=request.query,
      symbol=request.symbol,
      horizon=request.horizon,
      top_k=request.top_k,
      sparse_top_k=request.sparse_top_k,
      alpha=request.alpha,
      max_context_chunks=request.max_context_chunks,
    )
  )
  return RagQueryResponse(
    answer=result.answer,
    confidence=result.confidence,
    citations=result.citations,
    reasoning=result.reasoning,
  )
