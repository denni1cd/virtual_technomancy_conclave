"""
Trace helper that:
1. Uses python-dotenv to slurp variables from a .env file (wherever
   python-dotenv finds it by walking up the directory tree).
2. Looks up OPENAI_API_KEY with os.getenv() to decide whether tracing
   is enabled, then prints the SDK's trace URL if present.
"""

from __future__ import annotations
import os
from typing import Any

from dotenv import load_dotenv  # pip install python-dotenv

def print_trace_url(run: Any) -> None:
    """
    Accept an AgentRun / Runner result and print its `.trace_url`
    if tracing is active.  If the key is absent, log a short notice.
    """
    # Try to load from .env file first
    load_dotenv()
    
    # Check for API key in environment
    key = os.getenv("OPENAI_API_KEY")
    if not key or key.strip() == "":
        print("[trace] OPENAI_API_KEY not set (is it in your .env?)")  # noqa: T201
        return

    # Only try to access trace_url if we have an API key
    url = getattr(run, "trace_url", None)
    if url:
        print(f"[trace] View trace → {url}")    # noqa: T201
    else:
        print("[trace] run.trace_url missing")  # noqa: T201
