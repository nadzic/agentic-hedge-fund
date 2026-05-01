from __future__ import annotations

import asyncio
import os
from time import perf_counter
from typing import Literal

from fastapi import APIRouter, Response, status
from langchain_core.messages import HumanMessage
from pydantic import BaseModel
from qdrant_client import QdrantClient

from app.agents.services.llm_service import get_llm

router = APIRouter()

CheckStatus = Literal["ok", "error"]


class DependencyCheck(BaseModel):
  status: CheckStatus
  latency_ms: float | None = None
  detail: str | None = None


class HealthResponse(BaseModel):
  status: Literal["ok", "degraded"]
  checks: dict[str, DependencyCheck]


def _elapsed_ms(start_time: float) -> float:
  return round((perf_counter() - start_time) * 1000, 2)


async def _check_qdrant() -> DependencyCheck:
  start_time = perf_counter()
  qdrant_url = os.getenv("QDRANT_URL", "http://localhost:6333")
  api_key = os.getenv("QDRANT_API_KEY", "")

  try:
    client = QdrantClient(url=qdrant_url, api_key=api_key, timeout=5)
    await asyncio.to_thread(client.get_collections)
    return DependencyCheck(status="ok", latency_ms=_elapsed_ms(start_time))
  except Exception as exc:
    return DependencyCheck(
      status="error",
      latency_ms=_elapsed_ms(start_time),
      detail=f"Qdrant unavailable: {exc}",
    )


def _llm_probe() -> None:
  llm = get_llm()
  _ = llm.invoke([HumanMessage(content="Reply with exactly: ok")])


async def _check_llm() -> DependencyCheck:
  start_time = perf_counter()
  try:
    await asyncio.wait_for(asyncio.to_thread(_llm_probe), timeout=12)
    return DependencyCheck(status="ok", latency_ms=_elapsed_ms(start_time))
  except Exception as exc:
    return DependencyCheck(
      status="error",
      latency_ms=_elapsed_ms(start_time),
      detail=f"LLM unavailable: {exc}",
    )


@router.get("/health", response_model=HealthResponse)
async def health_check(response: Response) -> HealthResponse:
  qdrant_check, llm_check = await asyncio.gather(
    _check_qdrant(),
    _check_llm(),
  )

  checks = {
    "qdrant": qdrant_check,
    "llm": llm_check,
  }
  is_healthy = all(check.status == "ok" for check in checks.values())
  if not is_healthy:
    response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

  return HealthResponse(status="ok" if is_healthy else "degraded", checks=checks)