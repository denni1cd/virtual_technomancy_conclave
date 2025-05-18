"""
base.py: Tiny Agent base wrapping Agents SDK.
"""
from dataclasses import dataclass
from typing import List

@dataclass
class AgentBase:
    """Base class for Technomancer agents."""
    name: str
    tools: List[str]