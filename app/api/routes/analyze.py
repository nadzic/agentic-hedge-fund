from fastapi import APIRouter
from app.api.schemas.signal import SignalResponse, SignalRequest
from starlette.concurrency import run_in_threadpool
from app.services.signal_service import run_graph_sync
from fastapi import APIRouter, HTTPException

router = APIRouter()

@router.post("/analyze", response_model=SignalResponse)
async def analyze(request: SignalRequest) -> SignalResponse:
  try:
    result = await run_in_threadpool(run_graph_sync, request)
  except Exception as e:
    raise HTTPException(status_code=500, detail=f"Graph execution failed: {e}") from e

  suggestion = result.get("suggestion")
  if suggestion is None:
    raise HTTPException(status_code=500, detail="No suggestion found")

  return SignalResponse(
    symbol=suggestion.symbol,
    signal=suggestion.signal,
    confidence=suggestion.confidence,
    reasoning=suggestion.reasoning,
    warning=result.get("warning"),
    error=result.get("error"),
  )

