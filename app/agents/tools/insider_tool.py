from __future__ import annotations

from langchain_core.tools import tool

from app.observability.tracing import observe


@tool
@observe(name="agents.tools.insider_tool")
def insider_tool(symbol: str, lookback_days: int = 30) -> None:
  pass