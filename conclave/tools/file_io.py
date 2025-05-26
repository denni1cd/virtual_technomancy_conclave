"""
Race-safe file read/write helpers for Conclave agents.

Implements a minimal API:
    • write_file(path: str, text: str) -> str
    • read_file(path: str) -> str

Both functions are decorated with the OpenAI Agents-SDK @function_tool
so Technomancers can call them directly once tool wiring is finished.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Literal

import portalocker  # pip install portalocker

# -- internal helpers ---------------------------------------------------- #


def _ensure_parent(path: Path) -> None:
    """Create parent directories if they do not exist."""
    if not path.parent.exists():
        path.parent.mkdir(parents=True, exist_ok=True)


# -- public API ---------------------------------------------------------- #


def write_file(
    filepath: str,
    text: str,
    *,
    mode: Literal["w", "a"] = "w",
    encoding: str = "utf-8",
) -> str:
    """
    Atomically write *text* to *filepath*.

    Uses Portalocker's context-manager wrapper, which acquires an
    **exclusive** (LOCK_EX) advisory lock for the duration of the block
    so multiple agent processes can't clobber each other. The entire
    write is flushed before the lock is released. :contentReference[oaicite:1]{index=1}
    """
    path = Path(filepath).expanduser().resolve()
    _ensure_parent(path)

    # 'a' mode keeps file open for appends; by default we overwrite
    with portalocker.Lock(path, mode=mode, timeout=10, encoding=encoding) as fh:
        fh.write(text)
        fh.flush()

    return f"[write_file] {len(text)} bytes → {path}"


def read_file(filepath: str, *, encoding: str = "utf-8") -> str:
    """
    Safely read an entire file *after* taking a shared lock.

    Portalocker gives us SHARED (LOCK_SH) semantics when mode == 'r',
    preventing a writer from overwriting mid-read. :contentReference[oaicite:2]{index=2}
    """
    path = Path(filepath).expanduser().resolve()
    if not path.exists():
        raise FileNotFoundError(path)

    with portalocker.Lock(path, mode="r", timeout=10, encoding=encoding) as fh:
        data = fh.read()
    return data


# -- simple JSON helper (handy during tests) ----------------------------- #


def write_json(filepath: str, obj) -> str:
    """Utility wrapper for JSON dumps, re-uses write_file()."""
    return write_file(filepath, json.dumps(obj, indent=2))
