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
agent_var: contextvars.ContextVar[str] = contextvars.ContextVar("agent_id")

# ── exception ────────────────────────────────────────────────────────
class CostCapExceeded(RuntimeError):
    """Raised when an agent's projected or actual spend breaches its cap."""

# ── helpers ──────────────────────────────────────────────────────────
def _utc() -> str:
    return datetime.now().isoformat(timespec="seconds").replace("+00:00", "Z")


def _totals(agent_id: str) -> dict:
    """Aggregate ledger totals for *agent_id*."""
    tok = cost = 0
    if _LEDGER_FILE.exists():
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

    # atomic append
    with portalocker.Lock(_LEDGER_FILE, "a", timeout=5, encoding="utf-8") as fh:
        json_line = json.dumps(rec, separators=(",", ":"))
        fh.write(json_line + "\n")

    caps = ROLE_CAPS.get(role_name)
    if caps:
        run = _totals(agent_id)
        if run["cost"] > caps["dollar_cap"]:
            raise CostCapExceeded(
                f"{agent_id} exceeded {role_name} cap "
                f"(${run['cost']:.2f} / ${caps['dollar_cap']:.2f})"
            )

def log_for(role_name: str, tokens: int, cost: float):
    """
    Convenience wrapper that pulls agent_id from context.
    Falls back to role name if caller hasn't set self.agent_id
    """
    # fall back to role name if caller hasn't set self.agent_id
    agent_id = getattr(contextvars.ContextVar("agent_id"), "get", lambda: role_name)()
    log_usage(role_name, agent_id, tokens, cost)

def cost_guard(role_name: str, est_tokens: int = 0, est_cost: float = 0.0):
    """
    Wrap a function that *actually* calls the LLM.

    1.  Pre-check: projected spend  (est_cost) against remaining budget.
    2.  Execute fn → expect it returns (result, tokens_used, cost_used)
        *or* just `result` (in which case log nothing).
    3.  Post-log: raise if running total > cap.
    """
    cap = ROLE_CAPS[role_name]["dollar_cap"]
    def decorator(fn: Callable[..., Any]):
        if asyncio.iscoroutinefunction(fn):
            @functools.wraps(fn)
            async def async_wrapper(*args, **kwargs):
                agent_id = agent_var.get(role_name)
                spent = _totals(agent_id)["cost"]
                if spent + est_cost > cap:
                    raise CostCapExceeded(
                        f"{agent_id} would exceed ${cap:.2f} budget "
                        f"(spent {spent:.2f}, need {est_cost:.2f})"
                    )
                rv = await fn(*args, **kwargs)
                if isinstance(rv, tuple) and len(rv) == 3:
                    result, tokens, cost = rv
                    log_usage(role_name, agent_id, tokens, cost)
                else:
                    result = rv
                    tokens = cost = 0
                new_total = _totals(agent_id)["cost"]
                if new_total > cap:
                    raise CostCapExceeded(
                        f"{agent_id} exceeded ${cap:.2f} after call "
                        f"(now {new_total:.2f})"
                    )
                return result
            return async_wrapper
        else:
            @functools.wraps(fn)
            def sync_wrapper(*args, **kwargs):
                agent_id = agent_var.get(role_name)
                spent = _totals(agent_id)["cost"]
                if spent + est_cost > cap:
                    raise CostCapExceeded(
                        f"{agent_id} would exceed ${cap:.2f} budget "
                        f"(spent {spent:.2f}, need {est_cost:.2f})"
                    )
                rv = fn(*args, **kwargs)
                if isinstance(rv, tuple) and len(rv) == 3:
                    result, tokens, cost = rv
                    log_usage(role_name, agent_id, tokens, cost)
                else:
                    result = rv
                    tokens = cost = 0
                new_total = _totals(agent_id)["cost"]
                if new_total > cap:
                    raise CostCapExceeded(
                        f"{agent_id} exceeded ${cap:.2f} after call "
                        f"(now {new_total:.2f})"
                    )
                return result
            return sync_wrapper
    return decorator
