from conclave.agents.agent_factory import factory


def test_attributes_injected():
    """Each runtime subclass should inherit template fields."""
    tech = factory.spawn("Technomancer")
    assert tech.rank == 2
    assert hasattr(tech, "role_prompt")
    assert hasattr(tech, "token_cap")


def test_think_stub():
    """Stub returns a predictable string until LLM wiring is done."""
    tech = factory.spawn("Technomancer")
    assert tech.think() == "TODO-think"
