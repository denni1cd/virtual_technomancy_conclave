# SPDX-License-Identifier: MIT
from __future__ import annotations
from config import GUARDRAILS, ROLES
from services.memory import MemoryStore
from tools.cost_tracker import enforce_cost
import logging

class TechnomancerBase:
    """Common logic for every Technomancer rank."""

    rank: str = "technomancer"
    expertise: str | None = None
    limits = None
    tools: list[str]

    def __init__(self, name: str, tools: list, limits):
        self.name = name
        self.tools = tools
        self.limits = limits
        self.memory = MemoryStore.for_agent(name)
        logging.getLogger(__name__).info("👾 %s spawned (%s)", name, self.rank)

    @enforce_cost(role_name=lambda self: self.name)
    def call_llm(self, prompt: str) -> str:  # placeholder
        """Stub for future LLM calls."""
        return f"[{self.name} responding to]: {prompt}"