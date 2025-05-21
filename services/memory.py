# SPDX-License-Identifier: MIT
"""
services.memory
~~~~~~~~~~~~~~~
Append-only JSONL short-term memory store with optional rotation.

Features
--------
* `MemoryStore.for_agent(name, scope)` → returns/creates a per-agent file
  at  ~/.conclave_memory/<name>_<scope>.jsonl   (or $CONCLAVE_HOME override)
* Automatic file rotation after `max_size` lines (moved to backups/).
* `fetch_last(k)` convenience for recent context.
* Optional thread-safe writes if the `portalocker` package is present.

Environment
-----------
CONCLAVE_HOME — override the base directory (defaults to the user’s HOME).
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, List

# Optional cross-platform advisory lock
try:
    import portalocker  # type: ignore
except ModuleNotFoundError:  # pragma: no cover
    portalocker = None  # type: ignore

_BASE_DIR: Path = (
    Path(os.getenv("CONCLAVE_HOME", Path.home())) / ".conclave_memory"
)


class MemoryStore:
    """Append-only JSONL memory file with simple rotation."""

    # ------------------------------------------------------------------ #
    # Construction helpers
    # ------------------------------------------------------------------ #
    def __init__(self, path: Path, max_size: int = 10_000):
        """
        Parameters
        ----------
        path : Path
            Full path to the JSONL file.
        max_size : int, optional
            Number of lines before the file is rotated (default 10 000).
        """
        self.path = path
        self.max_size = max_size
        self._ensure_file()

    @classmethod
    def for_agent(cls, name: str, scope: str = "epic") -> "MemoryStore":
        """Quick factory that builds a scoped file for an agent."""
        file_path = _BASE_DIR / f"{name}_{scope}.jsonl"
        return cls(file_path)

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #
    def append(self, role: str, message: str) -> None:
        """Add a JSONL entry to the memory file."""
        self._rotate_if_needed()
        entry = {"role": role, "message": message}
        with self.path.open("a", encoding="utf-8") as f:
            if portalocker:
                portalocker.lock(f, portalocker.LOCK_EX)
            f.write(json.dumps(entry) + "\n")

    def fetch_last(self, k: int = 10) -> List[Dict[str, Any]]:
        """Return the *k* most-recent memory entries."""
        return [json.loads(line) for line in self._read_lines()[-k:]]

    # ------------------------------------------------------------------ #
    # Internal helpers
    # ------------------------------------------------------------------ #
    def _ensure_file(self) -> None:
        """Create directory and empty file if they don’t exist."""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.touch(exist_ok=True)

    def _read_lines(self) -> List[str]:
        """Return all non-blank lines from the JSONL file."""
        return [
            line
            for line in self.path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]

    def _rotate_if_needed(self) -> None:
        """Rotate the file when `max_size` lines is exceeded."""
        if len(self._read_lines()) < self.max_size:
            return
        backup_dir = self.path.parent / "backups"
        backup_dir.mkdir(exist_ok=True)
        backup_file = backup_dir / f"{self.path.stem}.backup.jsonl"
        self.path.rename(backup_file)
        self.path.write_text("", encoding="utf-8")
