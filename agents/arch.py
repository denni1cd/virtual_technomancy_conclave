# SPDX-License-Identifier: MIT

"""
agents.arch
~~~~~~~~~~~
Orchestrator that plans milestones, spawns sub-agents, and controls costs.
"""

import sys
from config import ROLES
from agents.technomancer_base import TechnomancerBase

class ArchTechnomancer(TechnomancerBase):
    """Orchestrator that plans milestones, spawns sub-agents, and controls costs."""
    def __init__(self):
        cfg = ROLES["ArchTechnomancer"]
        name = "ArchTechnomancer"
        tools = cfg.tools or []
        limits = cfg.limits
        super().__init__(name=name, tools=tools, limits=limits)

def main():
    """CLI entrypoint for ArchTechnomancer."""
    if len(sys.argv) < 2:
        print("Usage: python main.py <goal>")
        sys.exit(1)
    goal = " ".join(sys.argv[1:])
    arch = ArchTechnomancer()
    response = arch.call_llm(goal)
    print(response)