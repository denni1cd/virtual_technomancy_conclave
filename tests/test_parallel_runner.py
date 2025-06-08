"""Test parallel milestone scheduling with isolated workspaces."""

import os
from concurrent.futures import Future
from pathlib import Path
import pytest

from conclave.agents.parallel_runner import ParallelScheduler
from conclave.services.cost_ledger import CostCapExceeded

def test_sandbox_isolation(tmp_path, monkeypatch):
    """Test that each milestone gets its own isolated workspace."""
    scheduler = ParallelScheduler("dummy.yaml", root_ws=tmp_path)
    sandbox1 = scheduler._sandbox("m1")
    sandbox2 = scheduler._sandbox("m1")
    
    # Each sandbox should be unique
    assert sandbox1 != sandbox2
    assert sandbox1.name.startswith("m1_")
    assert sandbox2.name.startswith("m1_")

def test_parallel_execution(tmp_path, monkeypatch):
    """Test that milestones run in parallel when dependencies allow."""
    test_graph = {
        "nodes": [
            {"id": "m1", "goal": "first task", "deps": []},
            {"id": "m2", "goal": "second task", "deps": []},
        ]
    }

    # Mock graph loader
    class MockGraph:
        def __init__(self):
            self.nodes = test_graph["nodes"]
            self.running = set()
            self.complete = False
            
        def incomplete(self):
            return not self.complete
            
        def ready_nodes(self):
            return [n for n in self.nodes if n["id"] not in self.running]
            
        def mark_running(self, mid):
            self.running.add(mid)
            
        def mark_passed(self, mid):
            self.running.remove(mid)
            if len(self.running) == 0:
                self.complete = True
                
        def mark_failed(self, mid):
            self.running.remove(mid)

    monkeypatch.setattr("conclave.utils.milestone_graph.load_graph", 
                       lambda _: MockGraph())

    # Mock HighTechnomancer to avoid real execution
    class MockHigh:
        def __init__(self, goal): self.goal = goal
        def run_milestone(self): pass

    monkeypatch.setattr("conclave.agents.parallel_runner.HighTechnomancer", 
                       MockHigh)

    # Mock pytest.main to always pass
    monkeypatch.setattr("pytest.main", lambda *args, **kwargs: 0)

    scheduler = ParallelScheduler("dummy.yaml", root_ws=tmp_path)
    scheduler.run_all()

    # Both milestones should have created sandboxes
    sandboxes = list(tmp_path.parent.glob("m*_*"))
    assert len(sandboxes) >= 2

def test_cost_cap_handling(tmp_path, monkeypatch):
    """Test that cost cap exceptions are handled gracefully."""
    test_graph = {
        "nodes": [{"id": "expensive", "goal": "costly task", "deps": []}]
    }

    class MockGraph:
        def __init__(self):
            self.nodes = test_graph["nodes"]
            self.failed = set()
            
        def incomplete(self):
            return len(self.failed) == 0
            
        def ready_nodes(self):
            return self.nodes
            
        def mark_running(self, mid): pass
            
        def mark_failed(self, mid):
            self.failed.add(mid)

    monkeypatch.setattr("conclave.utils.milestone_graph.load_graph",
                       lambda _: MockGraph())

    # Mock HighTechnomancer to raise CostCapExceeded
    class ExpensiveHigh:
        def __init__(self, goal): self.goal = goal
        def run_milestone(self): 
            raise CostCapExceeded("Too expensive!")

    monkeypatch.setattr("conclave.agents.parallel_runner.HighTechnomancer",
                       ExpensiveHigh)

    scheduler = ParallelScheduler("dummy.yaml", root_ws=tmp_path)
    scheduler.run_all()  # Should complete without raising
