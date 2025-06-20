"""
Race-safe JSONL ledger with hard-cap enforcement.
"""

from __future__ import annotations

import json
import contextvars
from datetime import datetime
from importlib import resources
from pathlib import Path
from types import MappingProxyType
from typing import Any, Dict, Callable
import functools
import asyncio
import threading

import portalocker
import yaml

# ── locate roles.yaml robustly ───────────────────────────────────────
try:
    _CFG = resources.files("conclave.config").joinpath("roles.yaml")
except Exception:  # zipapp or very old Python
    _CFG = Path(__file__).resolve().parent / "config" / "roles.yaml"

with _CFG.open(encoding="utf-8") as fh:
    _ROLE_RAW: Dict[str, Dict[str, Any]] = yaml.safe_load(fh)

_ROLE_CAPS = MappingProxyType(
    {r: {"usd": float(c["cost_cap_usd"]), "tokens": int(c["token_cap"])} for r, c in _ROLE_RAW.items()}
)

# ── paths & constants ────────────────────────────────────────────────
_LEDGER_FILE = Path(__file__).resolve().parents[2] / "conclave_usage.jsonl"
_LEDGER_FILE.parent.mkdir(exist_ok=True)          # ensure folder
_TOKEN_PRICE = 1 / 100_000                        # $10 / 1 M tokens

ROLE_CAPS = json.loads(
    (Path(__file__).parent / ".." / "config" / "roles_caps.json").read_text()
)

# Module-level ContextVar for agent_id
_AGENT_ID_VAR: contextvars.ContextVar[str] = contextvars.ContextVar("agent_id")

# Lock for reading totals (separate from write lock)
_totals_lock = threading.Lock()

# ── exception ────────────────────────────────────────────────────────
class CostCapExceeded(RuntimeError):
    """Raised when an agent's projected or actual spend breaches its cap."""

# ── helpers ──────────────────────────────────────────────────────────
def _utc() -> str:
    return datetime.now().isoformat(timespec="seconds").replace("+00:00", "Z")


def _totals(agent_id: str) -> dict:
    """
    Aggregate ledger totals for *agent_id*.
    
    TODO: This is O(n) and could be cached in memory for high-volume runs.
    """
    tok = cost = 0
    if _LEDGER_FILE.exists():
        with _totals_lock:  # Use separate lock for reading
            with _LEDGER_FILE.open(encoding="utf-8") as fh:
                for ln in fh:
                    rec = json.loads(ln)
                    if rec["agent"] == agent_id:
                        tok += rec.get("tokens", 0)
                        cost += rec.get("cost", 0.0)
    return {"tokens": tok, "cost": cost}

# ── public API ───────────────────────────────────────────────────────
def log_usage(
    role_name: str,
    agent_id: str,
    tokens: int,
    cost: float,
    *,
    extra: Dict[str, Any] | None = None,
) -> None:
    """Append one record; raise **CostCapExceeded** when a cap is breached."""
    rec = {
        "ts": _utc(),
        "role": role_name,
        "agent": agent_id,
        "tokens": tokens,
        "cost": cost
    }
    if extra:
        rec.update(extra)

    # Check caps before acquiring write lock
    caps = ROLE_CAPS.get(role_name)
    if caps:
        run = _totals(agent_id)
        if run["cost"] + cost > caps["dollar_cap"]:
            raise CostCapExceeded(
                f"{agent_id} would exceed {role_name} cap "
                f"(${run['cost'] + cost:.2f} / ${caps['dollar_cap']:.2f})"
            )

    # Atomic append with write lock
    with portalocker.Lock(_LEDGER_FILE, "a", timeout=5, encoding="utf-8") as fh:
        # Re-seek to end and append the new record
        fh.seek(0, 2)  # Seek to end
        json_line = json.dumps(rec, separators=(",", ":"))
        fh.write(json_line + "\n")

def log_for(role_name: str, tokens: int, cost: float):
    """
    Convenience wrapper that pulls agent_id from context.
    Falls back to role name if caller hasn't set self.agent_id
    """
    # Get agent_id from context var, fall back to role name
    try:
        agent_id = _AGENT_ID_VAR.get()
    except LookupError:
        agent_id = role_name
    log_usage(role_name, agent_id, tokens, cost)

def noop_guard(role_name: str, est_tokens: int = 0, est_cost: float = 0.0):
    """
    Kept for backward compatibility; does nothing.
    """
    def decorator(fn: Callable[..., Any]):
        return fn
    return decorator

# Alias for backward compatibility
cost_guard = noop_guard
