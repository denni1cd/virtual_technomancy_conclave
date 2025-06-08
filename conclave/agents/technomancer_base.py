"""
Technomancer base-class.

Responsibilities
----------------
• Own an OpenAI Agent (via Responses API).
• Provide `.think(prompt)` that routes through the Agent and logs
  prompt/completion token usage plus latency.
• Expose basic metadata (`role_name`, `model`, `created_at`, …).

The hard-cap decorator `@cost_guard` is a no-op stub until T-15.
"""

from __future__ import annotations

import time
import contextvars
from datetime import datetime, UTC
from pathlib import Path
from typing import Any, Dict, List
from uuid import uuid4

from openai import OpenAI, AsyncOpenAI  # SDK v1.3+
from pydantic import BaseModel, Field

from conclave.services.cost_ledger import log_usage, cost_guard, _TOKEN_PRICE

# ---------------------------------------------------------------------------
_client = AsyncOpenAI()        # picks up OPENAI_API_KEY from env
# ---------------------------------------------------------------------------


class TechnomancerConfig(BaseModel):
    """Parsed template from roles.yaml (merged at runtime)."""
    role_name: str
    model: str = Field(default="gpt-4.1")
    instructions: str = Field(default="You are a helpful Conclave Technomancer.")
    tools: List[Dict[str, Any]] = Field(default_factory=list)


class TechnomancerBase:
    """
    Every runtime agent subclasses this.

    Concrete behaviour is supplied either by HighTechnomancer /
    ApprenticeTechnomancer subclasses or via the AgentFactory's `type()`
    dynamic mixins.
    """

    cfg: TechnomancerConfig                          # set by AgentFactory

    def __init__(self, role_name: str, **kwargs) -> None:
        self.created_at: datetime = datetime.now(UTC)
        self.agent_id = f"{role_name}_{uuid4().hex[:8]}"
        contextvars.ContextVar("agent_id").set(self.agent_id)
        self.cfg = TechnomancerConfig(role_name=role_name, **kwargs)

    # ──────────────────────────────────────────────────────────────
    # Low-level LLM call (Responses API) — guarded for cost caps.
    # ──────────────────────────────────────────────────────────────
    @cost_guard
    async def _call_llm(self, input_text: str, **kw) -> str:
        """
        Send *input_text* to the agent and return the assistant's reply string.
        kw → forwarded to `responses.create()` (temperature, max_tokens, etc.).
        """
        t0 = time.perf_counter()

        # Don't pass history to responses.create()
        if 'history' in kw:
            del kw['history']

        rsp = await _client.responses.create(
            model=self.cfg.model,
            input=input_text,
            instructions=self.cfg.instructions,
            tools=self.cfg.tools,
            **kw,
        )

        latency = time.perf_counter() - t0
        # New OpenAI API uses different token count keys
        usage = rsp.usage.model_dump()
        prompt_tokens = usage.get('input_tokens', 0)
        completion_tokens = usage.get('output_tokens', 0)
        
        # Calculate cost at $10 per 1M tokens
        total_tokens = prompt_tokens + completion_tokens
        cost = total_tokens * _TOKEN_PRICE

        log_usage(
            role_name=self.cfg.role_name,
            agent_id=self.agent_id,  # Using the unique agent_id
            tokens=total_tokens,
            cost=cost
        )
        return rsp.output_text

    # ──────────────────────────────────────────────────────────────
    # Public helper every subclass calls
    # ──────────────────────────────────────────────────────────────
    async def think(self, prompt: str, **kw) -> str:
        """
        High-level helper: send *prompt* to the LLM and return the answer.
        Additional kwargs bubble down to `_call_llm()`.
        """
        return await self._call_llm(prompt, **kw)

    def _log_cost(self, prompt_tokens: int, completion_tokens: int) -> None:
        """For cost-cap test."""
        total_tokens = prompt_tokens + completion_tokens
        cost = total_tokens * _TOKEN_PRICE
        log_usage(
            role_name=self.cfg.role_name,
            agent_id=self.agent_id,  # Using the unique agent_id
            tokens=total_tokens,
            cost=cost
        )

    # conventional __repr__ for debugging
    def __repr__(self) -> str:  # noqa: D401
        return f"<{self.cfg.role_name}_{self.agent_id} model={self.cfg.model!s}>"
