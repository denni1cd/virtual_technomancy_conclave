from pathlib import Path
import pytest
from conclave.agents import arch_runner
from conclave.agents.arch_runner import MilestoneRunner


@pytest.mark.timeout(5)  # Force test to timeout after 5 seconds
def test_failure_replan(tmp_path, monkeypatch):
    """
    Patch Arch's workspace/failed paths into a temp dir, force the first
    test run to fail and the second to pass, and check that a failure
    archive was created.
    """
    # Point Arch at temporary folders
    monkeypatch.setattr(arch_runner, "WORKSPACE", tmp_path / "ws")
    monkeypatch.setattr(arch_runner, "FAILED_DIR", tmp_path / "failed")
    arch_runner.WORKSPACE.mkdir(parents=True, exist_ok=True)

    milestones = [{"goal": "fail-now"}]

    # Mock think() method on HighTechnomancer to return immediately
    def mock_run_milestone(self, issue, tech_count):
        return "mock decision"

    from conclave.agents.high_behavior import _attach_to

    for cls in arch_runner.factory.registry.values():
        if "HighTechnomancer" in cls.__name__:
            monkeypatch.setattr(cls, "run_milestone", mock_run_milestone)

    # Mock subprocess.run to avoid real pytest calls
    def mock_run_tests(self):
        # First call fails, second passes
        calls["n"] += 1
        return calls["n"] == 2

    calls = {"n": 0}
    monkeypatch.setattr(MilestoneRunner, "_run_tests", mock_run_tests)

    runner = MilestoneRunner(milestones)
    assert runner.run_next() == "failed"
    assert runner.run_next() == "passed"
    assert (tmp_path / "failed").exists()
