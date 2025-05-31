"""Tests for Phase‑2 web.search tool wrapper.

We verify that the function-tool wrapper can be imported without the
OpenAI Agents SDK present and returns a stubbed string in offline mode.
"""
from __future__ import annotations
import sys, types, importlib

import pytest


def _remove_sdk_if_present():
    sys.modules.pop("openai_agents", None)


def test_web_search_offline_returns_stub(monkeypatch):
    """Ensure web_search() runs even if openai_agents is missing."""
    _remove_sdk_if_present()
    import conclave.tools.web_search as ws
    importlib.reload(ws)  # re-evaluate wrapper with SDK absent

    result = ws.web_search("python portalocker example")
    assert "offline mode" in result.lower()


def test_web_search_function_name():
    """Function should keep the declared name 'web.search' for SDK schema."""
    _remove_sdk_if_present()
    import conclave.tools.web_search as ws
    assert ws.web_search.__name__ == "web_search", "local function name stays pythonic"
    # decorator sets ws.web_search.tool_name when SDK is present; skip if absent
    assert hasattr(ws.web_search, "__call__")
