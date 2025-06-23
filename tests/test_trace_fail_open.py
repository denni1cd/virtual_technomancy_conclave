"""
Test fail-open behavior when tracing backends are down.
"""

import pytest
import os
from unittest.mock import Mock, patch
from conclave.services.tracing import get_tracer, reset_tracer
from conclave.services.tracing.noop import NoopTracer


def test_noop_tracer_fallback():
    """Test that noop tracer is used when no backend is configured."""
    reset_tracer()
    os.environ.pop("TRACE_ENABLED", None)  # Clear any existing setting
    
    tracer = get_tracer()
    assert isinstance(tracer, NoopTracer)


def test_langsmith_fail_open():
    """Test that LangSmith tracer falls back to noop when initialization fails."""
    reset_tracer()
    os.environ["TRACE_ENABLED"] = "langsmith"
    
    # Mock langsmith import to fail
    with patch.dict('sys.modules', {'langsmith': None}):
        tracer = get_tracer()
        assert isinstance(tracer, NoopTracer)


def test_langfuse_fail_open():
    """Test that Langfuse tracer falls back to noop when initialization fails."""
    reset_tracer()
    os.environ["TRACE_ENABLED"] = "langfuse"
    
    # Mock langfuse import to fail
    with patch.dict('sys.modules', {'langfuse': None}):
        tracer = get_tracer()
        assert isinstance(tracer, NoopTracer)


def test_langsmith_network_failure():
    """Test that LangSmith tracer handles network failures gracefully."""
    reset_tracer()
    os.environ["TRACE_ENABLED"] = "langsmith"
    
    # Mock langsmith to raise network errors
    mock_langsmith = Mock()
    mock_client = Mock()
    mock_client.create_run.side_effect = Exception("Network timeout")
    mock_langsmith.Client.return_value = mock_client
    mock_langsmith.RunTree = Mock()
    
    with patch.dict('sys.modules', {'langsmith': mock_langsmith}):
        tracer = get_tracer()
        
        # Should not raise exception, should use noop behavior
        with tracer.root_span("test_project"):
            tracer.add_event("test", {"data": "value"})
        
        # Should not have called the failing client
        assert not mock_client.create_run.called


def test_langfuse_network_failure():
    """Test that Langfuse tracer handles network failures gracefully."""
    reset_tracer()
    os.environ["TRACE_ENABLED"] = "langfuse"
    
    # Mock langfuse to raise network errors
    mock_langfuse = Mock()
    mock_client = Mock()
    mock_client.trace.side_effect = Exception("Network timeout")
    mock_langfuse.Langfuse.return_value = mock_client
    
    with patch.dict('sys.modules', {'langfuse': mock_langfuse}):
        tracer = get_tracer()
        
        # Should not raise exception, should use noop behavior
        with tracer.root_span("test_project"):
            tracer.add_event("test", {"data": "value"})
        
        # Since the tracer fell back to noop, it shouldn't have called the failing client
        # But the LangfuseTracer constructor would have been called
        assert mock_langfuse.Langfuse.called


def test_trace_disabled_via_env():
    """Test that tracing can be disabled via environment variable."""
    reset_tracer()
    
    # Test various ways to disable tracing
    for disable_value in ["false", "0", "off", "none"]:
        os.environ["TRACE_ENABLED"] = disable_value
        tracer = get_tracer()
        assert isinstance(tracer, NoopTracer)


def test_trace_enabled_via_env():
    """Test that tracing can be enabled via environment variable."""
    reset_tracer()
    
    # Test various ways to enable tracing
    for enable_value in ["true", "1", "on", "langsmith"]:
        os.environ["TRACE_ENABLED"] = enable_value
        # Should not raise exception even if langsmith is not available
        tracer = get_tracer()
        # Should fall back to noop if langsmith is not available
        # Note: If langsmith is actually available, it will use LangSmithTracer
        # So we just check that we get a valid tracer
        assert hasattr(tracer, 'root_span')
        assert hasattr(tracer, 'child_span')
        assert hasattr(tracer, 'add_event')


def test_noop_tracer_operations():
    """Test that noop tracer operations don't fail."""
    tracer = NoopTracer()
    
    # All operations should complete without error
    with tracer.root_span("test_project", {"key": "value"}) as context:
        assert context.run_id == "noop"
        assert context.span_id == "noop"
        
        with tracer.child_span("test_child", "LLM") as child_context:
            assert child_context.run_id == "noop"
            assert child_context.span_id == "noop_test_child"
        
        tracer.add_event("test_event", {"data": "value"}, cost_usd=0.1, tokens=100)
    
    # Should not raise any exceptions


def test_trace_url_fallback():
    """Test that trace URL generation fails gracefully."""
    tracer = NoopTracer()
    url = tracer.get_trace_url()
    assert url is None


def test_context_propagation_fallback():
    """Test that context propagation works in noop mode."""
    tracer = NoopTracer()
    
    # Context operations should not fail
    context = tracer.get_current_context()
    assert context is None
    
    tracer.set_current_context(Mock())
    context = tracer.get_current_context()
    assert context is not None


def test_cleanup_after_failure():
    """Test that tracer state is cleaned up after failures."""
    reset_tracer()
    
    # Simulate a failure scenario
    os.environ["TRACE_ENABLED"] = "langsmith"
    
    # Mock langsmith to fail after successful initialization
    mock_langsmith = Mock()
    mock_client = Mock()
    mock_run = Mock()
    mock_run.start_child.side_effect = Exception("Runtime error")
    mock_client.create_run.return_value = mock_run
    mock_langsmith.Client.return_value = mock_client
    mock_langsmith.RunTree = Mock()
    
    with patch.dict('sys.modules', {'langsmith': mock_langsmith}):
        tracer = get_tracer()
        
        # Should handle runtime errors gracefully
        try:
            with tracer.root_span("test_project"):
                with tracer.child_span("test_child", "LLM"):
                    pass
        except Exception:
            pytest.fail("Tracer should handle runtime errors gracefully") 