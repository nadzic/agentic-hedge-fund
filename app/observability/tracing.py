from __future__ import annotations

import os
from dotenv import load_dotenv
from langfuse import observe

_ = load_dotenv()

def tracing_enabled() -> bool:
  return bool(os.getenv("LANGFUSE_PUBLIC_KEY") and os.getenv("LANGFUSE_SECRET_KEY"))

# Spodnja vrstica določa, katere funkcije ali spremenljivke bodo izpostavljene, če nekdo uvozi ta modul z "from tracing import *".
# S tem omogočimo, da se lahko iz tega modula dostopa samo do funkcij 'observe' in 'tracing_enabled'.
__all__ = ["observe", "tracing_enabled"]