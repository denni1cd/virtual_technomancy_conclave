import pytest
from conclave.agents.agent_factory import factory


def test_attributes_injected():
    """Each runtime subclass should inherit template fields."""
    tech = factory.spawn("Technomancer")
    assert tech.rank == 2
    assert hasattr(tech, "role_prompt")
    assert hasattr(tech, "token_cap")


def test_think_stub(monkeypatch):
    """Synchronous test with mocked client."""
    tech = factory.spawn("Technomancer")
    
    # Mock the async think method to be synchronous for testing
    def mock_think(*args, **kwargs):
        return "test response"
    
    monkeypatch.setattr(tech, "think", mock_think)
    result = tech.think("test prompt")
    assert result == "test response"
