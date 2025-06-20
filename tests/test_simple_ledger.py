import pytest
import json
from conclave.services.cost_ledger import log_usage, _totals, log_for, _AGENT_ID_VAR


def test_basic_log_usage(tmp_path, monkeypatch):
    """Test basic log_usage functionality."""
    # Redirect ledger to temp dir
    from conclave.services import cost_ledger
    ledger_file = tmp_path / "basic.jsonl"
    monkeypatch.setattr("conclave.services.cost_ledger._LEDGER_FILE", ledger_file)
    
    # Test basic logging
    log_usage("Technomancer", "TestAgent_123", 100, 0.01)
    
    # Verify file was created and contains valid JSON
    assert ledger_file.exists()
    
    with ledger_file.open(encoding="utf-8") as fh:
        lines = fh.readlines()
        assert len(lines) == 1
        
        record = json.loads(lines[0])
        assert record["agent"] == "TestAgent_123"
        assert record["role"] == "Technomancer"
        assert record["tokens"] == 100
        assert record["cost"] == 0.01


def test_log_for_with_context(tmp_path, monkeypatch):
    """Test log_for with ContextVar set."""
    # Redirect ledger to temp dir
    from conclave.services import cost_ledger
    ledger_file = tmp_path / "context.jsonl"
    monkeypatch.setattr("conclave.services.cost_ledger._LEDGER_FILE", ledger_file)
    
    # Set context var
    _AGENT_ID_VAR.set("ContextAgent_456")
    
    # Test log_for
    log_for("Technomancer", 200, 0.02)
    
    # Verify file was created and contains valid JSON
    assert ledger_file.exists()
    
    with ledger_file.open(encoding="utf-8") as fh:
        lines = fh.readlines()
        assert len(lines) == 1
        
        record = json.loads(lines[0])
        assert record["agent"] == "ContextAgent_456"
        assert record["role"] == "Technomancer"
        assert record["tokens"] == 200
        assert record["cost"] == 0.02


def test_log_for_fallback(tmp_path, monkeypatch):
    """Test log_for falls back to role name when no context."""
    # Redirect ledger to temp dir
    from conclave.services import cost_ledger
    ledger_file = tmp_path / "fallback.jsonl"
    monkeypatch.setattr("conclave.services.cost_ledger._LEDGER_FILE", ledger_file)
    
    # Create a completely fresh context without any variables
    import contextvars
    ctx = contextvars.Context()
    
    def run_without_context():
        # This should fall back to role name
        log_for("Apprentice", 50, 0.005)
    
    # Run in fresh context without any variables set
    ctx.run(run_without_context)
    
    # Verify file was created and contains valid JSON
    assert ledger_file.exists()
    
    with ledger_file.open(encoding="utf-8") as fh:
        lines = fh.readlines()
        assert len(lines) == 1
        
        record = json.loads(lines[0])
        assert record["agent"] == "Apprentice"  # Should fall back to role name
        assert record["role"] == "Apprentice"
        assert record["tokens"] == 50
        assert record["cost"] == 0.005


def test_totals_function(tmp_path, monkeypatch):
    """Test _totals function."""
    # Redirect ledger to temp dir
    from conclave.services import cost_ledger
    ledger_file = tmp_path / "totals.jsonl"
    monkeypatch.setattr("conclave.services.cost_ledger._LEDGER_FILE", ledger_file)
    
    # Add some test data
    log_usage("Technomancer", "TotalAgent_789", 100, 0.01)
    log_usage("Technomancer", "TotalAgent_789", 200, 0.02)
    log_usage("Technomancer", "OtherAgent_999", 50, 0.005)
    
    # Test totals
    totals = _totals("TotalAgent_789")
    assert totals["tokens"] == 300
    assert abs(totals["cost"] - 0.03) < 0.001
    
    other_totals = _totals("OtherAgent_999")
    assert other_totals["tokens"] == 50
    assert abs(other_totals["cost"] - 0.005) < 0.001 