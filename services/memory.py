# SPDX-License-Identifier: MIT
"""
services.memory
Append-only JSONL memory store with optional rotation.

Env:
    CONCLAVE_HOME – override base dir (defaults to ~/.conclave_memory)
"""
import json, os
from pathlib import Path
from typing import Any, Dict, List
try:
    import portalocker  # optional runtime safety
except ImportError:  # pragma: no cover
    portalocker = None

_BASE = Path(os.getenv("CONCLAVE_HOME", Path.home())) / ".conclave_memory"

class MemoryStore:
    def __init__(self, path: Path, max_size: int = 10_000):
        self.path = path
        self.max_size = max_size
        self._ensure_file()

    # ---------- convenience ----------
    @classmethod
    def for_agent(cls, name: str, scope: str = "epic") -> "MemoryStore":
        file = _BASE / f"{name}_{scope}.jsonl"
        return cls(file)

    # ---------- public ---------------
    def append(self, role: str, message: str) -> None:
        self._rotate_if_needed()
        with self.path.open("a", encoding="utf-8") as f:
            if portalocker:  # cross-platform advisory lock :contentReference[oaicite:5]{index=5}
                portalocker.lock(f, portalocker.LOCK_EX)
            f.write(json.dumps({"role": role, "message": message}) + "\n")

    def fetch_last(self, k: int = 10) -> List[Dict[str, Any]]:
        return [json.loads(l) for l in self._read_lines()[-k:]]

    def _rotate_if_needed(self):
        if len(self._read_lines()) >= self.max_size:
            backup_dir = self.path.parent / "backups"
            backup_dir.mkdir(exist_ok=True)
            self.path.rename(backup_dir / f"{self.path.stem}.backup.jsonl")
            self.path.write_text("", encoding="utf-8")

    # ---------- internals ------------
    def _ensure_file(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)  # mkdir -p style :contentReference[oaicite:6]{index=6}
        self.path.touch(exist_ok=True)

    def _read_lines(self) -> List[str]:
        return [l for l in self.path.read_text(encoding="utf-8").splitlines() if l.strip()]
