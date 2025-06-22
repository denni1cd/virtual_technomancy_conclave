"""
Generic debate orchestration for Conclave (Sprint T5).

Usage
-----
from conclave.consensus.debate_manager import DebateManager

mgr = DebateManager(rounds=3, protocol="majority", timeout=30)
decision, history = mgr.run(issue="Pick a data-store", agents=[a1, a2, a3])
"""

from __future__ import annotations
import asyncio, inspect, time
from collections import Counter
from typing import List, Tuple, Any

from conclave.services.tracing import get_tracer

class DebateTimeout(Exception): ...

class DebateManager:
    def __init__(self, *, rounds: int = 3,
                 protocol: str = "majority",
                 timeout: float | None = None) -> None:
        if rounds < 1:
            raise ValueError("rounds must be ≥ 1")
        self.rounds, self.protocol, self.timeout = rounds, protocol, timeout

    async def _ask(self, agent, issue, history):
        if inspect.iscoroutinefunction(agent.think):
            return await agent.think(issue, history=history)
        return agent.think(issue, history=history)

    async def _round(self, agents, issue, history):
        coros = [self._ask(a, issue, history) for a in agents]
        return await asyncio.gather(*coros)

    def _decide(self, proposals):
        if self.protocol == "majority":
            winner, _ = Counter(proposals).most_common(1)[0]
            return winner
        if self.protocol == "unanimous" and len(set(proposals)) == 1:
            return proposals[0]
        return None                        # unresolved

    # ------------------------------------------------------------------ #
    def run(self, *, issue: str, agents: List, loop=None
            ) -> Tuple[str | None, List]:
        if not agents:
            raise ValueError("Must supply ≥1 agent")
        history: List[Tuple[str, Any]] = []
        loop = loop or asyncio.new_event_loop()

        # Start tracing child span for debate
        tracer = get_tracer()
        with tracer.child_span(
            name="debate_manager",
            kind="DEBATE",
            metadata={
                "issue": issue,
                "agent_count": len(agents),
                "rounds": self.rounds,
                "protocol": self.protocol
            }
        ):
            start = time.time()
            for round_num in range(self.rounds):
                if self.timeout and (time.time() - start) > self.timeout:
                    raise DebateTimeout(self.timeout)

                proposals = loop.run_until_complete(
                    self._round(agents, issue, history)
                )
                history.append(("round", proposals))
                
                # Add tracing event for debate round
                tracer.add_event(
                    "debate_round",
                    {
                        "round": round_num + 1,
                        "proposals": proposals,
                        "agent_count": len(agents)
                    }
                )
                
                decision = self._decide(proposals)
                if decision:
                    # Add tracing event for final decision
                    tracer.add_event(
                        "debate_choice",
                        {
                            "decision": decision,
                            "rounds_used": round_num + 1,
                            "protocol": self.protocol
                        }
                    )
                    return decision, history

            # no consensus after N rounds
            tracer.add_event(
                "debate_timeout",
                {
                    "rounds_completed": self.rounds,
                    "protocol": self.protocol,
                    "decision": None
                }
            )
            return None, history
