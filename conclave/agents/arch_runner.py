from __future__ import annotations
import subprocess, shutil, json
from pathlib import Path
from typing import List, Dict

from conclave.agents.agent_factory import factory
from conclave.services.cost_ledger import CostCapExceeded
from conclave.consensus.debate_manager import DebateManager
from conclave.services.tracing import get_tracer
# ensure HighTechnomancer subclasses gain .run_milestone()
import conclave.agents.high_behavior      # ← side-effect patch
import time, shutil

WORKSPACE = Path(__file__).parents[2] / "workspace"
FAILED_DIR = WORKSPACE.parent / "failed"      #  ◄── sibling, not child
FAILED_DIR.mkdir(exist_ok=True)

class MilestoneRunner:
    def __init__(self, milestones: List[Dict[str, str]]) -> None:
        self.milestones = milestones
        self.idx = 0

    # --------------------------------------------------------------
    def _run_tests(self) -> bool:
        """Run pytest in workspace; treat 'no tests' as pass."""
        result = subprocess.run(
            ["pytest", "-q", str(WORKSPACE)],
            cwd=WORKSPACE.parent,
            capture_output=True,
            text=True,
        )
        # ----------------------------------------------------------------
        if "no tests ran" in result.stdout.lower():
            return True                     # consider empty suite a pass
        # ----------------------------------------------------------------
        return result.returncode == 0
    
    def _archive_fail(self) -> None:
        ts = time.strftime("%Y%m%d_%H%M%S")
        dest = FAILED_DIR / f"milestone_{self.idx}_{ts}"
        dest.mkdir(parents=True, exist_ok=True)
        # copy contents, then clear workspace
        for item in WORKSPACE.iterdir():
            target = dest / item.name
            if item.is_dir():
                shutil.copytree(item, target, dirs_exist_ok=True)
                shutil.rmtree(item, ignore_errors=True)
            else:
                shutil.copy2(item, target)
                item.unlink(missing_ok=True)


    # --------------------------------------------------------------
    def run_next(self) -> str:
        if self.idx >= len(self.milestones):
            print("All milestones complete")
            return "done"

        milestone = self.milestones[self.idx]["goal"]
        print(f"[Arch] running milestone {self.idx}: {milestone}")

        # Start tracing root span for this milestone
        tracer = get_tracer()
        with tracer.root_span(
            project_name=f"milestone_{self.idx}",
            metadata={
                "milestone_goal": milestone,
                "milestone_index": self.idx,
                "role": "ArchTechnomancer"
            }
        ):
            high = factory.spawn("HighTechnomancer")
            try:
                decision = high.run_milestone(issue=milestone, tech_count=3)
                print(f"[Arch] High decision: {decision}")

                if not self._run_tests():
                    raise AssertionError("integration tests failed")

                self.idx += 1
                return "passed"

            except (CostCapExceeded, AssertionError) as exc:
                print(f"[Arch] milestone failed: {exc}")
                self._archive_fail()
                # re-plan: inject lessons-learned into new High
                return "failed"
