"""
Test cost metric events in tracing.
"""

import pytest
from unittest.mock import Mock, patch
from conclave.services.tracing import get_tracer, reset_tracer
from conclave.services.cost_ledger import log_and_check, log_usage


class MockTracer:
    """Mock tracer for testing cost events."""
    
    def __init__(self):
        self.events = []
    
    def add_event(self, event_type: str, payload, cost_usd=None, tokens=None):
        self.events.append((event_type, payload, cost_usd, tokens))
    
    def get_current_context(self):
        return None
    
    def set_current_context(self, context):
        pass
    
    def start_root_span(self, project_name: str, metadata=None):
        return Mock()
    
    def start_child_span(self, name: str, kind: str, metadata=None):
        return Mock()
    
    def end_span(self, context, outputs=None):
        pass


@pytest.fixture
def mock_tracer():
    """Provide a mock tracer for testing."""
    reset_tracer()
    with patch('conclave.services.tracing._tracer', MockTracer()):
        yield get_tracer()


def test_cost_event_emission(mock_tracer):
    """Test that cost events are emitted when logging costs."""
    log_and_check(
        role_name="Technomancer",
        agent_id="test_agent_123",
        tokens=1000,
        cost=0.15,
        extra={"operation": "test_call"}
    )
    
    assert len(mock_tracer.events) == 1
    event_type, payload, cost_usd, tokens = mock_tracer.events[0]
    
    assert event_type == "cost"
    assert payload["role"] == "Technomancer"
    assert payload["agent"] == "test_agent_123"
    assert payload["operation"] == "test_call"
    assert cost_usd == 0.15
    assert tokens == 1000


def test_cost_event_without_extra(mock_tracer):
    """Test that cost events work without extra metadata."""
    log_and_check(
        role_name="HighTechnomancer",
        agent_id="high_agent_456",
        tokens=500,
        cost=0.075
    )
    
    assert len(mock_tracer.events) == 1
    event_type, payload, cost_usd, tokens = mock_tracer.events[0]
    
    assert event_type == "cost"
    assert payload["role"] == "HighTechnomancer"
    assert payload["agent"] == "high_agent_456"
    assert payload["operation"] == "unknown"  # Default when no extra
    assert cost_usd == 0.075
    assert tokens == 500


def test_log_usage_wrapper(mock_tracer):
    """Test that log_usage wrapper also emits cost events."""
    log_usage(
        role_name="ArchTechnomancer",
        agent_id="arch_agent_789",
        tokens=2000,
        cost=0.30,
        extra={"operation": "milestone_execution"}
    )
    
    assert len(mock_tracer.events) == 1
    event_type, payload, cost_usd, tokens = mock_tracer.events[0]
    
    assert event_type == "cost"
    assert payload["role"] == "ArchTechnomancer"
    assert payload["agent"] == "arch_agent_789"
    assert payload["operation"] == "milestone_execution"
    assert cost_usd == 0.30
    assert tokens == 2000


def test_cost_event_fail_open(mock_tracer):
    """Test that cost events fail open when tracing fails."""
    # Mock the tracer to raise an exception
    def failing_add_event(*args, **kwargs):
        raise Exception("Tracing backend down")
    
    mock_tracer.add_event = failing_add_event
    
    # This should not raise an exception
    try:
        log_and_check(
            role_name="Technomancer",
            agent_id="test_agent",
            tokens=100,
            cost=0.01
        )
    except Exception:
        pytest.fail("Cost logging should not fail when tracing fails")


def test_multiple_cost_events(mock_tracer):
    """Test that multiple cost events are tracked correctly."""
    # Log multiple costs
    log_and_check("Technomancer", "agent1", 100, 0.01, extra={"operation": "call1"})
    log_and_check("Technomancer", "agent2", 200, 0.02, extra={"operation": "call2"})
    log_and_check("HighTechnomancer", "agent3", 300, 0.03, extra={"operation": "call3"})
    
    assert len(mock_tracer.events) == 3
    
    # Check first event
    event_type, payload, cost_usd, tokens = mock_tracer.events[0]
    assert event_type == "cost"
    assert payload["agent"] == "agent1"
    assert cost_usd == 0.01
    assert tokens == 100
    
    # Check second event
    event_type, payload, cost_usd, tokens = mock_tracer.events[1]
    assert event_type == "cost"
    assert payload["agent"] == "agent2"
    assert cost_usd == 0.02
    assert tokens == 200
    
    # Check third event
    event_type, payload, cost_usd, tokens = mock_tracer.events[2]
    assert event_type == "cost"
    assert payload["agent"] == "agent3"
    assert cost_usd == 0.03
    assert tokens == 300


def test_cost_event_with_total_aggregation(mock_tracer):
    """Test that cost events include total aggregation when caps are defined."""
    # This test would require mocking the role caps, but we can test the basic structure
    log_and_check(
        role_name="Technomancer",
        agent_id="test_agent",
        tokens=100,
        cost=0.01,
        extra={"operation": "test"}
    )
    
    assert len(mock_tracer.events) == 1
    event_type, payload, cost_usd, tokens = mock_tracer.events[0]
    
    assert event_type == "cost"
    assert "total_tokens" in payload
    assert "total_cost" in payload 