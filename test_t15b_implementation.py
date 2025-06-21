#!/usr/bin/env python3
"""
Test script for T15-b implementation.
This script verifies that the context isolation and atomic ledger operations work correctly.
"""

import asyncio
import tempfile
import json
from pathlib import Path
import pytest

from conclave.services.context import set_role, get_role, create_task_with_context
from conclave.services.cost_ledger import log_and_check, CostCapExceeded


@pytest.mark.asyncio
async def test_context_isolation():
    """Test that each async task sees its own role context."""
    print("Testing context isolation...")
    
    async def task_with_role(role_name: str, task_id: int):
        """Async task that sets a role and verifies it's isolated."""
        set_role(role_name)
        await asyncio.sleep(0.01)  # Small delay to allow context switching
        current_role = get_role()
        return task_id, role_name, current_role
    
    tasks = []
    for i in range(5):
        role = f"Role_{i}"
        task = create_task_with_context(task_with_role(role, i), role)
        tasks.append(task)
    
    results = await asyncio.gather(*tasks)
    
    # Verify each task got its own role
    for task_id, expected_role, actual_role in results:
        assert actual_role == expected_role, f"Task {task_id}: expected {expected_role}, got {actual_role}"
        print(f"  ✓ Task {task_id}: {expected_role} == {actual_role}")
    
    print("  ✓ Context isolation test passed!")


def test_atomic_ledger_operations():
    """Test that atomic ledger operations work correctly."""
    print("Testing atomic ledger operations...")
    
    # Create a temporary ledger file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
        temp_ledger = Path(f.name)
    
    try:
        # Monkey patch the ledger file
        import conclave.services.cost_ledger
        original_ledger = conclave.services.cost_ledger._LEDGER_FILE
        conclave.services.cost_ledger._LEDGER_FILE = temp_ledger
        
        agent_id = "TestAgent_123"
        role_name = "Apprentice"  # Has $5.00 cap
        
        # Test that we can spend exactly up to the cap
        log_and_check(role_name, agent_id, 500_000, 5.00)
        print(f"  ✓ Successfully spent exactly $5.00")
        
        # Verify the record was written
        assert temp_ledger.exists()
        with temp_ledger.open(encoding="utf-8") as fh:
            lines = fh.readlines()
            assert len(lines) == 1
            
            record = json.loads(lines[0])
            assert record["agent"] == agent_id
            assert record["role"] == role_name
            assert record["cost"] == 5.00
            print(f"  ✓ Record written correctly: {record}")
        
        # Test that spending $0.01 more raises the exception
        try:
            log_and_check(role_name, agent_id, 1000, 0.01)
            assert False, "Expected CostCapExceeded exception"
        except CostCapExceeded as e:
            print(f"  ✓ CostCapExceeded raised correctly: {e}")
        
        # Verify no additional record was written (atomic operation failed)
        with temp_ledger.open(encoding="utf-8") as fh:
            lines = fh.readlines()
            assert len(lines) == 1, "Atomic operation should not have written additional record"
            print(f"  ✓ No additional record written (atomic operation failed correctly)")
        
        print("  ✓ Atomic ledger operations test passed!")
        
    finally:
        # Restore original ledger file
        conclave.services.cost_ledger._LEDGER_FILE = original_ledger
        # Clean up temp file
        temp_ledger.unlink(missing_ok=True)


@pytest.mark.asyncio
async def test_concurrent_spend_race_condition():
    """Test that concurrent spending doesn't cause race conditions."""
    print("Testing concurrent spend race condition...")
    
    # Create a temporary ledger file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
        temp_ledger = Path(f.name)
    
    try:
        # Monkey patch the ledger file
        import conclave.services.cost_ledger
        original_ledger = conclave.services.cost_ledger._LEDGER_FILE
        conclave.services.cost_ledger._LEDGER_FILE = temp_ledger
        
        agent_id = "RaceTest_1111"
        role_name = "Apprentice"  # Has $5.00 cap
        
        async def spend_dollar():
            """Async function that spends exactly $1.00."""
            log_and_check(role_name, agent_id, 100_000, 1.00)
            return True
        
        # Run 10 concurrent tasks, each spending $1.00
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
        
        # Verify exactly 5 tasks succeeded (spending $5.00 total)
        assert len(results) == 5, f"Expected 5 successful spends, got {len(results)}"
        print(f"  ✓ {len(results)} tasks succeeded (spent $5.00 total)")
        
        # Verify exactly 5 tasks failed due to cap exceeded
        assert len(exceptions) == 5, f"Expected 5 cap exceeded exceptions, got {len(exceptions)}"
        print(f"  ✓ {len(exceptions)} tasks failed due to cap exceeded")
        
        # Verify the ledger contains exactly 5 records
        assert temp_ledger.exists()
        with temp_ledger.open(encoding="utf-8") as fh:
            lines = fh.readlines()
            assert len(lines) == 5, f"Expected 5 ledger entries, got {len(lines)}"
            
            # Verify all records have the correct agent_id and role
            total_cost = 0
            for line in lines:
                record = json.loads(line)
                assert record["agent"] == agent_id
                assert record["role"] == role_name
                total_cost += record["cost"]
            
            # Verify total cost is exactly $5.00
            assert abs(total_cost - 5.00) < 0.001, f"Expected total cost $5.00, got ${total_cost:.2f}"
            print(f"  ✓ Total cost: ${total_cost:.2f} (exactly $5.00)")
        
        print("  ✓ Concurrent spend race condition test passed!")
        
    finally:
        # Restore original ledger file
        conclave.services.cost_ledger._LEDGER_FILE = original_ledger
        # Clean up temp file
        temp_ledger.unlink(missing_ok=True)


async def main():
    """Run all tests."""
    print("Running T15-b implementation tests...\n")
    
    # Test context isolation
    await test_context_isolation()
    print()
    
    # Test atomic ledger operations
    test_atomic_ledger_operations()
    print()
    
    # Test concurrent spend race condition
    await test_concurrent_spend_race_condition()
    print()
    
    print("🎉 All T15-b tests passed!")


if __name__ == "__main__":
    asyncio.run(main()) 