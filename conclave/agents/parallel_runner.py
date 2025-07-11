# -*- coding: utf-8 -*-
"""
ParallelScheduler – launch HighTechnomancers whose dependencies are met,
each in an isolated workspace branch, and merge when they pass.
"""

from concurrent.futures import (
    ThreadPoolExecutor,
    Future,
    wait,
    FIRST_COMPLETED,
)
from pathlib import Path
import shutil
import os
import uuid

from .high_technomancer import HighTechnomancer
from ..services.cost_ledger import CostCapExceeded
from ..utils import milestone_graph

MAX_PARALLEL = 4  # configurable via env


class ParallelScheduler:
    def __init__(self, milestones_yaml: str, root_ws: str | Path = "workspace"):
        # Use module reference so monkeypatching milestone_graph.load_graph works
        self.graph = milestone_graph.load_graph(milestones_yaml)
        self.root_ws = Path(root_ws)
        self.executor = ThreadPoolExecutor(max_workers=MAX_PARALLEL)
        self.sandboxes: list[Path] = []  # kept for diagnostics
        self._scheduled: set[str] = set()  # track milestones already enqueued

    # ------------------------------------------------------------------ #
    # helpers
    # ------------------------------------------------------------------ #
    def _sandbox(self, mid: str) -> Path:
        """Clone the root workspace into a uniquely-named directory."""
        sb = self.root_ws.parent / f"{mid}_{uuid.uuid4().hex[:6]}"
        shutil.copytree(self.root_ws, sb, dirs_exist_ok=True)
        self.sandboxes.append(sb)
        return sb

    def _run_high(self, milestone: dict) -> tuple[str, bool, Path]:
        """Worker thread – execute HighTechnomancer inside its sandbox."""
        mid = milestone["id"]
        ws = self._sandbox(mid)

        # Point file-IO helpers at this sandbox
        os.environ["CONCLAVE_WORKSPACE"] = str(ws)

        high = HighTechnomancer(goal=milestone["goal"])
        try:
            high.run_milestone()
            passed = True                       # <- simplest pass/fail flag
        except CostCapExceeded:
            passed = False
        return mid, passed, ws

    # ------------------------------------------------------------------ #
    # public API
    # ------------------------------------------------------------------ #
    def run_all(self) -> None:
        """Execute the whole milestone graph (possibly in parallel)."""
        futures: dict[Future, str] = {}
        print(f"[ParallelScheduler] Starting execution of {len(self.graph.nodes)} milestones")

        while self.graph.incomplete() or futures:
            # 1️⃣ enqueue each milestone whose dependencies are satisfied
            ready = self.graph.ready_nodes()
            print(f"[ParallelScheduler] Ready milestones: {[m['id'] for m in ready]}")
            
            for m in ready:
                mid = m["id"]
                if mid in self._scheduled:
                    continue
                print(f"[ParallelScheduler] Scheduling milestone: {mid} - {m['goal']}")
                fut = self.executor.submit(self._run_high, m)
                futures[fut] = mid
                self._scheduled.add(mid)
                self.graph.mark_running(mid)

            if not futures:  # graph finished
                print("[ParallelScheduler] No more milestones to schedule")
                break

            # 2️⃣ wait until *one* future completes
            done, _ = wait(list(futures.keys()), return_when=FIRST_COMPLETED)

            # 3️⃣ process completed future(s)
            for fut in done:
                mid = futures.pop(fut)
                try:
                    _mid, ok, ws = fut.result()
                    print(f"[ParallelScheduler] Milestone {mid} completed: {'PASSED' if ok else 'FAILED'}")
                except Exception as e:
                    print(f"[ParallelScheduler] Milestone {mid} failed with exception: {e}")
                    ok, ws = False, None  # defensive: never crash loop

                if ok and ws:
                    try:
                        self._merge(ws)
                        self.graph.mark_passed(mid)
                        print(f"[ParallelScheduler] Milestone {mid} merged successfully")
                    except RuntimeError as e:
                        print(f"[ParallelScheduler] Milestone {mid} merge failed: {e}")
                        self.graph.mark_failed(mid)
                else:
                    self.graph.mark_failed(mid)

        print("[ParallelScheduler] All milestones completed")
        self.executor.shutdown(wait=True)

    # ------------------------------------------------------------------ #
    # merge helper
    # ------------------------------------------------------------------ #
    def _merge(self, sandbox: Path) -> None:
        """Copy files from sandbox → root workspace (sandbox wins)."""
        # Files to exclude from merge (placeholders, etc.)
        exclude_files = {"hello.txt", "test_placeholder.py", "__pycache__"}
        
        for file in sandbox.rglob("*"):
            try:
                rel = file.relative_to(sandbox)
            except ValueError:
                continue
            
            # Skip excluded files and directories
            if any(excluded in rel.parts for excluded in exclude_files):
                continue

            dst = self.root_ws / rel
            if file.is_dir():
                dst.mkdir(parents=True, exist_ok=True)
                continue

            if dst.exists():  # conflict detection
                raise RuntimeError(f"Merge conflict on {rel}")

            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(file, dst)
