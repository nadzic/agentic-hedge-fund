from __future__ import annotations

import asyncio
from typing import Any, Protocol, cast

from fastapi import APIRouter, HTTPException
from starlette.concurrency import run_in_threadpool

from app.agents.graph.state_models.nodes_research_state import NodesResearchState
from app.agents.graph.workflow import build_graph
from app.api.schemas.research import (
  Brief,
  EvidenceQualitySummary,
  ResearchRequest,
  ResearchResponse,
)


router = APIRouter()
RESEARCH_TIMEOUT_SECONDS = 60


class _GraphRunner(Protocol):
  def invoke(self, input: NodesResearchState, /) -> NodesResearchState: ...


_GRAPH = cast(_GraphRunner, cast(object, build_graph()))


def _quality_bucket(source_rank: Any) -> str:
  try:
    sr = int(source_rank)
  except Exception:
    return "weak"
  if sr <= 3:
    return "strong"
  if sr <= 10:
    return "medium"
  return "weak"


def _evidence_quality(selected: list[dict[str, Any]]) -> EvidenceQualitySummary:
  strong = 0
  medium = 0
  weak = 0
  for ev in selected:
    bucket = _quality_bucket(ev.get("source_rank"))
    if bucket == "strong":
      strong += 1
    elif bucket == "medium":
      medium += 1
    else:
      weak += 1
  return EvidenceQualitySummary(strong=strong, medium=medium, weak=weak)


def _as_str_list(value: Any) -> list[str]:
  if not isinstance(value, list):
    return []
  out: list[str] = []
  for item in value:
    text = str(item).strip()
    if text:
      out.append(text)
  return out


@router.post("/research", response_model=ResearchResponse)
async def research(payload: ResearchRequest) -> ResearchResponse:
  state: NodesResearchState = {
    "query": payload.query,
    "input_query": payload.query,
    "warning": None,
    "error": None,
  }

  try:
    result = await asyncio.wait_for(
      run_in_threadpool(_GRAPH.invoke, state),
      timeout=RESEARCH_TIMEOUT_SECONDS,
    )
  except TimeoutError as e:
    raise HTTPException(
      status_code=504,
      detail=f"Research execution timed out after {RESEARCH_TIMEOUT_SECONDS}s",
    ) from e
  except Exception as e:
    raise HTTPException(status_code=500, detail=f"Research execution failed: {e}") from e

  company_name = cast(str | None, result.get("company_name"))
  symbol = cast(str | None, result.get("symbol"))

  ranked_sources = result.get("ranked_sources")
  sources: list[dict[str, Any]] = ranked_sources if isinstance(ranked_sources, list) else []

  selected = result.get("selected_evidences")
  selected_evidence: list[dict[str, Any]] = selected if isinstance(selected, list) else []

  classified = result.get("classified_evidences")
  classified_evidence: list[dict[str, Any]] = classified if isinstance(classified, list) else []

  discarded_evidence_count = max(0, len(classified_evidence) - len(selected_evidence))

  summary = cast(str | None, result.get("research_summary"))
  research_brief = result.get("research_brief")
  brief_data = research_brief if isinstance(research_brief, dict) else {}

  brief = Brief(
    executive_summary=cast(str | None, brief_data.get("executive_summary")) or summary,
    what_changed=_as_str_list(brief_data.get("what_changed")),
    what_matters_most_now=_as_str_list(brief_data.get("what_matters_most_now")),
    bull_points=_as_str_list(brief_data.get("bull_points")),
    bear_points=_as_str_list(brief_data.get("bear_points")),
    what_to_watch_next=_as_str_list(brief_data.get("what_to_watch_next")),
  )
  disclaimer = str(brief_data.get("disclaimer") or "This is not investment advice.").strip()

  response = ResearchResponse(
    company=company_name,
    ticker=symbol,
    brief=brief,
    evidence_quality_summary=_evidence_quality(selected_evidence),
    sources=sources,
    selected_evidence=selected_evidence,
    discarded_evidence_count=discarded_evidence_count,
    disclaimer=disclaimer or "This is not investment advice.",
    warning=cast(str | None, result.get("warning")),
    error=cast(str | None, result.get("error")),
  )
  return response

