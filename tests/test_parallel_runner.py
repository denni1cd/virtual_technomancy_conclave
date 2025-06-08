"""Test parallel milestone scheduling with isolated workspaces."""

import os
from concurrent.futures import Future
from pathlib import Path
import pytest

from conclave.agents.parallel_runner import ParallelScheduler
from conclave.services.cost_ledger import CostCapExceeded

# Mock HighTechnomancer implementations
_executed_goals = []  # Global to track execution order

class MockBaseHigh:
    def __init__(self, goal): 
        self.goal = goal
        
    def run_milestone(self):
        sandbox = Path(os.environ["CONCLAVE_WORKSPACE"])
        (sandbox / "test.txt").write_text("Test content")
        (sandbox / "src").mkdir(exist_ok=True)
        (sandbox / "src" / "main.py").write_text("print('test')")

class ExpensiveHigh:
    def __init__(self, goal): 
        self.goal = goal
        
    def run_milestone(self): 
        raise CostCapExceeded("Too expensive!")

class DependencyMockHigh:
    def __init__(self, goal): 
        self.goal = goal
        
    def run_milestone(self):
        global _executed_goals
        sandbox = Path(os.environ["CONCLAVE_WORKSPACE"])
        _executed_goals.append(self.goal)
        (sandbox / "test.txt").write_text(f"Output from {self.goal}")

class ConflictMergeHigh:
    def __init__(self, goal):
        self.goal = goal
        
    def run_milestone(self):
        sandbox = Path(os.environ["CONCLAVE_WORKSPACE"])
        if "m1" in str(sandbox):
            (sandbox / "unique_first.txt").write_text("First output")
        elif "m2" in str(sandbox):
            (sandbox / "unique_second.txt").write_text("Second output")

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

    monkeypatch.setattr("conclave.agents.parallel_runner.HighTechnomancer", 
                       MockBaseHigh)

    monkeypatch.setattr("pytest.main", lambda *args, **kwargs: 0)

    workspace = tmp_path / "workspace"
    workspace.mkdir()
    scheduler = ParallelScheduler("dummy.yaml", root_ws=workspace)
    scheduler.run_all()

    # Both milestones should have created sandboxes
    sandboxes = list(workspace.parent.glob("m*_*"))
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

    monkeypatch.setattr("conclave.agents.parallel_runner.HighTechnomancer",
                       ExpensiveHigh)
                       
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    scheduler = ParallelScheduler("dummy.yaml", root_ws=workspace)
    scheduler.run_all()  # Should complete without raising

def test_dependency_order(tmp_path, monkeypatch):
    """Test that milestones respect dependency order."""
    # Reset global execution tracker
    global _executed_goals
    _executed_goals = []
    
    # Set up config
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    test_yaml = config_dir / "test.yaml"
    test_yaml.write_text("""
- id: auth_module
  goal: "Implement JWT-based authentication layer."
  dependencies: []

- id: user_profile
  goal: "Add user profile CRUD screens."
  dependencies: [auth_module]
""")

    monkeypatch.setattr("conclave.agents.parallel_runner.HighTechnomancer", 
                       DependencyMockHigh)
    
    monkeypatch.setattr("pytest.main", lambda *args, **kwargs: 0)
    
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    
    scheduler = ParallelScheduler(str(test_yaml), root_ws=workspace)
    scheduler.run_all()

    # Verify correct ordering
    auth_idx = _executed_goals.index("Implement JWT-based authentication layer.")
    profile_idx = _executed_goals.index("Add user profile CRUD screens.")
    assert auth_idx < profile_idx, "Dependencies not respected"

def test_sandbox_merge(tmp_path, monkeypatch):
    """Test that sandbox merging works correctly."""
    test_graph = {
        "nodes": [{"id": "m1", "goal": "merge test", "deps": []}]
    }

    class MockGraph:
        def __init__(self):
            self.nodes = test_graph["nodes"]
            self.complete = False
            
        def incomplete(self):
            return not self.complete
            
        def ready_nodes(self):
            return self.nodes if not self.complete else []
            
        def mark_running(self, _): pass
            
        def mark_passed(self, _):
            self.complete = True
            
        def mark_failed(self, _): pass

    monkeypatch.setattr("conclave.utils.milestone_graph.load_graph", 
                       lambda _: MockGraph())
            
    monkeypatch.setattr("conclave.agents.parallel_runner.HighTechnomancer",
                       MockBaseHigh)

    monkeypatch.setattr("pytest.main", lambda *args, **kwargs: 0)

    workspace = tmp_path / "workspace" 
    workspace.mkdir()
    scheduler = ParallelScheduler("dummy.yaml", root_ws=workspace)
    scheduler.run_all()

    # Verify files were merged to workspace
    assert (workspace / "test.txt").exists()
    assert (workspace / "test.txt").read_text() == "Test content"
    assert (workspace / "src" / "main.py").exists()
    assert (workspace / "src" / "main.py").read_text() == "print('test')"

def test_merge_conflicts(tmp_path, monkeypatch):
    """Test handling of conflicts during sandbox merges."""
    test_graph = {
        "nodes": [
            {"id": "m1", "goal": "first task", "deps": []},
            {"id": "m2", "goal": "second task", "deps": []}
        ]
    }

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

    monkeypatch.setattr("conclave.agents.parallel_runner.HighTechnomancer",
                       ConflictMergeHigh)

    monkeypatch.setattr("pytest.main", lambda *args, **kwargs: 0)

    workspace = tmp_path / "workspace"
    workspace.mkdir()

    scheduler = ParallelScheduler("dummy.yaml", root_ws=workspace)
    scheduler.run_all()

    # Both unique files should have been merged since they don't conflict
    assert (workspace / "unique_first.txt").exists()
    assert (workspace / "unique_second.txt").exists()
    assert (workspace / "unique_first.txt").read_text() == "First output"
    assert (workspace / "unique_second.txt").read_text() == "Second output"
