import json
import threading
from pathlib import Path

from conclave.services import cost_ledger

def _spam_logger(target: Path, agent_id: str):
    # call the public API ten times
    for _ in range(10):
        cost_ledger.log_usage(
            role_name="Unknown",
            agent_id=agent_id,
            tokens=33,
            cost=0.00033,
            extra={"task": "unit-test"},
        )

def test_parallel_logging(tmp_path):
    """Two threads append; resulting file has 20 valid JSON lines."""
    # point the ledger to temp dir for isolation
    cost_ledger._LEDGER_FILE = tmp_path / "ledger.jsonl"

    t1 = threading.Thread(target=_spam_logger, args=(tmp_path, "Tech-A"))
    t2 = threading.Thread(target=_spam_logger, args=(tmp_path, "Tech-B"))
    t1.start(); t2.start(); t1.join(); t2.join()

    lines = cost_ledger._LEDGER_FILE.read_text().splitlines()
    assert len(lines) == 20  # 10 lines per thread

    # every line is valid JSON and has expected keys
    for ln in lines:
        rec = json.loads(ln)
        assert {"ts", "role", "agent", "tokens", "cost"}.issubset(rec.keys())
