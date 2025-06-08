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
        # 1M tokens at $10/1M = $10 cost
        cost_ledger.log_usage(
            role_name="Technomancer",
            agent_id=tech.cfg.role_name,
            tokens=1_000_000,
            cost=10.0
        )
