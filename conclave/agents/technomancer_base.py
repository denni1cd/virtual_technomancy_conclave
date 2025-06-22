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
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, cast
from uuid import uuid4

from openai import AsyncOpenAI
from pydantic import BaseModel, Field

from conclave.services.cost_ledger import log_and_check, cost_guard, _TOKEN_PRICE, _AGENT_ID_VAR
from conclave.services.context import set_role, get_role, create_task_with_context
from conclave.services.tracing import get_tracer

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
        self.created_at: datetime = datetime.now()
        self.agent_id = f"{role_name}_{uuid4().hex[:8]}"
        _AGENT_ID_VAR.set(self.agent_id)
        set_role(role_name)  # Set role in context
        self.cfg = TechnomancerConfig(role_name=role_name, **kwargs)

    # ──────────────────────────────────────────────────────────────
    # Low-level LLM call (Responses API) — guarded for cost caps.
    # ──────────────────────────────────────────────────────────────
    @cost_guard(role_name="Technomancer", est_tokens=800, est_cost=0.10)
    async def _call_llm(self, input_text: str, **kw) -> tuple[str, int, float]:
        """
        Send *input_text* to the agent and return the assistant's reply string.
        kw → forwarded to `responses.create()` (temperature, max_tokens, etc.).
        """
        if 'history' in kw:
            del kw['history']

        # Start tracing child span for LLM call
        tracer = get_tracer()
        with tracer.child_span(
            name="llm_call",
            kind="LLM",
            metadata={
                "model": self.cfg.model,
                "role": self.cfg.role_name,
                "agent_id": self.agent_id,
                "input_length": len(input_text)
            }
        ):
            rsp = await _client.responses.create(
                model=self.cfg.model,
                input=input_text,
                instructions=self.cfg.instructions,
                tools=self.cfg.tools,
                **kw,
            )

            usage = rsp.usage.model_dump()
            prompt_tokens = usage.get('input_tokens', 0)
            completion_tokens = usage.get('output_tokens', 0)
            
            total_tokens = prompt_tokens + completion_tokens
            cost = total_tokens * _TOKEN_PRICE

            # Add tracing event for LLM response
            tracer.add_event(
                "llm_response",
                {
                    "model": self.cfg.model,
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens,
                    "total_tokens": total_tokens,
                    "response_length": len(rsp.output_text)
                },
                cost_usd=cost,
                tokens=total_tokens
            )

            return rsp.output_text, total_tokens, cost

    # ──────────────────────────────────────────────────────────────
    # Public helper every subclass calls
    # ──────────────────────────────────────────────────────────────
    async def think(self, prompt: str, **kw) -> str:
        """
        High-level helper: send *prompt* to the LLM and return the answer.
        Additional kwargs bubble down to `_call_llm()`.
        """
        # Since cost_guard is now a no-op, we need to handle the tuple return manually
        result_tuple = await self._call_llm(prompt, **kw)
        if isinstance(result_tuple, tuple) and len(result_tuple) == 3:
            result, tokens, cost = result_tuple
            # Use atomic log_and_check instead of separate log_usage call
            log_and_check(
                role_name=self.cfg.role_name,
                agent_id=self.agent_id,
                tokens=tokens,
                cost=cost,
                extra={"operation": "think"}
            )
            return str(result)
        else:
            # Fallback for unexpected return type
            return str(result_tuple)

    def _log_cost(self, prompt_tokens: int, completion_tokens: int) -> None:
        """For cost-cap test."""
        total_tokens = prompt_tokens + completion_tokens
        cost = total_tokens * _TOKEN_PRICE
        log_and_check(
            role_name=self.cfg.role_name,
            agent_id=self.agent_id,  # Using the unique agent_id
            tokens=total_tokens,
            cost=cost
        )

    # conventional __repr__ for debugging
    def __repr__(self) -> str:  # noqa: D401
        return f"<{self.cfg.role_name}_{self.agent_id} model={self.cfg.model!s}>"
