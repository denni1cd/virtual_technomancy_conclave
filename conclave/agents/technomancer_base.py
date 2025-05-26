from __future__ import annotations
from typing import Any, Dict


class TechnomancerBase:
    """
    Shared plumbing for every Conclave agent.
    Role-specific attributes are injected at runtime by AgentFactory.
    """

    def __init__(self, *, role_name: str, **attrs: Dict[str, Any]):
        self.role_name = role_name
        # copy template attrs (prompt, rank, caps, rounds …)
        for k, v in attrs.items():
            setattr(self, k, v)

    # -- stubs to be filled by later sprint tasks --------------------------
    def think(self, *_, **__) -> str:  # noqa: D401, E501
        raise NotImplementedError("Sub-classes must implement `think()`")

    def call_llm(self, *_, **__) -> str:
        raise NotImplementedError
