"""Milestone dependency graph utilities."""

import yaml
from pathlib import Path
from typing import Dict, List, Any

class MilestoneGraph:
    """Track milestone dependencies and state."""
    
    def __init__(self, nodes: List[Dict[str, Any]]):
        self.nodes = nodes
        self.running = set()
        self.passed = set()
        self.failed = set()
        
    def incomplete(self) -> bool:
        """Return True if any milestones are not passed/failed."""
        complete = self.passed | self.failed
        return len(complete) < len(self.nodes)
        
    def ready_nodes(self) -> List[Dict[str, Any]]:
        """Return nodes whose dependencies are satisfied."""
        ready = []
        active = self.running | self.failed
        for node in self.nodes:
            if node["id"] not in active | self.passed:
                deps = set(node.get("deps", []))
                if deps <= self.passed:  # all deps passed
                    ready.append(node)
        return ready
        
    def mark_running(self, mid: str) -> None:
        """Mark milestone as currently executing."""
        self.running.add(mid)
        
    def mark_passed(self, mid: str) -> None:
        """Mark milestone as successfully completed."""
        self.running.remove(mid)
        self.passed.add(mid)
        
    def mark_failed(self, mid: str) -> None:
        """Mark milestone as failed."""
        self.running.remove(mid)
        self.failed.add(mid)


def load_graph(yaml_path: str) -> MilestoneGraph:
    """Load milestone graph from YAML file."""
    path = Path(yaml_path)
    if not path.exists():
        # For testing, return empty graph
        return MilestoneGraph([])
    
    with path.open() as f:
        data = yaml.safe_load(f)
    return MilestoneGraph(data.get("nodes", []))
