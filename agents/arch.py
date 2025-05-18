"""
arch.py: ArchTechnomancer class.
"""
import sys
import yaml
from pathlib import Path
from agents.base import AgentBase
from services.search import web_search

class ArchTechnomancer(AgentBase):
    """Orchestrator that plans milestones and controls costs."""
    def __init__(self):
        # Load roles config
        base_dir = Path(__file__).resolve().parents[1]
        config_path = base_dir / "config" / "roles.yaml"
        config = yaml.safe_load(config_path.read_text())
        role_conf = config["roles"]["ArchTechnomancer"]
        super().__init__(name="ArchTechnomancer", tools=role_conf.get("tools", []))
        # Initialize web.search tool
        self.search = web_search

    def plan_milestones(self, goal: str) -> list[str]:
        """Generate a milestone plan based on the goal."""
        # Placeholder implementation
        return [
            f"Define project scope: {goal}",
            "Set up repository scaffold",
            "Bootstrap ArchTechnomancer"
        ]

    def open_hand_offs(self, milestones: list[str]):
        """Hand off first epic to Engineering and stub tests via QA."""
        # Placeholder: print hand-off actions
        print(f"Handing off to HighTechnomancer-Engineering: {milestones[0]}")
        print("Requesting HighTechnomancer-QA to stub tests.")

def main():
    if len(sys.argv) < 2:
        print("Usage: python main.py <goal>")
        sys.exit(1)
    goal = sys.argv[1]
    arch = ArchTechnomancer()
    milestones = arch.plan_milestones(goal)
    # Write milestones to docs/MILESTONES.md
    base_dir = Path(__file__).resolve().parents[1]
    milestones_path = base_dir / "docs" / "MILESTONES.md"
    with open(milestones_path, "w") as f:
        f.write("# Milestones Plan\n\n")
        for m in milestones:
            f.write(f"- {m}\n")
    arch.open_hand_offs(milestones)

if __name__ == "__main__":
    main()