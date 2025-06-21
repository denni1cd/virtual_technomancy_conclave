import pytest
import contextvars
from conclave.services.cost_ledger import log_for, _AGENT_ID_VAR


def test_contextvar_agent_id():
    """Test that log_for() uses the correct unique agent ID from context."""
    # Set a unique agent ID in the context
    unique_agent_id = "TechTest_1234"
    _AGENT_ID_VAR.set(unique_agent_id)
    
    # Call log_for with a role name
    role_name = "Technomancer"
    tokens = 100
    cost = 0.01
    
    # This should use the unique agent ID, not the plain role name
    log_for(role_name, tokens, cost)
    
    # Verify the ledger contains the unique agent ID
    from conclave.services.cost_ledger import _LEDGER_FILE
    if _LEDGER_FILE.exists():
        with _LEDGER_FILE.open(encoding="utf-8") as fh:
            lines = fh.readlines()
            if lines:
                last_line = lines[-1]
                import json
                record = json.loads(last_line)
                assert record["agent"] == unique_agent_id, f"Expected {unique_agent_id}, got {record['agent']}"
                assert record["role"] == role_name
                assert record["tokens"] == tokens
                assert record["cost"] == cost


def test_contextvar_fallback():
    """Test that log_for() falls back to role name when no agent_id is set."""
    # Create a completely fresh context without any variables
    import contextvars
    ctx = contextvars.Context()
    
    def run_without_context():
        # Call log_for without setting agent_id
        role_name = "Apprentice"
        tokens = 50
        cost = 0.005
        
        log_for(role_name, tokens, cost)
        
        # Verify the ledger contains the role name as agent_id
        from conclave.services.cost_ledger import _LEDGER_FILE
        if _LEDGER_FILE.exists():
            with _LEDGER_FILE.open(encoding="utf-8") as fh:
                lines = fh.readlines()
                if lines:
                    last_line = lines[-1]
                    import json
                    record = json.loads(last_line)
                    assert record["agent"] == role_name, f"Expected {role_name}, got {record['agent']}"
                    assert record["role"] == role_name
                    assert record["tokens"] == tokens
                    assert record["cost"] == cost
    
    # Run in fresh context without any variables set
    ctx.run(run_without_context) 