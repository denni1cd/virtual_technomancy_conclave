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

# Load .env (python-dotenv searches current dir upward until it finds one)
load_dotenv()   # default search; does nothing if file isn't present :contentReference[oaicite:0]{index=0}

def print_trace_url(run: Any) -> None:
    """
    Accept an AgentRun / Runner result and print its `.trace_url`
    if tracing is active.  If the key is absent, log a short notice.
    """
    if not os.getenv("OPENAI_API_KEY"):
        print("[trace] OPENAI_API_KEY not set (is it in your .env?)")  # noqa: T201
        return

    url = getattr(run, "trace_url", None)
    if url:                                     # normal success path
        print(f"[trace] View trace → {url}")    # noqa: T201
    else:                                       # tracing was disabled when run executed
        print("[trace] run.trace_url missing")  # noqa: T201
