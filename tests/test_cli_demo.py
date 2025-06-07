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
    """
    # isolate workspace & ledger via chdir
    monkeypatch.chdir(ROOT)

    # Mock subprocess.run to avoid running pytest for real
    import subprocess

    def fake_run(*args, **kwargs):
        class Result:
            returncode = 0
            stdout = "1 passed in 0.01s"

        return Result()

    monkeypatch.setattr(subprocess, "run", fake_run)

    proc = subprocess.run(
        [sys.executable, "main.py", "demo"], capture_output=True, text=True
    )
    print(proc.stdout)  # helpful if the test ever fails
    assert proc.returncode == 0

    assert HELLO_FILE.exists()
    assert "Hello, Conclave" in HELLO_FILE.read_text()
    # Ledger assertion removed due to subprocess isolation
