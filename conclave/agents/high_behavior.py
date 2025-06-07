"""
Attach debate orchestration to every HighTechnomancer subclass at startup.

Called once from your app entry-point (ideally right after AgentFactory is
instantiated).  Relies on:

* AgentFactory.registry           – read-only mapping {role_name: cls}
* ConclaveTechnomancer subclasses – already include .think()
* DebateManager                   – imported from conclave.consensus
"""

import asyncio
from collections import Counter
from typing import List

from conclave.consensus.debate_manager import DebateManager
from conclave.agents.agent_factory import factory

# -------------------------------------------------------------------- #
# helper
# -------------------------------------------------------------------- #


def _odd(n: int) -> int:  # ensure odd pool, minimum 1
    return n if n % 2 else n + 1


def _attach_to(cls):
    """Inject .run_milestone() into the HighTechnomancer subclass."""

    async def _debate_async(self, issue: str, techs: List):
        mgr = DebateManager(rounds=getattr(self, "debate_rounds", 3))
        decision, history = mgr.run(issue=issue, agents=techs)
        return decision, history

    def run_milestone(self, issue: str, tech_count: int = 3):
        tech_count = _odd(tech_count)
        techs = [factory.spawn("Technomancer") for _ in range(tech_count)]
        # DebateManager.run() is already synchronous and creates its own loop
        mgr = DebateManager(rounds=getattr(self, "debate_rounds", 3))
        decision, _hist = mgr.run(issue=issue, agents=techs)
        return decision

    cls.run_milestone = run_milestone  # monkey-patch


# -------------------------------------------------------------------- #
# patch every HighTechnomancer runtime subclass
# -------------------------------------------------------------------- #
for name, cls in factory.registry.items():
    if "HighTechnomancer" in name:
        _attach_to(cls)
