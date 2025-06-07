# tests/test_technomancer_llm.py
import pytest
from conclave.agents.agent_factory import factory

@pytest.mark.asyncio
async def test_llm_call(monkeypatch):
    """Test that the LLM call gets properly mocked."""
    tech = factory.spawn("Technomancer")

    class MockResponse:
        output_text = "test response"
        usage = type("Usage", (), {
            "model_dump": lambda self: {
                "input_tokens": 1,
                "output_tokens": 2
            }
        })()

    class MockClient:
        class responses:
            @staticmethod
            async def create(*args, **kwargs):
                return MockResponse()
    
    import conclave.agents.technomancer_base as tb
    monkeypatch.setattr(tb, "_client", MockClient())

    result = await tech.think("test prompt")
    assert result == "test response"
