from __future__ import annotations

from pathlib import Path

from llama_index.core.schema import Document

from app.rag.ingestion.custom_transformation import CustomTransformation
from app.rag.ingestion.pdf_ingestion import ingest_pdf
from app.rag.ingestion.url_ingestion import ingest_url
from app.rag.indexing.qdrant_indexing import QdrantIndexing
from app.rag.pipelines.types import IngestIndexRequest, IngestIndexResult


class IngestIndexPipeline:
  def run(self, request: IngestIndexRequest) -> IngestIndexResult:
    raw_docs: list[Document] = []

    for pdf_path in request.pdf_paths:
      raw_docs.extend(ingest_pdf(path=pdf_path, recursive=request.pdf_recursive))

    for url in request.urls:
      raw_docs.append(ingest_url(url=url))

    transformer = CustomTransformation(
      collection_name=request.collection_name,
      min_chars=request.min_chars,
    )
    transformed_docs, stats = transformer.transform_documents(raw_docs)

    snapshot_abs = str(Path(request.snapshot_path).resolve())
    indexer = QdrantIndexing(collection_name=request.collection_name)
    indexer.save_jsonl_snapshot(transformed_docs, snapshot_abs)
    _ = indexer.build_qdrant_index(transformed_docs)

    return IngestIndexResult(
      input_count=stats["input_count"],
      transformed_count=stats["output_count"],
      dropped_empty_or_short=stats["dropped_empty_or_short"],
      dropped_challenge_or_junk=stats["dropped_challenge_or_junk"],
      indexed_count=len(transformed_docs),
      snapshot_path=snapshot_abs,
      collection_name=request.collection_name,
    )
