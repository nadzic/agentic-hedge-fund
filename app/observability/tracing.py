from __future__ import annotations

import os
from dotenv import load_dotenv
from langfuse import observe

_ = load_dotenv()

def tracing_enabled() -> bool:
  return bool(os.getenv("LANGFUSE_PUBLIC_KEY") and os.getenv("LANGFUSE_SECRET_KEY"))

__all__ = ["observe", "tracing_enabled"]