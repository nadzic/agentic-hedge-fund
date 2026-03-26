from fastapi import APIRouter, HTTPException
from starlette.concurrency import run_in_threadpool

from app.api.schemas.rag import RagIngestIndexRequest, RagIngestIndexResponse
from app.services.rag_service import run_rag_ingest_index_sync

router = APIRouter()

@router.post("/ingest-index", response_model=RagIngestIndexResponse)
async def rag_ingest(request: RagIngestIndexRequest) -> RagIngestIndexResponse:
  try: 
    result = await run_in_threadpool(run_rag_ingest_index_sync, request)
    return result
  except Exception as e:
    raise HTTPException(status_code=500, detail=f"RAG ingestion failed: {e}") from e


