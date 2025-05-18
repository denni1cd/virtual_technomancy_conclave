"""
test_bootstrap.py: Verifies ArchTechnomancer can draft milestones.
"""
import pytest

from agents.arch import ArchTechnomancer

def test_plan_milestones_non_empty():
    arch = ArchTechnomancer()
    milestones = arch.plan_milestones("a test goal")
    assert isinstance(milestones, list)
    assert len(milestones) > 0, "Milestone list should not be empty"