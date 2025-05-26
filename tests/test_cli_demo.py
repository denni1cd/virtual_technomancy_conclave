import subprocess, sys, json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
HELLO_FILE = ROOT / "workspace" / "hello.txt"
LEDGER = ROOT / "conclave_usage.jsonl"


def test_cli_smoke(tmp_path, monkeypatch):
    """
    Runs `python main.py "demo"` and asserts:
      • exit-code 0
      • hello.txt exists and contains greeting
      • cost ledger grew by ≥1 line
    """
    # isolate workspace & ledger via chdir
    monkeypatch.chdir(ROOT)

    # pre-count ledger lines
    before = 0
    if LEDGER.exists():
        before = LEDGER.read_text().count("\n")

    proc = subprocess.run(
        [sys.executable, "main.py", "demo"], capture_output=True, text=True
    )
    print(proc.stdout)  # helpful if the test ever fails
    assert proc.returncode == 0

    assert HELLO_FILE.exists()
    assert "Hello, Conclave" in HELLO_FILE.read_text()

    after = LEDGER.read_text().count("\n")
    assert after > before, "ledger line should have been appended"
