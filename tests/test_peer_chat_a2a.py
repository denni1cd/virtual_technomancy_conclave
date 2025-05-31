"""
Test the peer_chat() helper with an in-memory FastAPI A2A server.
"""

import requests
from fastapi.testclient import TestClient

from conclave.services.a2a_server import app, latest_message
from conclave.tools import peer_chat_a2a

client = TestClient(app)


def test_peer_chat_roundtrip(monkeypatch):
    # Patch requests.post so peer_chat() talks to the TestClient instead
    def _fake_post(url, json, timeout):
        return client.post("/tasks", json=json)

    monkeypatch.setattr(requests, "post", _fake_post)

    result = peer_chat_a2a.peer_chat(
        target_url=str(client.base_url),
        sender_id="pytest",
        content="ping",
    )
    assert result.startswith("peer_chat sent")

    # server stored the message
    assert latest_message() == "ping"

    # agent card still responds
    r = client.get("/.well-known/agent.json")
    assert r.status_code == 200 and "peer_chat" in r.json()["skills"]

def test_tool_wrapper_exists_when_sdk_present():
    try:
        from agents import function_tool          # noqa: F401
        from agents.tool import FunctionTool
    except ImportError:
        pytest.skip("SDK not installed – wrapper check skipped")

    from conclave.tools.peer_chat_a2a import peer_chat_tool
    assert isinstance(peer_chat_tool, FunctionTool)
