from __future__ import annotations

import hashlib
import hmac
import os
import threading
import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Literal

import httpx
from fastapi import Request, Response

IdentityType = Literal["anon", "user"]

GUEST_COOKIE_NAME = "veritake_guest_id"
GUEST_COOKIE_MAX_AGE_SECONDS = 60 * 60 * 24 * 365
DEFAULT_COOKIE_SECRET = "dev-change-me"
_FALLBACK_COUNTER_LOCK = threading.Lock()
_FALLBACK_DAILY_COUNTER: dict[tuple[IdentityType, str, str], int] = {}


@dataclass(frozen=True)
class RateLimitDecision:
  allowed: bool
  identity_type: IdentityType
  limit: int
  remaining: int
  reset_at: str | None
  upgrade_required: bool
  guest_cookie_value: str | None


def _get_env(*names: str) -> str:
  for name in names:
    value = os.getenv(name)
    if value:
      return value
  return ""


def _cookie_secret() -> str:
  return _get_env("RATE_LIMIT_COOKIE_SECRET", "COOKIE_SIGNING_SECRET") or DEFAULT_COOKIE_SECRET


def _sign_guest_id(guest_id: str) -> str:
  secret = _cookie_secret().encode("utf-8")
  digest = hmac.new(secret, guest_id.encode("utf-8"), hashlib.sha256).hexdigest()[:24]
  return f"{guest_id}.{digest}"


def _verify_signed_guest_id(value: str | None) -> str | None:
  if not value:
    return None
  guest_id, dot, provided_sig = value.partition(".")
  if not dot or not guest_id or not provided_sig:
    return None
  expected = _sign_guest_id(guest_id).partition(".")[2]
  if hmac.compare_digest(provided_sig, expected):
    return guest_id
  return None


def _new_guest_cookie_value() -> tuple[str, str]:
  guest_id = uuid.uuid4().hex
  return guest_id, _sign_guest_id(guest_id)


def _client_ip(request: Request) -> str:
  forwarded_for = request.headers.get("x-forwarded-for", "")
  if forwarded_for:
    return forwarded_for.split(",")[0].strip()
  return request.client.host if request.client else "unknown"


def _anon_fallback_identity(request: Request) -> str:
  ip = _client_ip(request)
  user_agent = request.headers.get("user-agent", "unknown")
  raw = f"{ip}:{user_agent}"
  return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _extract_bearer_token(request: Request) -> str | None:
  auth_header = request.headers.get("authorization")
  if not auth_header:
    return None
  prefix = "bearer "
  if not auth_header.lower().startswith(prefix):
    return None
  token = auth_header[len(prefix):].strip()
  return token or None


def _resolve_authenticated_user_id(access_token: str) -> str | None:
  supabase_url = _get_env("SUPABASE_URL", "NEXT_PUBLIC_SUPABASE_URL")
  # Prefer anon key for user lookup, but allow service-role fallback on server runtimes
  # where anon env can be missing.
  supabase_api_key = _get_env(
    "SUPABASE_ANON_KEY",
    "NEXT_PUBLIC_SUPABASE_ANON_KEY",
    "SUPABASE_SERVICE_ROLE_KEY",
  )
  if not supabase_url or not supabase_api_key:
    return None

  try:
    response = httpx.get(
      f"{supabase_url.rstrip('/')}/auth/v1/user",
      headers={
        "apikey": supabase_api_key,
        "Authorization": f"Bearer {access_token}",
      },
      timeout=5.0,
    )
    if response.status_code != 200:
      return None
    payload = response.json()
    user_id = payload.get("id")
    if isinstance(user_id, str) and user_id.strip():
      return user_id
  except Exception:
    return None
  return None


def _resolve_identity(request: Request) -> tuple[IdentityType, str, str | None]:
  access_token = _extract_bearer_token(request)
  if access_token:
    user_id = _resolve_authenticated_user_id(access_token)
    if user_id:
      return "user", user_id, None

  signed_guest_id = request.cookies.get(GUEST_COOKIE_NAME)
  verified_guest_id = _verify_signed_guest_id(signed_guest_id)
  if verified_guest_id:
    return "anon", verified_guest_id, None

  guest_id, signed_value = _new_guest_cookie_value()
  return "anon", guest_id, signed_value


def _daily_limit_for(identity_type: IdentityType) -> int:
  if identity_type == "user":
    return int(os.getenv("RATE_LIMIT_USER_DAILY", "5"))
  return int(os.getenv("RATE_LIMIT_ANON_DAILY", "2"))


def _safe_int(value: object, fallback: int) -> int:
  if isinstance(value, bool):
    return int(value)
  if isinstance(value, int):
    return value
  if isinstance(value, float):
    return int(value)
  if isinstance(value, str):
    try:
      return int(value)
    except ValueError:
      return fallback
  return fallback


def _fallback_daily_decision(
  identity_type: IdentityType,
  identity_key: str,
  limit: int,
) -> RateLimitDecision:
  utc_day = datetime.utcnow().date().isoformat()
  counter_key = (identity_type, identity_key, utc_day)

  with _FALLBACK_COUNTER_LOCK:
    current_count = _FALLBACK_DAILY_COUNTER.get(counter_key, 0)
    next_count = current_count + 1
    _FALLBACK_DAILY_COUNTER[counter_key] = next_count

  allowed = next_count <= limit
  remaining = max(limit - next_count, 0)
  return RateLimitDecision(
    allowed=allowed,
    identity_type=identity_type,
    limit=limit,
    remaining=remaining,
    reset_at=None,
    upgrade_required=(identity_type == "anon"),
    guest_cookie_value=None,
  )


def _call_supabase_usage_rpc(
  identity_type: IdentityType,
  identity_key: str,
  limit: int,
) -> dict[str, object]:
  supabase_url = _get_env("SUPABASE_URL", "NEXT_PUBLIC_SUPABASE_URL")
  supabase_key = _get_env(
    "SUPABASE_SERVICE_ROLE_KEY",
    "SUPABASE_ANON_KEY",
    "NEXT_PUBLIC_SUPABASE_ANON_KEY",
  )
  if not supabase_url or not supabase_key:
    # Force deterministic local fallback limiter when Supabase env is missing.
    raise RuntimeError("Missing Supabase configuration for usage RPC")

  response = httpx.post(
    f"{supabase_url.rstrip('/')}/rest/v1/rpc/check_and_increment_usage_limit",
    headers={
      "apikey": supabase_key,
      "Authorization": f"Bearer {supabase_key}",
      "Content-Type": "application/json",
    },
    json={
      "p_identity_type": identity_type,
      "p_identity_key": f"{identity_type}:{identity_key}",
      "p_daily_limit": limit,
    },
    timeout=5.0,
  )
  response.raise_for_status()
  payload = response.json()
  if isinstance(payload, list):
    if not payload:
      raise ValueError("Supabase RPC returned empty list")
    row = payload[0]
  else:
    row = payload
  if not isinstance(row, dict):
    raise ValueError("Supabase RPC returned invalid payload")
  return row


def check_analyze_rate_limit(request: Request, response: Response) -> RateLimitDecision:
  identity_type, identity_key, guest_cookie_value = _resolve_identity(request)
  limit = _daily_limit_for(identity_type)

  try:
    rpc_payload = _call_supabase_usage_rpc(identity_type, identity_key, limit)
    allowed = bool(rpc_payload.get("allowed", True))
    remaining = _safe_int(rpc_payload.get("remaining"), max(limit - 1, 0))
    reset_at_raw = rpc_payload.get("reset_at")
    reset_at = None
    if isinstance(reset_at_raw, str):
      reset_at = reset_at_raw
    elif isinstance(reset_at_raw, datetime):
      reset_at = reset_at_raw.isoformat()
    return RateLimitDecision(
      allowed=allowed,
      identity_type=identity_type,
      limit=limit,
      remaining=max(remaining, 0),
      reset_at=reset_at,
      upgrade_required=(identity_type == "anon"),
      guest_cookie_value=guest_cookie_value,
    )
  except Exception:
    fallback_decision = _fallback_daily_decision(identity_type, identity_key, limit)
    return RateLimitDecision(
      allowed=fallback_decision.allowed,
      identity_type=fallback_decision.identity_type,
      limit=fallback_decision.limit,
      remaining=fallback_decision.remaining,
      reset_at=fallback_decision.reset_at,
      upgrade_required=fallback_decision.upgrade_required,
      guest_cookie_value=guest_cookie_value,
    )
