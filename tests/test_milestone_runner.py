from pathlib import Path

from conclave.agents import arch_runner
from conclave.agents.arch_runner import MilestoneRunner


def test_failure_replan(tmp_path, monkeypatch):
    """
    Patch Arch’s workspace/failed paths into a temp dir, force the first
    test run to fail and the second to pass, and check that a failure
    archive was created.
    """
    # Point Arch at temporary folders
    monkeypatch.setattr(arch_runner, "WORKSPACE", tmp_path / "ws")
    monkeypatch.setattr(arch_runner, "FAILED_DIR", tmp_path / "failed")
    arch_runner.WORKSPACE.mkdir(parents=True, exist_ok=True)

    milestones = [{"goal": "fail-now"}]

    # Make _run_tests fail once, then succeed
    calls = {"n": 0}

    def fake_tests(self):
        calls["n"] += 1
        return calls["n"] == 2  # pass on second call

    monkeypatch.setattr(
        arch_runner.MilestoneRunner,
        "_run_tests",
        fake_tests,
        raising=True,
    )

    runner = MilestoneRunner(milestones)
    assert runner.run_next() == "failed"
    assert runner.run_next() == "passed"
    assert (tmp_path / "failed").exists()
