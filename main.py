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
from conclave.tools import file_io

# ───────────────────────── config ───────────────────────── #
WORKSPACE = Path(__file__).resolve().parent / "workspace"
WORKSPACE.mkdir(exist_ok=True)
HELLO_PATH = WORKSPACE / "hello.txt"

# Two toy milestones so you can see the PASS → DONE flow.
MILESTONES = [
    {"goal": "Write greeting file"},
    {"goal": "Add logging stub"},
]

# ───────────────────────── main ─────────────────────────── #
def main() -> None:
    if len(sys.argv) < 2:
        print('Usage: python main.py "top-level epic goal"')
        sys.exit(1)

    epic = sys.argv[1]
    print(f"[Conclave] bootstrapping for epic -> {epic!r}")

    # -----------------------------------------------------
    # (A) ARCH kicks off sequential milestones
    # -----------------------------------------------------
    arch = factory.spawn("ArchTechnomancer")
    runner = MilestoneRunner(MILESTONES)

    while runner.run_next() != "done":
        continue

    # -----------------------------------------------------
    # (B) Write a hello artefact so users still see a file
    # -----------------------------------------------------
    file_io.write_file(HELLO_PATH, "Hello, Conclave!\n")
    print(f"[Conclave] artefact written -> {HELLO_PATH.relative_to(Path.cwd())}")

    # -----------------------------------------------------
    # (C) Surface a fake trace link (replace with real Runner.run)
    # -----------------------------------------------------
    class _StubRun:
        trace_url = "https://platform.openai.com/traces/r/demo123"
        usage = type("Usage", (), {"prompt_tokens": 1, "completion_tokens": 2})()

    print_trace_url(_StubRun())

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
    tech._finish_run(_StubRun())           # writes ledger line