import os, json

def test_memory_roundtrip(tmp_path, monkeypatch):
    monkeypatch.setenv("CONCLAVE_HOME", tmp_path.as_posix())
    from services.memory import MemoryStore
    store = MemoryStore.for_agent("UnitTester", "ticket")
    store.append("user", "hello")
    assert store.fetch_last(1)[0]["message"] == "hello"
    raw = store.path.read_text(encoding="utf-8").strip()
    assert json.loads(raw)["message"] == "hello"