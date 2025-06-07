"""
peer_chat A2A helper.

* If the OpenAI Agents SDK is available, the message-sender is registered
  as a FunctionTool under `peer_chat_tool`.
* Regardless of the SDK, call `peer_chat()` from normal Python and tests.
"""

from __future__ import annotations

import time
import uuid
from typing import Literal

import requests

A2A_VERSION = "0.1.0"

# ────────────────────────────────────────────────────────────────────
# Core implementation (never wrapped)
# ────────────────────────────────────────────────────────────────────
def _peer_chat_impl(
    target_url: str,
    sender_id: str,
    content: str,
    *,
    msg_type: Literal["user", "assistant"] = "user",
    timeout: float = 10.0,
) -> str:
    """POST a Google A2A Task envelope to `{target_url}/tasks`."""
    task_id = str(uuid.uuid4())
    payload = {
        "a2a_version": A2A_VERSION,
        "id": task_id,
        "state": "submitted",
        "messages": [
            {"role": msg_type, "content": content, "timestamp": int(time.time())}
        ],
        "from": sender_id,
    }
    resp = requests.post(f"{target_url.rstrip('/')}/tasks", json=payload, timeout=timeout)
    resp.raise_for_status()
    return f"peer_chat sent (task_id={task_id})"

# ────────────────────────────────────────────────────────────────────
# Optional SDK registration
# ────────────────────────────────────────────────────────────────────
try:
    from agents import function_tool            # OpenAI Agents SDK
    peer_chat_tool = function_tool(_peer_chat_impl)   # FunctionTool obj
    # expose the underlying Python callable for normal use
    peer_chat: callable = getattr(peer_chat_tool, "python_fn", _peer_chat_impl)
except ImportError:
    # SDK not installed → fall back to plain function
    peer_chat_tool = _peer_chat_impl            # placeholder, still callable
    peer_chat = _peer_chat_impl                 # alias used by code/tests
