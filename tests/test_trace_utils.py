import importlib
import os
import types

import pytest

# Always import via package so reload() works
import conclave.services.trace_utils as trace_utils


def test_trace_url_prints_when_key_present(monkeypatch, capsys):
    """If OPENAI_API_KEY is set, helper should print the trace URL."""
    # Ensure the key is in the environment
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")

    # Reload module so load_dotenv() re-evaluates with the new env var
    importlib.reload(trace_utils)

    # Fake a minimal AgentRun-like object returned by the SDK
    run = types.SimpleNamespace(trace_url="https://platform.openai.com/traces/r/abc123")

    trace_utils.print_trace_url(run)
    out = capsys.readouterr().out
    assert "https://platform.openai.com/traces/r/abc123" in out


def test_notice_prints_when_key_missing(monkeypatch, capsys):
    """If the key is missing, helper should warn and NOT raise."""
    # Remove the env var if it exists
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    
    # Mock load_dotenv to do nothing (simulating no .env file found)
    def mock_load_dotenv(*args, **kwargs):
        return False
    monkeypatch.setattr("dotenv.load_dotenv", mock_load_dotenv)
    
    importlib.reload(trace_utils)  # reload with key absent

    run = types.SimpleNamespace(trace_url="https://example.com/trace/xyz")
    trace_utils.print_trace_url(run)
    out = capsys.readouterr().out
    assert "not set" in out.lower()  # generic notice
