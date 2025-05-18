"""
cost_tracker.py: Tracks token and dollar spend per agent.
"""
from collections import defaultdict

class CostTracker:
    """Tracks token and dollar usage per agent."""
    def __init__(self):
        self.usage = defaultdict(lambda: {"tokens": 0, "dollars": 0.0})

    def record(self, agent_name: str, tokens: int, cost: float):
        """Record usage for an agent."""
        self.usage[agent_name]["tokens"] += tokens
        self.usage[agent_name]["dollars"] += cost

    def get_usage(self, agent_name: str):
        """Get usage for a specific agent."""
        return self.usage.get(agent_name, {"tokens": 0, "dollars": 0.0})

    def reset(self):
        """Reset all tracked usage."""
        self.usage.clear()