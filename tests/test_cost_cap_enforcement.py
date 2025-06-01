import pytest
from types import SimpleNamespace
from conclave.agents.agent_factory import factory
from conclave.services.cost_ledger import CostCapExceeded, _LEDGER_FILE

def test_cap_triggers(tmp_path, monkeypatch):
    # redirect ledger to temp dir
    monkeypatch.setattr("conclave.services.cost_ledger._LEDGER_FILE", tmp_path / "cap.jsonl")

    tech = factory.spawn("Technomancer")
    # monkeypatch _log_cost to simulate huge usage
    with pytest.raises(CostCapExceeded):
        tech._log_cost(prompt_tokens=1_000_000, completion_tokens=0)
