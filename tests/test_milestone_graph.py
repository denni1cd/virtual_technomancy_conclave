"""Test milestone graph implementation with networkx."""

import pytest
from pathlib import Path
from conclave.utils.milestone_graph import load_graph

def test_empty_graph_creation(tmp_path):
    """Test creating an empty graph when YAML doesn't exist."""
    graph = load_graph(tmp_path / "nonexistent.yaml")
    assert len(graph.nodes) == 0
    assert not graph.incomplete()
    assert graph.ready_nodes() == []

def test_graph_state_transitions(tmp_path):
    """Test state transitions in milestone graph."""
    yaml_path = tmp_path / "test.yaml"
    yaml_path.write_text("""
- id: auth
  goal: "Implement auth"
  dependencies: []
- id: api
  goal: "Build API"
  dependencies: [auth]
""")
    
    graph = load_graph(str(yaml_path))
    
    # Check initial state
    assert len(graph.nodes) == 2
    assert graph.incomplete()
    ready = graph.ready_nodes()
    assert len(ready) == 1
    assert ready[0]["id"] == "auth"
    
    # Test state transitions
    graph.mark_running("auth")
    assert len(graph.ready_nodes()) == 0  # No new nodes ready
    
    graph.mark_passed("auth")
    ready = graph.ready_nodes()
    assert len(ready) == 1  # api should now be ready
    assert ready[0]["id"] == "api"
    
    graph.mark_failed("api")  # Test failure state
    assert graph.incomplete()  # Still incomplete due to failure
    
def test_complex_dependencies(tmp_path):
    """Test more complex dependency chains."""
    yaml_path = tmp_path / "complex.yaml"
    yaml_path.write_text("""
- id: auth
  goal: "Auth system"
  dependencies: []
- id: api
  goal: "REST API"
  dependencies: [auth]
- id: ui
  goal: "Frontend UI"
  dependencies: [api]
- id: docs
  goal: "Documentation"
  dependencies: [api, ui]
""")
    
    graph = load_graph(str(yaml_path))
    
    # Only auth should be ready initially
    assert len(graph.ready_nodes()) == 1
    assert graph.ready_nodes()[0]["id"] == "auth"
    
    # Complete auth, api should be ready
    graph.mark_passed("auth")
    assert len(graph.ready_nodes()) == 1
    assert graph.ready_nodes()[0]["id"] == "api"
    
    # Complete api, ui should be ready
    graph.mark_passed("api")
    assert len(graph.ready_nodes()) == 1
    assert graph.ready_nodes()[0]["id"] == "ui"
    
    # Complete ui, docs should be ready
    graph.mark_passed("ui")
    assert len(graph.ready_nodes()) == 1
    assert graph.ready_nodes()[0]["id"] == "docs"
    
    # Complete docs, all done
    graph.mark_passed("docs")
    assert not graph.incomplete()
    assert len(graph.ready_nodes()) == 0

def test_cyclic_dependencies(tmp_path):
    """Test handling of cyclic dependencies."""
    yaml_path = tmp_path / "cyclic.yaml"
    yaml_path.write_text("""
- id: a
  goal: "Task A"
  dependencies: [b]
- id: b
  goal: "Task B"
  dependencies: [a]
""")
    
    graph = load_graph(str(yaml_path))
    
    # With cyclic deps, no nodes should be ready
    assert len(graph.ready_nodes()) == 0
    assert graph.incomplete()
