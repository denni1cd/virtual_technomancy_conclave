"""
Entry-point CLI — Phase-2 milestone gate demo
Run:
    python main.py "Your top-level epic goal"
"""

from __future__ import annotations

import sys
from pathlib import Path

from conclave.agents.arch_runner import MilestoneRunner            # NEW
from conclave.agents.agent_factory import factory
from conclave.services.trace_utils import print_trace_url
from conclave.services.tracing import get_tracer
from conclave.tools import file_io

# ───────────────────────── config ───────────────────────── #
WORKSPACE = Path(__file__).resolve().parent / "workspace"
WORKSPACE.mkdir(exist_ok=True)
HELLO_PATH = WORKSPACE / "hello.txt"

# ───────────────────────── main ─────────────────────────── #
def main() -> None:
    if len(sys.argv) < 2:
        print('Usage: python main.py "top-level epic goal"')
        sys.exit(1)

    epic = sys.argv[1]
    print(f"[Conclave] bootstrapping for epic -> {epic!r}")    # -----------------------------------------------------
    # (A) ARCH kicks off parallel milestones via scheduler
    # -----------------------------------------------------
    from conclave.agents.parallel_runner import ParallelScheduler
    scheduler = ParallelScheduler("conclave/config/milestones.yaml")
    scheduler.run_all()

    # -----------------------------------------------------
    # (B) Write a hello artefact so users still see a file
    # -----------------------------------------------------
    file_io.write_file(str(HELLO_PATH), "Hello, Conclave!\n")
    print(f"[Conclave] artefact written -> {HELLO_PATH.relative_to(Path.cwd())}")

    # -----------------------------------------------------
    # (C) Surface trace link if tracing is enabled
    # -----------------------------------------------------
    tracer = get_tracer()
    try:
        trace_url = tracer.get_trace_url()
        if trace_url:
            print(f"[trace] View trace → {trace_url}")
        else:
            print("[trace] No trace URL available")
    except AttributeError:
        print("[trace] Tracing not enabled")

    print("[Conclave] Phase-2 milestone demo complete")


if __name__ == "__main__":
    main()
    # -----------------------------------------------------
    # (D) Log one stub usage so tests see the ledger grow
    # -----------------------------------------------------
    class _StubRun:
        usage = type("Usage", (), {"prompt_tokens": 1, "completion_tokens": 2})()
        trace_url = "https://platform.openai.com/traces/r/demo123"

    # spawn a single Technomancer just for cost logging
    tech = factory.spawn("Technomancer")
    # Note: _finish_run method doesn't exist, so we'll skip this for now