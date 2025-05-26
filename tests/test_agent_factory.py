import importlib
from conclave.agents.agent_factory import factory

def test_registry_has_four_roles():
    assert len(factory.registry) == 4

def test_spawn_properties():
    obj = factory.spawn("HighTechnomancer")
    assert obj.rank == 1
    assert obj.role_prompt
    assert obj.cost_cap_usd > 0
