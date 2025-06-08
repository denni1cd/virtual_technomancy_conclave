# -*- coding: utf-8 -*-
"""
ParallelScheduler – launch HighTechnomancers whose dependencies are met,
each in an isolated workspace branch, and merge when they pass.
"""
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
import shutil, os, tempfile, uuid, pytest

from .high_technomancer import HighTechnomancer
from ..services.cost_ledger import CostCapExceeded
from ..utils.milestone_graph import load_graph   # helper added below

MAX_PARALLEL = 4  # configurable via env

class ParallelScheduler:
    def __init__(self, milestones_yaml: str, root_ws="workspace"):
        self.graph = load_graph(milestones_yaml)
        self.root_ws = Path(root_ws)
        self.executor = ThreadPoolExecutor(max_workers=MAX_PARALLEL)

    def _sandbox(self, mid: str) -> Path:
        sandbox = self.root_ws.parent / f"{mid}_{uuid.uuid4().hex[:6]}"
        shutil.copytree(self.root_ws, sandbox, dirs_exist_ok=True)
        return sandbox

    def _run_high(self, milestone):
        mid = milestone["id"]
        ws = self._sandbox(mid)
        os.environ["CONCLAVE_WORKSPACE"] = str(ws)
        high = HighTechnomancer(goal=milestone["goal"])
        try:
            high.run_milestone()
            passed = pytest.main(["-q"], plugins=[], cwd=ws) == 0
        except CostCapExceeded:
            passed = False
        return mid, passed, ws

    def run_all(self):
        futures = {}
        while self.graph.incomplete():
            ready = self.graph.ready_nodes()
            for m in ready:
                futures[self.executor.submit(self._run_high, m)] = m
                self.graph.mark_running(m["id"])
            done, _ = as_completed(futures), futures  # wait for at least one
            for fut in list(done):
                mid, ok, ws = fut.result()
                if ok:
                    self._merge(ws)
                    self.graph.mark_passed(mid)
                else:
                    self.graph.mark_failed(mid)
                futures.pop(fut)
        self.executor.shutdown(wait=True)

    def _merge(self, sandbox: Path):
        # naïve "copy-if-clean" merge
        for file in sandbox.rglob("*"):
            rel = file.relative_to(sandbox)
            dst = self.root_ws / rel
            if dst.exists():
                raise RuntimeError(f"Merge conflict on {rel}")
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(file, dst)
