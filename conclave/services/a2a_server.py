"""
FastAPI A2A server with:
    • POST /tasks                – accept Task envelopes
    • GET  /subscribe            – Server-Sent Events stream (SSE)
    • optional JWT auth (set A2A_SECRET env-var)
    • ring-buffer replay (last 1 000 tasks)
"""

from __future__ import annotations
import os, uuid, time, json, asyncio
from collections import deque
from typing import Dict, Any, AsyncGenerator

from fastapi import FastAPI, HTTPException, Depends, Request, status, Header
from sse_starlette.sse import EventSourceResponse          # pip install sse-starlette
from pydantic import BaseModel

# ─── config ────────────────────────────────────────────────────────────────
A2A_VERSION = "0.1.0"
JWT_SECRET = os.getenv("A2A_SECRET")        # if set, endpoints require JWT
JWT_ALG = "HS256"

def _verify_token(req: Request) -> None:
    """JWT Bearer token guard (skipped when A2A_SECRET unset)."""
    if not JWT_SECRET:
        return

    try:
        import jwt
        from jwt import InvalidTokenError
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="JWT support unavailable on host",
        )

    auth = req.headers.get("Authorization")
    if not (auth and auth.startswith("Bearer ")):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

    token = auth.split(maxsplit=1)[1]
    try:
        jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALG])
    except InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

# ─── in-memory data ────────────────────────────────────────────────────────
INBOX: "deque[Dict[str, Any]]" = deque(maxlen=1_000)   # replay buffer
SUBSCRIBERS: "set[asyncio.Queue]" = set()              # live client queues

# ─── Pydantic models ───────────────────────────────────────────────────────
class Message(BaseModel):
    role: str
    content: str
    timestamp: int

class Task(BaseModel):
    id: str
    state: str
    from_: str | None = None
    messages: list[Message]

# ─── FastAPI app & routes ──────────────────────────────────────────────────
app = FastAPI(title="Conclave-A2A-Agent")

@app.post("/tasks", status_code=202)
async def receive_task(task: Task, _: None = Depends(_verify_token)):
    data = task.model_dump()
    INBOX.append(data)
    # push to live subscribers
    for q in list(SUBSCRIBERS):
        await q.put(data)
    return {"status": "accepted", "buffer_len": len(INBOX)}

@app.get("/subscribe")
async def subscribe(
    _: None = Depends(_verify_token),
    accept_limit: int | None = Header(None, alias="Accept-Limit"),
):
    """SSE stream of tasks; honours optional Accept-Limit header."""

    async def event_generator() -> AsyncGenerator[str, None]:
        q: asyncio.Queue = asyncio.Queue()
        SUBSCRIBERS.add(q)
        sent = 0

        # replay buffer
        for item in list(INBOX):
            yield {"data": json.dumps(item)}
            sent += 1
            if accept_limit and sent >= accept_limit:
                break

        # live updates
        try:
            while not (accept_limit and sent >= accept_limit):
                msg = await q.get()
                yield {"data": json.dumps(msg)}
                sent += 1
        finally:
            SUBSCRIBERS.discard(q)
            yield {"event": "eof"}

    return EventSourceResponse(event_generator())

# helper for peer-chat test
def latest_message() -> str | None:
    return INBOX[-1]["messages"][0]["content"] if INBOX else None

@app.get("/.well-known/agent.json")
def agent_card():
    return {
        "a2a_version": A2A_VERSION,
        "name": "Conclave Local Agent",
        "id": str(uuid.uuid4()),
        "endpoint": os.getenv("A2A_ENDPOINT", "http://localhost:8001"),
        "skills": ["peer_chat", "subscribe"],
    }
