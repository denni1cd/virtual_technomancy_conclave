import pytest
from conclave.services.cost_ledger import log_usage, CostCapExceeded


def test_exact_cap_boundary(tmp_path, monkeypatch):
    """Test that exact cap usage doesn't trigger exception, but $0.01 more does."""
    # Redirect ledger to temp dir
    from conclave.services import cost_ledger
    monkeypatch.setattr("conclave.services.cost_ledger._LEDGER_FILE", tmp_path / "boundary.jsonl")
    
    agent_id = "BoundaryTest_1234"
    role_name = "Technomancer"  # Has $10.00 cap
    
    # Log usage that brings cost exactly to $10.00
    # 1M tokens at $10/1M = $10.00 cost
    log_usage(role_name, agent_id, 1_000_000, 10.00)
    
    # This should NOT raise an exception
    # Verify the record was written
    ledger_file = tmp_path / "boundary.jsonl"
    assert ledger_file.exists()
    
    with ledger_file.open(encoding="utf-8") as fh:
        lines = fh.readlines()
        assert len(lines) == 1, f"Expected 1 line, got {len(lines)}"
        
        import json
        record = json.loads(lines[0])
        assert record["agent"] == agent_id
        assert record["cost"] == 10.00
        assert record["tokens"] == 1_000_000
    
    # Now log $0.01 more - this should raise CostCapExceeded
    with pytest.raises(CostCapExceeded) as exc_info:
        log_usage(role_name, agent_id, 1000, 0.01)  # $0.01 more
    
    # Verify the exception message
    assert "would exceed" in str(exc_info.value).lower()
    assert "10.00" in str(exc_info.value)
    assert "10.01" in str(exc_info.value)


def test_penny_over_cap(tmp_path, monkeypatch):
    """Test that going over by just a penny triggers the exception."""
    # Redirect ledger to temp dir
    from conclave.services import cost_ledger
    monkeypatch.setattr("conclave.services.cost_ledger._LEDGER_FILE", tmp_path / "penny.jsonl")
    
    agent_id = "PennyTest_5678"
    role_name = "Apprentice"  # Has $5.00 cap
    
    # Log usage that brings cost to $4.99
    log_usage(role_name, agent_id, 499_000, 4.99)
    
    # Log $0.02 more - this should raise CostCapExceeded
    with pytest.raises(CostCapExceeded) as exc_info:
        log_usage(role_name, agent_id, 2000, 0.02)  # $0.02 more = $5.01 total
    
    # Verify the exception message
    assert "would exceed" in str(exc_info.value).lower()
    assert "5.00" in str(exc_info.value)
    assert "5.01" in str(exc_info.value)


def test_multiple_small_increments(tmp_path, monkeypatch):
    """Test that multiple small increments that exceed cap are caught."""
    # Redirect ledger to temp dir
    from conclave.services import cost_ledger
    monkeypatch.setattr("conclave.services.cost_ledger._LEDGER_FILE", tmp_path / "increments.jsonl")
    
    agent_id = "IncrementTest_9999"
    role_name = "Technomancer"  # Has $10.00 cap
    
    # Log several small amounts that add up to exactly $10.00
    amounts = [2.00, 3.00, 3.50, 1.50]
    for amount in amounts:
        log_usage(role_name, agent_id, int(amount * 100_000), amount)
    
    # Verify we're at exactly $10.00
    from conclave.services.cost_ledger import _totals
    totals = _totals(agent_id)
    assert abs(totals["cost"] - 10.00) < 0.001, f"Expected 10.00, got {totals['cost']}"
    
    # Now try to log $0.01 more
    with pytest.raises(CostCapExceeded):
        log_usage(role_name, agent_id, 1000, 0.01) 