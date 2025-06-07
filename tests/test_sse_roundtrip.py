# tests/test_sse_roundtrip.py
"""
Async SSE round-trip:
  • POST /tasks             → server stores task
  • GET  /subscribe         → Accept-Limit:1 → server replays and closes
  • Assert replay contains “ping”.
"""

from __future__ import annotations
import json, os, time, asyncio, httpx
import pytest
from conclave.services import a2a_server as srv

# Force ANYIO to use *only* asyncio for every test in this module
pytestmark = pytest.mark.anyio("asyncio")

def _auth_hdr() -> dict[str, str]:
    secret = os.getenv("A2A_SECRET")
    if not secret:
        return {}
    try:
        import jwt
        return {"Authorization": f"Bearer {jwt.encode({'exp': time.time()+60}, secret, algorithm='HS256')}"}
    except Exception:
        pytest.skip("PyJWT unavailable")
        return {}

async def _first_event(stream: httpx.Response) -> dict:
    async for line in stream.aiter_lines():
        if line.startswith("data:"):
            return json.loads(line[5:].strip())

async def test_sse_stream():
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=srv.app),
        base_url="http://test",
    ) as ac:
        # 1️⃣  POST a task
        payload = {
            "id": "1",
            "state": "submitted",
            "messages": [{"role": "user", "content": "ping", "timestamp": int(time.time())}],
        }
        await ac.post("/tasks", json=payload, headers=_auth_hdr())

        # 2️⃣  Subscribe (Accept-Limit:1 ends stream after first event)
        async with ac.stream("GET", "/subscribe",
                             headers={"Accept-Limit": "1", **_auth_hdr()}) as stream:
            event = await asyncio.wait_for(_first_event(stream), timeout=2)
            assert event["messages"][0]["content"] == "ping"
