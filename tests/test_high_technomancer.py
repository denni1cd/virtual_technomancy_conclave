from conclave.agents.agent_factory import factory
import importlib
import pytest

# ensure monkey-patch runs
import conclave.agents.high_behavior  # noqa: F401


def test_majority_via_hightechnomancer(monkeypatch):
    # Patch all Technomancer think methods to return 'TODO-think'
    def fake_think(self, *args, **kwargs):
        return "TODO-think"
    # Patch the class, so all instances use the fake_think
    for cls in factory.registry.values():
        if cls.__name__.startswith("ConclaveTechnomancer"):
            monkeypatch.setattr(cls, "think", fake_think)

    high = factory.spawn("HighTechnomancer")
    # ask for 4 techs; helper auto-odd → 5
    decision = high.run_milestone(issue="Return A", tech_count=4)
    assert decision == "TODO-think"
