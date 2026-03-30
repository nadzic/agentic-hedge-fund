import asyncio

from fastapi import APIRouter, HTTPException
from starlette.concurrency import run_in_threadpool

from app.api.schemas.signal import SignalRequest, SignalResponse
from app.services.signal_service import run_signal_sync

router = APIRouter()
ANALYZE_TIMEOUT_SECONDS = 45

@router.post("/analyze", response_model=SignalResponse)
async def analyze(request: SignalRequest) -> SignalResponse:
  try:
    result = await asyncio.wait_for(
      run_in_threadpool(run_signal_sync, request),
      timeout=ANALYZE_TIMEOUT_SECONDS,
    )
  except TimeoutError as e:
    raise HTTPException(
      status_code=504,
      detail=f"Graph execution timed out after {ANALYZE_TIMEOUT_SECONDS}s",
    ) from e
  except Exception as e:
    raise HTTPException(status_code=500, detail=f"Graph execution failed: {e}") from e
  return result

