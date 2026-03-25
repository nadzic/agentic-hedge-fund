from app.rag.pipelines import (
  IngestIndexRequest,
  IngestIndexResult,
  QueryPipelineRequest,
  QueryPipelineResult,
  get_ingest_index_pipeline,
  get_query_pipeline,
)


def run_rag_ingest_index_sync(request: IngestIndexRequest) -> IngestIndexResult:
  pipeline = get_ingest_index_pipeline()
  return pipeline.run(request)


def run_rag_query_sync(request: QueryPipelineRequest) -> QueryPipelineResult:
  pipeline = get_query_pipeline()
  return pipeline.run(request)
