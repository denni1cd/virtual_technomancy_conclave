"""
Tiny A2A-compatible server for local peer-chat tests & demos.

Spin it with:  uvicorn conclave.services.a2a_server:app --port 8001
"""

from __future__ import annotations
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uuid, time, os, json
from pathlib import Path

app = FastAPI(title="Conclave-A2A-Agent")

# ---- in-memory store -------------------------------------------------- #
MESSAGES = []  # list[dict]


# ---- models ----------------------------------------------------------- #
class Message(BaseModel):
    role: str
    content: str
    timestamp: int


class Task(BaseModel):
    id: str
    from_: str = "unknown"  # 'from' is reserved in Python
    state: str
    messages: list[Message]


# ---- endpoints -------------------------------------------------------- #
@app.post("/tasks", status_code=202)
def receive_task(task: Task):
    MESSAGES.append(task.model_dump())
    return {"status": "accepted", "count": len(MESSAGES)}


# Required by the A2A discovery spec  :contentReference[oaicite:4]{index=4}
@app.get("/.well-known/agent.json")
def agent_card():
    return {
        "a2a_version": "0.1.0",
        "name": "Conclave Local Agent",
        "id": str(uuid.uuid4()),
        "endpoint": os.getenv("A2A_ENDPOINT", "http://localhost:8001"),
        "skills": ["peer_chat"],
    }


# helper for tests
def latest_message() -> str | None:
    if MESSAGES:
        return MESSAGES[-1]["messages"][0]["content"]
    return None
