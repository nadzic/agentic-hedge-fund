import asyncio

from fastapi import APIRouter, HTTPException, Request, Response
from starlette.concurrency import run_in_threadpool

from app.api.schemas.signal import SignalRequest, SignalResponse
from app.services.rate_limit_service import (
  GUEST_COOKIE_MAX_AGE_SECONDS,
  GUEST_COOKIE_NAME,
  check_analyze_rate_limit,
)
from app.services.signal_service import run_signal_sync

router = APIRouter()
ANALYZE_TIMEOUT_SECONDS = 45

@router.post("/analyze", response_model=SignalResponse)
async def analyze(payload: SignalRequest, request: Request, response: Response) -> SignalResponse:
  decision = await run_in_threadpool(check_analyze_rate_limit, request, response)
  if decision.guest_cookie_value:
    response.set_cookie(
      key=GUEST_COOKIE_NAME,
      value=decision.guest_cookie_value,
      max_age=GUEST_COOKIE_MAX_AGE_SECONDS,
      httponly=True,
      samesite="lax",
    )
  if not decision.allowed:
    raise HTTPException(
      status_code=429,
      detail={
        "code": "rate_limit_exceeded",
        "message": "Free query limit reached.",
        "identity_type": decision.identity_type,
        "limit": decision.limit,
        "remaining": decision.remaining,
        "reset_at": decision.reset_at,
        "upgrade_required": decision.upgrade_required,
      },
    )
  try:
    result = await asyncio.wait_for(
      run_in_threadpool(run_signal_sync, payload),
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

