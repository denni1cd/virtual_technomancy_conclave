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
from contextlib import contextmanager

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

# ── exception ────────────────────────────────────────────────────────
class CostCapExceeded(RuntimeError):
    """Raised when an agent's projected or actual spend breaches its cap."""

# ── lock management ──────────────────────────────────────────────────
@contextmanager
def ledger_lock(shared: bool = False):
    """
    Context manager for ledger locking.
    
    Args:
        shared: If True, use shared lock (for reads). If False, use exclusive lock (for writes).
    """
    lock_flags = portalocker.LOCK_SH if shared else portalocker.LOCK_EX
    # Ensure the file exists before locking
    if not _LEDGER_FILE.exists():
        _LEDGER_FILE.touch()
    with portalocker.Lock(_LEDGER_FILE, "a+", flags=lock_flags) as fh:
        yield fh

# ── helpers ──────────────────────────────────────────────────────────
def _utc() -> str:
    return datetime.now().isoformat(timespec="seconds").replace("+00:00", "Z")


def _totals(agent_id: str) -> dict:
    """
    Aggregate ledger totals for *agent_id*.
    
    Uses shared lock to prevent race conditions during reads.
    """
    tok = cost = 0
    if _LEDGER_FILE.exists():
        with ledger_lock(shared=True):
            with _LEDGER_FILE.open(encoding="utf-8") as fh:
                for ln in fh:
                    rec = json.loads(ln)
                    if rec["agent"] == agent_id:
                        tok += rec.get("tokens", 0)
                        cost += rec.get("cost", 0.0)
    return {"tokens": tok, "cost": cost}


def log_and_check(role_name: str, agent_id: str, tokens: int, cost: float, *, extra: Dict[str, Any] | None = None) -> None:
    """
    Atomic log and check operation.
    
    This function:
    1. Opens exclusive lock
    2. Calculates totals (including the new record)
    3. Raises CostCapExceeded if over cap
    4. Appends the new record if under cap
    
    This prevents race conditions where two agents could both read stale totals
    and think they're under budget, then overspend.
    """
    rec = {
        "ts": _utc(),
        "role": role_name,
        "agent": agent_id,
        "tokens": tokens,
        "cost": cost
    }
    if extra:
        rec.update(extra)

    # Check caps with exclusive lock to prevent race conditions
    caps = ROLE_CAPS.get(role_name)
    if caps:
        with ledger_lock(shared=False) as fh:  # Exclusive lock for atomic operation
            fh.seek(0)
            total_tok = total_cost = 0
            lines = fh.readlines()
            for ln in lines:
                try:
                    record = json.loads(ln)
                except Exception:
                    continue
                if record["agent"] == agent_id:
                    total_tok += record.get("tokens", 0)
                    total_cost += record.get("cost", 0.0)
            # Add the new record's tokens and cost
            total_tok += tokens
            total_cost += cost
            if total_cost > caps.get("dollar_cap", caps.get("usd", 0)):
                raise CostCapExceeded(
                    f"{agent_id} would exceed {role_name} cap "
                    f"(${total_cost:.2f} / ${caps.get('dollar_cap', caps.get('usd', 0)):.2f})"
                )
            # Only write if under cap
            fh.seek(0, 2)  # Move to end for appending
            json_line = json.dumps(rec, separators=(",", ":"))
            fh.write(json_line + "\n")
            fh.flush()
    else:
        # No caps defined, just append
        with ledger_lock(shared=False) as fh:
            fh.seek(0, 2)
            json_line = json.dumps(rec, separators=(",", ":"))
            fh.write(json_line + "\n")
            fh.flush()
    
    # Add tracing event for cost
    try:
        from .tracing import get_tracer
        tracer = get_tracer()
        tracer.add_event(
            "cost",
            {
                "role": role_name,
                "agent": agent_id,
                "operation": extra.get("operation", "unknown") if extra else "unknown",
                "total_tokens": total_tok if caps else tokens,
                "total_cost": total_cost if caps else cost
            },
            cost_usd=cost,
            tokens=tokens
        )
    except Exception as e:
        # Fail open - tracing errors shouldn't break cost logging
        import logging
        logging.debug(f"Failed to add cost trace event: {e}")

# ── public API ───────────────────────────────────────────────────────
def log_usage(
    role_name: str,
    agent_id: str,
    tokens: int,
    cost: float,
    *,
    extra: Dict[str, Any] | None = None,
) -> None:
    """
    Append one record; raise **CostCapExceeded** when a cap is breached.
    
    This is now a wrapper around log_and_check for backward compatibility.
    """
    log_and_check(role_name, agent_id, tokens, cost, extra=extra)

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
