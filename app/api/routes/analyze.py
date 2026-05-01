import asyncio
import json
from typing import Any

from fastapi import APIRouter, HTTPException, Request, Response
from fastapi.responses import StreamingResponse
from starlette.concurrency import run_in_threadpool

from app.api.schemas.signal import SignalRequest, SignalResponse
from app.services.rate_limit_service import (
  GUEST_COOKIE_MAX_AGE_SECONDS,
  GUEST_COOKIE_NAME,
  check_analyze_rate_limit,
)
from app.services.signal_service import run_signal_stream_sync, run_signal_sync

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


def _rate_limit_exception(decision: Any) -> HTTPException:
  return HTTPException(
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


def _sse_event(event: str, payload: dict[str, Any]) -> str:
  return f"event: {event}\ndata: {json.dumps(payload)}\n\n"


@router.post("/analyze/stream")
async def analyze_stream(
  payload: SignalRequest, request: Request, response: Response
) -> StreamingResponse:
  decision = await run_in_threadpool(check_analyze_rate_limit, request, response)
  if not decision.allowed:
    raise _rate_limit_exception(decision)

  def event_generator():
    try:
      for event in run_signal_stream_sync(payload):
        event_type = event.get("type", "update")
        event_payload = event.get("payload", {})
        if not isinstance(event_payload, dict):
          event_payload = {"value": event_payload}
        yield _sse_event(str(event_type), event_payload)
    except Exception as e:
      yield _sse_event("error", {"message": f"Graph execution failed: {e}"})

  stream_response = StreamingResponse(
    event_generator(),
    media_type="text/event-stream",
    headers={
      "Cache-Control": "no-cache",
      "Connection": "keep-alive",
      "X-Accel-Buffering": "no",
    },
  )
  if decision.guest_cookie_value:
    stream_response.set_cookie(
      key=GUEST_COOKIE_NAME,
      value=decision.guest_cookie_value,
      max_age=GUEST_COOKIE_MAX_AGE_SECONDS,
      httponly=True,
      samesite="lax",
    )
  return stream_response

