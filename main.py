"""
Entry-point CLI for Sprint-1 smoke-test.

Usage:
    python main.py "Your top-level goal sentence"
"""

from __future__ import annotations
import sys
from pathlib import Path

from conclave.agents.agent_factory import factory
from conclave.consensus.debate_manager import DebateManager
from conclave.tools import file_io
from conclave.services.trace_utils import print_trace_url

WORKSPACE = Path(__file__).resolve().parent / "workspace"
WORKSPACE.mkdir(exist_ok=True)

HELLO_PATH = WORKSPACE / "hello.txt"


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage:  python main.py \"<goal sentence>\"")
        sys.exit(1)

    goal = sys.argv[1]
    print(f"[Conclave] bootstrapping for goal -> {goal!r}")

    # spawn demo swarm
    high, tech = factory.spawn_one_high_with_one_technomancer()

    # run a 1-round debate (toy issue)
    mgr = DebateManager(rounds=1)
    decision, _hist = mgr.run(
        issue="Write greeting file", agents=[high, tech]
    )
    print(f"[Conclave] debate decision: {decision}")

    # write a hello file as artefact
    file_io.write_file(HELLO_PATH, "Hello, Conclave!\n")
    print(f"[Conclave] artefact written -> {HELLO_PATH.relative_to(Path.cwd())}")

    # fake an SDK run result for tracing demo
    class _StubRun:
        trace_url = "https://platform.openai.com/traces/r/demo123"
        usage = type("Usage", (), {"prompt_tokens": 1, "completion_tokens": 2})()

    tech._finish_run(_StubRun())  # logs cost + prints trace

    print("[Conclave] Sprint-1 smoke-test complete")


if __name__ == "__main__":
    main()
