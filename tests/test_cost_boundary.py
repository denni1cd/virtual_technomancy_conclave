import pytest
import asyncio
import contextvars
from conclave.services.cost_ledger import log_usage, CostCapExceeded, log_and_check
from conclave.services.context import set_role, get_role, create_task_with_context


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


def test_context_isolation():
    """Test that each async task sees its own role context."""
    async def task_with_role(role_name: str, task_id: int):
        """Async task that sets a role and verifies it's isolated."""
        set_role(role_name)
        await asyncio.sleep(0.01)  # Small delay to allow context switching
        current_role = get_role()
        return task_id, role_name, current_role
    
    async def run_context_test():
        """Run multiple tasks with different roles and verify isolation."""
        tasks = []
        for i in range(5):
            role = f"Role_{i}"
            task = create_task_with_context(task_with_role(role, i), role)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks)
        
        # Verify each task got its own role
        for task_id, expected_role, actual_role in results:
            assert actual_role == expected_role, f"Task {task_id}: expected {expected_role}, got {actual_role}"
        
        return results
    
    # Run the test
    results = asyncio.run(run_context_test())
    assert len(results) == 5


def test_concurrent_spend_race_condition(tmp_path, monkeypatch):
    """Test that concurrent spending doesn't cause race conditions."""
    # Redirect ledger to temp dir
    from conclave.services import cost_ledger
    monkeypatch.setattr("conclave.services.cost_ledger._LEDGER_FILE", tmp_path / "race.jsonl")
    
    agent_id = "RaceTest_1111"
    role_name = "Apprentice"  # Has $5.00 cap
    
    async def spend_dollar():
        """Async function that spends exactly $1.00."""
        log_and_check(role_name, agent_id, 100_000, 1.00)
        return True
    
    async def run_concurrent_spend():
        """Run 10 concurrent tasks, each spending $1.00."""
        tasks = []
        for i in range(10):
            task = create_task_with_context(spend_dollar(), f"Spender_{i}")
            tasks.append(task)
        
        results = []
        exceptions = []
        
        # Gather results, catching exceptions
        for task in asyncio.as_completed(tasks):
            try:
                result = await task
                results.append(result)
            except CostCapExceeded as e:
                exceptions.append(e)
        
        return results, exceptions
    
    # Run the concurrent test
    results, exceptions = asyncio.run(run_concurrent_spend())
    
    # Verify exactly 5 tasks succeeded (spending $5.00 total)
    assert len(results) == 5, f"Expected 5 successful spends, got {len(results)}"
    
    # Verify exactly 5 tasks failed due to cap exceeded
    assert len(exceptions) == 5, f"Expected 5 cap exceeded exceptions, got {len(exceptions)}"
    
    # Verify all exceptions are CostCapExceeded
    for exc in exceptions:
        assert isinstance(exc, CostCapExceeded)
        assert "would exceed" in str(exc).lower()
    
    # Verify the ledger contains exactly 5 records
    ledger_file = tmp_path / "race.jsonl"
    assert ledger_file.exists()
    
    with ledger_file.open(encoding="utf-8") as fh:
        lines = fh.readlines()
        assert len(lines) == 5, f"Expected 5 ledger entries, got {len(lines)}"
        
        # Verify all records have the correct agent_id and role
        import json
        total_cost = 0
        for line in lines:
            record = json.loads(line)
            assert record["agent"] == agent_id
            assert record["role"] == role_name
            total_cost += record["cost"]
        
        # Verify total cost is exactly $5.00
        assert abs(total_cost - 5.00) < 0.001, f"Expected total cost $5.00, got ${total_cost:.2f}"


def test_atomic_log_and_check(tmp_path, monkeypatch):
    """Test that log_and_check is truly atomic."""
    # Redirect ledger to temp dir
    from conclave.services import cost_ledger
    monkeypatch.setattr("conclave.services.cost_ledger._LEDGER_FILE", tmp_path / "atomic.jsonl")
    
    agent_id = "AtomicTest_2222"
    role_name = "Technomancer"  # Has $10.00 cap
    
    # Test that we can spend exactly up to the cap
    log_and_check(role_name, agent_id, 1_000_000, 10.00)
    
    # Verify the record was written
    ledger_file = tmp_path / "atomic.jsonl"
    assert ledger_file.exists()
    
    with ledger_file.open(encoding="utf-8") as fh:
        lines = fh.readlines()
        assert len(lines) == 1
        
        import json
        record = json.loads(lines[0])
        assert record["agent"] == agent_id
        assert record["role"] == role_name
        assert record["cost"] == 10.00
    
    # Test that spending $0.01 more raises the exception
    with pytest.raises(CostCapExceeded):
        log_and_check(role_name, agent_id, 1000, 0.01)
    
    # Verify no additional record was written (atomic operation failed)
    with ledger_file.open(encoding="utf-8") as fh:
        lines = fh.readlines()
        assert len(lines) == 1, "Atomic operation should not have written additional record" 