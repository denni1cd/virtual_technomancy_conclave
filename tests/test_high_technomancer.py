from conclave.agents.agent_factory import factory
import importlib

# ensure monkey-patch runs
import conclave.agents.high_behavior  # noqa: F401


def test_majority_via_hightechnomancer():
    high = factory.spawn("HighTechnomancer")
    # ask for 4 techs; helper auto-odd → 5
    decision = high.run_milestone(issue="Return A", tech_count=4)
    # our Technomancer.think() stub always responds "TODO-think"
    assert decision == "TODO-think"
