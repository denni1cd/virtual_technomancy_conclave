"""
technomancer_code.py: Generic worker agent.
"""
from agents.base import AgentBase
from tools.cost_tracker import CostTracker

class TechnomancerCode(AgentBase):
    """Worker agent that writes/modifies code."""
    def __init__(self):
        super().__init__(name="Technomancer-Code", tools=["cost_tracker"])
        self.cost_tracker = CostTracker()

    def write_code(self, instructions: str) -> str:
        """Write code based on instructions."""
        # Placeholder implementation
        return "# code generated based on instructions: " + instructions

    def run_tests(self) -> bool:
        """Run unit tests in sandbox and return True if success."""
        import subprocess
        result = subprocess.run(["pytest", "-q"], capture_output=True)
        return result.returncode == 0