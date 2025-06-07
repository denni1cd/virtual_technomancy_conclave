"""
Race-safe JSONL ledger with hard-cap enforcement.
"""

from __future__ import annotations

import json
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

_TOKEN_PRICE = 1 / 100_000            # $10 / 1 M tokens

# ── exception ────────────────────────────────────────────────────────
class CostCapExceeded(Exception):
    """Raised when an agent exceeds its USD or token cap."""

# ── helpers ──────────────────────────────────────────────────────────
def _utc() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")


def _totals(agent: str) -> Dict[str, float]:
    """Aggregate ledger totals for *agent*."""
    tok = usd = 0
    if _LEDGER_FILE.exists():
        with _LEDGER_FILE.open(encoding="utf-8") as fh:
            for ln in fh:
                rec = json.loads(ln)
                if rec["agent"] == agent:
                    tok += rec["total_tokens"]
                    usd += rec["usd_est"]
    return {"tokens": tok, "usd": usd}

# ── public API ───────────────────────────────────────────────────────
def log_usage(
    *,
    agent: str,
    prompt: int,
    completion: int,
    total: int,
    role_name: str | None = None,
    extra: Dict[str, Any] | None = None,
) -> None:
    """
    Append one record; raise **CostCapExceeded** when a cap is breached.

    `role_name` left optional so legacy callers continue to work; when
    omitted it is stored as "Unknown" and no caps are enforced.
    """
    role_name = role_name or "Unknown"
    rec = {
        "ts": _utc(),
        "agent": agent,
        "role": role_name,
        "prompt_tokens": prompt,
        "completion_tokens": completion,
        "total_tokens": total,
        "usd_est": round(total * _TOKEN_PRICE, 6),
    }
    if extra:
        rec.update(extra)

    # atomic append
    with portalocker.Lock(_LEDGER_FILE, "a", timeout=5, encoding="utf-8") as fh:
        fh.write(json.dumps(rec, separators=(",", ":")) + "\n")

    caps = _ROLE_CAPS.get(role_name)
    if caps:
        run = _totals(agent)
        if run["tokens"] > caps["tokens"] or run["usd"] > caps["usd"]:
            raise CostCapExceeded(
                f"{agent} exceeded {role_name} cap "
                f"({run['tokens']} tkn / ${run['usd']})"
            )

def cost_guard(fn):               # in cost_ledger.py for now
    async def _inner(*a, **k):    # noqa: D401
        return await fn(*a, **k)
    return _inner
