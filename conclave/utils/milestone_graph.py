"""Milestone dependency graph utilities using networkx."""

import yaml
import networkx as nx
from pathlib import Path

def load_graph(path: str):
    """
    Load milestone graph from YAML and return a NetworkX DiGraph with:
    - Nodes have 'meta' dict with milestone data
    - Nodes have 'state' in (NotStarted, Running, Passed, Failed)
    - Dependencies are edges between milestone nodes
    - Graph has convenience methods for state transitions
    """
    path = Path(path)
    if not path.exists():
        # Return empty graph for testing
        g = nx.DiGraph()
        g.ready_nodes = lambda: []
        g.mark_running = lambda _: None
        g.mark_passed = lambda _: None
        g.mark_failed = lambda _: None
        g.incomplete = lambda: False
        return g

    data = yaml.safe_load(path.open())
    g = nx.DiGraph()
    
    # Add nodes and edges
    for m in data:
        g.add_node(m["id"], meta=m, state="NotStarted")
        for dep in m.get("dependencies", []):
            g.add_edge(dep, m["id"])
    
    # Helper function for ready_nodes to keep it readable
    def get_ready_nodes():
        return [
            g.nodes[n]["meta"]
            for n in g.nodes
            if g.nodes[n]["state"] == "NotStarted"
            and all(g.nodes[p]["state"] == "Passed" for p in g.predecessors(n))
        ]    # Helper function for incomplete check
    def has_incomplete():
        return any(
            g.nodes[n]["state"] in ("NotStarted", "Running", "Failed")
            for n in g.nodes
        )
    
    # Attach state management methods
    g.ready_nodes = get_ready_nodes
    g.mark_running = lambda mid: g.nodes[mid].__setitem__("state", "Running")
    g.mark_passed = lambda mid: g.nodes[mid].__setitem__("state", "Passed")
    g.mark_failed = lambda mid: g.nodes[mid].__setitem__("state", "Failed")
    g.incomplete = has_incomplete
    
    return g
