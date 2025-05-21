import pytest
from agents.agent_factory import AgentFactory, AgentFactoryError

def test_arch_memory_attachment(tmp_path, monkeypatch):
    monkeypatch.setenv("CONCLAVE_HOME", tmp_path.as_posix())
    arch = AgentFactory.create_agent("ArchTechnomancer")
    arch.memory.append("system", "ping")
    assert arch.memory.fetch_last(1)[0]["message"] == "ping"

def test_template_role(tmp_path, monkeypatch):
    monkeypatch.setenv("CONCLAVE_HOME", tmp_path.as_posix())
    worker = AgentFactory.create_agent("Technomancer-Docs")
    assert worker.memory.fetch_last() == []

def test_unknown_role():
    with pytest.raises(AgentFactoryError):
        AgentFactory.create_agent("NoSuchRole")
