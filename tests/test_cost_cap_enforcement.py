import pytest
from conclave.agents.agent_factory import factory
from conclave.services.cost_ledger import CostCapExceeded

def test_cap_triggers(tmp_path, monkeypatch):
    """Test that cost cap triggers correctly."""
    # redirect ledger to temp dir
    from conclave.services import cost_ledger
    monkeypatch.setattr("conclave.services.cost_ledger._LEDGER_FILE", tmp_path / "cap.jsonl")

    tech = factory.spawn("Technomancer")
    # Test with direct log_usage call to simulate huge usage
    with pytest.raises(CostCapExceeded):
        # 1M tokens at $10/1M = $10 cost, plus $0.01 to exceed cap
        cost_ledger.log_usage(
            role_name="Technomancer",
            agent_id=tech.agent_id,
            tokens=1_001_000,  # 1M + 1K tokens
            cost=10.01  # $10.01 to exceed $10.00 cap
        )
