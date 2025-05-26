import pytest, random
from conclave.consensus.debate_manager import DebateManager

class DummyAgent:
    def __init__(self, name, answer): self.name, self.answer = name, answer
    def think(self, issue, history=None): return self.answer

def test_majority_wins():
    agents = [DummyAgent("A","X"), DummyAgent("B","Y"), DummyAgent("C","X")]
    mgr = DebateManager(rounds=2)
    decision, hist = mgr.run(issue="dummy", agents=agents)
    assert decision == "X"
    # history records two rounds max even if consensus in 1st
    assert hist[0][0] == "round"

def test_unanimous_protocol():
    agents = [DummyAgent("A","Z")] * 3
    mgr = DebateManager(rounds=1, protocol="unanimous")
    decision, _ = mgr.run(issue="dummy", agents=agents)
    assert decision == "Z"

def test_timeout():
    slow = DummyAgent("slow","A")
    slow.think = lambda *_: (_ for _ in ()).throw(TimeoutError)  # never returns
    mgr = DebateManager(rounds=1, timeout=0.01)
    with pytest.raises(Exception):
        mgr.run(issue="dummy", agents=[slow])
