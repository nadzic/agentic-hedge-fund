from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ResearchRequest(BaseModel):
  query: str = Field(..., min_length=1, description="User research query (e.g. NVDA)")


class Brief(BaseModel):
  executive_summary: str | None = None
  what_changed: list[str] = Field(default_factory=list)
  what_matters_most_now: list[str] = Field(default_factory=list)
  bull_points: list[str] = Field(default_factory=list)
  bear_points: list[str] = Field(default_factory=list)
  what_to_watch_next: list[str] = Field(default_factory=list)


class EvidenceQualitySummary(BaseModel):
  strong: int = 0
  medium: int = 0
  weak: int = 0


class ResearchResponse(BaseModel):
  company: str | None = None
  ticker: str | None = None
  brief: Brief
  evidence_quality_summary: EvidenceQualitySummary

  sources: list[dict[str, Any]] = Field(default_factory=list)
  selected_evidence: list[dict[str, Any]] = Field(default_factory=list)
  discarded_evidence_count: int = 0
  disclaimer: str = "This is not investment advice."

  warning: str | None = None
  error: str | None = None

