"""
Race-safe JSONL ledger with hard-cap enforcement.
"""

from __future__ import annotations

import json
import contextvars
from datetime import datetime, UTC
from importlib import resources
from pathlib import Path
from types import MappingProxyType
from typing import Any, Dict

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

# ── exception ────────────────────────────────────────────────────────
class CostCapExceeded(Exception):
    """Raised when an agent exceeds its USD or token cap."""

# ── helpers ──────────────────────────────────────────────────────────
def _utc() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")


def _totals(agent_id: str) -> dict:
    """Aggregate ledger totals for *agent_id*."""
    tok = usd = 0
    if _LEDGER_FILE.exists():
        with _LEDGER_FILE.open(encoding="utf-8") as fh:
            for ln in fh:
                rec = json.loads(ln)
                if rec["agent"] == agent_id:
                    tok += rec["tokens"]
                    usd += rec["cost"]
    return {"tokens": tok, "usd": usd}

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

    # atomic append
    with portalocker.Lock(_LEDGER_FILE, "a", timeout=5, encoding="utf-8") as fh:
        json_line = json.dumps(rec, separators=(",", ":"))
        fh.write(json_line + "\n")

    caps = _ROLE_CAPS.get(role_name)
    if caps:
        run = _totals(agent_id)
        if run["tokens"] > caps["tokens"] or run["usd"] > caps["usd"]:
            raise CostCapExceeded(
                f"{agent_id} exceeded {role_name} cap "
                f"({run['tokens']} tkn / ${run['usd']})"
            )

def log_for(role_name: str, tokens: int, cost: float):
    """
    Convenience wrapper that pulls agent_id from context.
    Falls back to role name if caller hasn't set self.agent_id
    """
    # fall back to role name if caller hasn't set self.agent_id
    agent_id = getattr(contextvars.ContextVar("agent_id"), "get", lambda: role_name)()
    log_usage(role_name, agent_id, tokens, cost)

def cost_guard(fn):               # in cost_ledger.py for now
    async def _inner(*a, **k):    # noqa: D401
        return await fn(*a, **k)
    return _inner
