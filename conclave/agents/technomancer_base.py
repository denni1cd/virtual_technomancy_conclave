from __future__ import annotations

from datetime import datetime, UTC
from typing import Any, Dict

# A stub import; the real ledger will arrive in T4.
try:
    from conclave.services.cost_ledger import log_usage  # pragma: no cover
    from conclave.services.cost_ledger import log_usage, CostCapExceeded

except ModuleNotFoundError:  # during early sprints
    def log_usage(*_, **__):  # type: ignore
        """No-op until cost_ledger.py is implemented."""
        return None


class TechnomancerBase:
    """
    Shared plumbing every runtime Conclave*Technomancer class inherits.

    Template attributes (role_prompt, rank, token_cap, …) are injected by
    AgentFactory via **attrs so the base never hard-codes role specifics.
    """

    # ------------------------------------------------------------------ #
    # Construction
    # ------------------------------------------------------------------ #
    def __init__(self, *, role_name: str, **attrs: Dict[str, Any]) -> None:
        self.role_name: str = role_name
        # copy template-level attrs produced by AgentFactory
        for key, val in attrs.items():
            setattr(self, key, val)

        # minimal runtime state
        self.created_at: datetime = datetime.now(UTC)
        self.tokens_used: int = 0

    # ------------------------------------------------------------------ #
    # Public stubs (filled in later sprints)
    # ------------------------------------------------------------------ #
    def think(self, *_, **__) -> str:
        """
        Placeholder reasoning loop.

        Returns a fixed string so early tests can assert the method exists
        without requiring an LLM call.
        """
        return "TODO-think"

    def call_llm(self, *_, **__) -> str:  # noqa: D401
        """
        Will wrap an OpenAI Agents-SDK call in T3/T6.

        We raise for now to ensure tests remind us to implement it.
        """
        raise NotImplementedError("call_llm stub — implemented in Phase 3")

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #
    # ------------------------------------------------------------------ #
    # Cost logging helper ---------------------------------------------- #
    def _log_cost(self, *, prompt_tokens: int, completion_tokens: int) -> None:
        """
        Send a single usage record to the shared ledger.

        Computes total and passes the correct role name so the new
        hard-cap logic works.
        """
        from conclave.services.cost_ledger import log_usage

        total = prompt_tokens + completion_tokens
        log_usage(
            agent=self.role_name,
            role_name=self.__class__.__name__.replace("Conclave", ""),
            prompt=prompt_tokens,
            completion=completion_tokens,
            total=total,
        )

    # ------------------------------------------------------------------ #
    # Tracing helper ---------------------------------------------------- #
    def _finish_run(self, run) -> None:
        """
        Call after each Runner.run(); logs tokens & prints trace URL.
        """
        usage = getattr(run, "usage", None)
        if usage:
            prompt = getattr(usage, "prompt_tokens", 0)
            completion = getattr(usage, "completion_tokens", 0)
            self._log_cost(
                prompt_tokens=prompt,
                completion_tokens=completion,
            )

        # surface trace link (no-op if key missing)
        from conclave.services.trace_utils import print_trace_url
        print_trace_url(run)
