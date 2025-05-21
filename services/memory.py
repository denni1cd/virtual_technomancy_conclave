"""
memory.py: Simple JSONL short-term memory store.
"""
import json
from pathlib import Path
from typing import Any, Dict, List


class MemoryStore:
    """Simple JSONL short-term memory with file rotation."""

    def __init__(self, path: Path, max_size: int = 10000):
        """
        Args:
            path: Path to JSONL file.
            max_size: Max number of entries before rotating.
        """
        self.path = path
        self.max_size = max_size
        self._ensure_file()

    # --------------------------------------------------------------------- #
    # Internal helpers
    # --------------------------------------------------------------------- #
    def _ensure_file(self):
        """Ensure the memory file exists."""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self.path.write_text("", encoding="utf-8")

    def _read_lines(self) -> List[str]:
        """Read all non-empty lines from the memory file."""
        content = self.path.read_text(encoding="utf-8")
        return [line for line in content.splitlines() if line.strip()]

    # --------------------------------------------------------------------- #
    # Public API
    # --------------------------------------------------------------------- #
    def add(self, entry: Dict[str, Any]):
        """Add an entry to memory, rotating file if necessary."""
        lines = self._read_lines()
        if len(lines) >= self.max_size:
            backup = self.path.parent / f"{self.path.stem}.backup.jsonl"
            self.path.rename(backup)
            self.path.write_text("", encoding="utf-8")
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")

    def get_all(self) -> List[Dict[str, Any]]:
        """Retrieve all entries from memory."""
        lines = self._read_lines()
        return [json.loads(line) for line in lines]
