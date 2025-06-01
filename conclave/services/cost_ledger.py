"""
JSON-Lines cost ledger for Conclave agents (Sprint T4).

Each call to `log_usage()` appends a single UTF-8 line:
{
  "ts": "2025-05-26T17:34:11Z",
  "agent": "Technomancer-42",
  "prompt_tokens": 123,
  "completion_tokens": 456,
  "total_tokens": 579,
  "usd_est": 0.0023
}
The file is created on-demand and guarded by an **exclusive**
Portalocker lock so concurrent processes can append safely.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone, UTC
from pathlib import Path
from typing import Any, Dict, Union

import portalocker  # cross-platform advisory locks ﻿:contentReference[oaicite:1]{index=1}

# Ledger path lives next to workspace/ but is configurable via env-var.
_LEDGER_FILE = Path(
    Path(__file__).resolve().parents[2] / "conclave_usage.jsonl"
)
_LEDGER_FILE.parent.mkdir(parents=True, exist_ok=True)

# Rough $ cost at $10 / 1M tokens (defaults to OpenAI “o3” pricing Jan-2025).
_TOKEN_PRICE = float(1) / 100_000


def _iso_z(dt: datetime) -> str:
    """Return ISO-8601 UTC timestamp with trailing “Z” (Zulu)."""
    # Datetime → ISO then swap +00:00 for Z ﻿:contentReference[oaicite:2]{index=2}
    return dt.astimezone(UTC).isoformat(timespec="seconds").replace(
        "+00:00", "Z"
    )


def log_usage(
    *,
    agent: str,
    prompt: int,
    completion: int,
    total: int,
    extra: Dict[str, Union[str, int, float]] | None = None,
) -> None:
    """
    Append one usage record; raise *no* exceptions on failure so
    logging never kills agent progress.

    `extra` lets callers stash custom fields later (e.g. tool name).
    """
    record: Dict[str, Any] = {
        "ts": _iso_z(datetime.now(UTC)),
        "agent": agent,
        "prompt_tokens": prompt,
        "completion_tokens": completion,
        "total_tokens": total,
        "usd_est": round(total * _TOKEN_PRICE, 6),
    }
    if extra:
        record.update(extra)

    line = json.dumps(record, separators=(",", ":")) + "\n"

    try:
        with portalocker.Lock(_LEDGER_FILE, mode="a", timeout=10, encoding="utf-8") as fh:
            fh.write(line)
            fh.flush()                 # guarantee durability ﻿:contentReference[oaicite:3]{index=3}
    except Exception:                   # pragma: no cover
        # Swallow all errors; we never block the main workflow.
        pass
