# SPDX-License-Identifier: MIT
from config import ROLES
from agents.technomancer_base import TechnomancerBase

class Technomancer(TechnomancerBase):
    """Generic Technomancer for various expertise areas."""
    def __init__(self, expertise: str, memory_scope: str | None = None):
        cfg = ROLES["TechnomancerTemplate"]
        name = f"Technomancer-{expertise}"
        tools = cfg.tools or []
        limits = cfg.limits
        # Determine memory_scope default from configuration
        default_scope = cfg.parameters.get("memory_scope") if hasattr(cfg, "parameters") else None
        ms = memory_scope or default_scope
        super().__init__(name=name, tools=tools, limits=limits)
        self.expertise = expertise
        self.memory_scope = ms