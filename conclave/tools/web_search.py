"""Wrapper for the built‑in web.search tool in the OpenAI Responses API.

This file registers a *function tool* so the LLM can call `web_search()` just
like any custom function.  At runtime the SDK recognises the name and routes
it to OpenAI's hosted web search backend; we simply declare the schema.
"""

from __future__ import annotations
from typing import Annotated

try:
    from openai_agents import function_tool
except ModuleNotFoundError:  # pragma: no cover – offline CI / tests
    def function_tool(fn=None, **_):  # type: ignore
        return fn if fn else (lambda f: f)


@function_tool(name="web.search", description="Search the live web and return short snippets.")
def web_search(query: Annotated[str, "The search query string."]) -> str:
    """Declarative stub; OpenAI executes it server‑side."""
    # The body is never run when the Responses API handles the call.
    # In offline tests we simply return an empty string.
    return "[web.search]: tool called in offline mode"
