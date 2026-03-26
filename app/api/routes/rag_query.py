from fastapi import APIRouter, HTTPException
from starlette.concurrency import run_in_threadpool

from app.api.schemas.rag import RagQueryRequest, RagQueryResponse
from app.services.rag_service import run_rag_query_sync

router = APIRouter()


@router.post("/query", response_model=RagQueryResponse)
async def rag_query(request: RagQueryRequest) -> RagQueryResponse:
  try:
    result = await run_in_threadpool(run_rag_query_sync, request)
    return result
  except Exception as e:
    raise HTTPException(status_code=500, detail=f"RAG query failed: {e}") from e
