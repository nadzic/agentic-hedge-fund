from fastapi import APIRouter, HTTPException
from starlette.concurrency import run_in_threadpool

from app.api.schemas.signal import SignalRequest, SignalResponse
from app.services.signal_service import run_signal_sync

router = APIRouter()

@router.post("/analyze", response_model=SignalResponse)
async def analyze(request: SignalRequest) -> SignalResponse:
  try:
    result = await run_in_threadpool(run_signal_sync, request)
  except Exception as e:
    raise HTTPException(status_code=500, detail=f"Graph execution failed: {e}") from e
  return result

