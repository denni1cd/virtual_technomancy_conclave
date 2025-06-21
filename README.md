# Conclave

Conclave is a **fully agentic, cost‑aware software‑engineering swarm**.
It couples the **OpenAI Agents SDK** (vertical orchestration & tool‑use via the Responses API) with Google’s **Agent‑to‑Agent (A2A) protocol** (horizontal peer‑to‑peer collaboration).
The system turns natural‑language prompts into tested, production‑ready code while staying within strict token‑ and dollar‑budgets.

---

## Phase Snapshot

| Phase                             | Goal                                  | Status         |
| --------------------------------- | ------------------------------------- | -------------- |
| **Phase 1 – Foundations**         | Skeleton swarm, guardrails, CI        | **✔ Complete** |
| **Phase 2 – Autonomous Agents**   | Real LLM calls, cost caps             | **✔ Complete** |
| **Phase 3 – Parallel Milestones** | Parallel milestones                   | **✔ Complete** |
| **Phase 4 – Enhancements**        | Observability, human‑in‑loop, scaling | ⏳ Planned      |

---

## Task Ledger (T01 – T16)

| ID        | Title                           | State | Highlights                                       |
| --------- | ------------------------------- | ----- | ------------------------------------------------ |
| **T01**   | Dynamic role factory            | ✔     | `AgentFactory` spawns Arch → High → Technomancer |
| **T02**   | JSONL cost ledger               | ✔     | Portalocker‑safe writes; per‑agent totals        |
| **T03**   | Guardrail caps                  | ✔     | Caps enforced post‑call via ledger checks        |
| **T04**   | File‑I/O tool                   | ✔     | Locked read/write to shared workspace            |
| **T05**   | Web‑search tool                 | ✔     | Stub; Responses‑API function call                |
| **T06**   | OpenAI trace hooks              | ✔     | Usage metrics sent to dashboard                  |
| **T07**   | Debate manager                  | ✔     | Odd‑agent majority vote with `asyncio.gather`    |
| **T08**   | CLI demo & CI suite             | ✔     | 68 unit tests; 95 % coverage                     |
| **T09**   | LLM call stubs                  | ✔     | Phase‑1 placeholder (superseded by T11)          |
| **T10**   | Real LLM calls                  | ✔     | GPT‑4o via Agents SDK & tool‑calling             |
| **T11**   | High‑Technomancer orchestration | ✔     | Spawns N technomancers; merges votes             |
| **T12**   | A2A peer messaging              | ✔     | FastAPI `/tasks`, `/subscribe` SSE               |
| **T13**   | Milestone FSM **→ parallel**    | ✔     | `ParallelScheduler` + DAG deps + sandbox merge   |
| **T14**   | Cost‑cap enforcement            | ✔     | `CostCapExceeded` raised on over‑spend           |
| **T15‑b** | Ledger polish                   | 🛠    | ContextVar fix, read‑lock (in review)            |
| **T16**   | External tracing                | ⏳     | LangSmith/Langfuse spans & cost events           |

*Full roadmap at bottom of this file.*

---

## Quick Start

```bash
# 1 – clone & install
$ git clone https://github.com/your‑org/conclave.git
$ cd conclave
$ conda create -n conclave python=3.12 -y && conda activate conclave
$ pip install -r requirements.txt

# 2 – add OpenAI key
$ echo "OPENAI_API_KEY=sk‑..." > .env

# 3 – run unit tests (no tokens)
$ pytest -q   # 68 green tests

# 4 – run live demo (real tokens)
$ python -m conclave.demo_agentic_build \
    --milestones examples/hello.yaml
```

The live demo spawns the full Arch → High → Tech hierarchy, writes code to `workspace/`, runs pytest on it, and logs spend to `conclave_usage.jsonl`.

---

## Directory Layout

```
conclave/
├─ agents/            # Arch, High, Technomancer base classes
├─ consensus/         # debate_manager.py
├─ config/            # roles.yaml • settings
├─ services/          # cost_ledger.py • a2a_server.py
├─ tools/             # file_io.py • web_search.py • peer_chat.py
├─ utils/             # milestone_graph.py • tracing stub
├─ workspace/         # generated code (git‑ignored)
├─ tests/             # pytest suite
└─ demo_agentic_build.py
```

---

## Runtime Role Hierarchy & Budgets

| Role                 | Purpose                                  | Cap (USD / tokens) |
| -------------------- | ---------------------------------------- | ------------------ |
| **ArchTechnomancer** | Milestone gatekeeper, retry, integration | 50 / 200 k         |
| **HighTechnomancer** | Spawns Technomancers, debates, merges    | 25 / 50 k          |
| **Technomancer**     | Implements single task                   | 10 / 25 k          |
| **Apprentice**       | Refactor / lint / unit‑test              | 5 / 5 k            |

Caps live in `roles.yaml` and are enforced in runtime via the **cost ledger** (post‑call check). Exceeding a cap raises `CostCapExceeded`, marks the milestone failed, and triggers retry logic.

---

## Core Features

* **OpenAI Agents SDK (GPT‑4o)** – tool‑calling with structured inputs/outputs
* **File, Search, Peer‑Chat tools** – exposed via Responses‑API schemas
* **A2A Messaging** – FastAPI + SSE for cross‑process chat
* **Parallel Milestones** – DAG scheduler, per‑sandbox workspaces, merge + integration test
* **Debate Consensus** – majority vote among odd Technomancer pool
* **Cost Ledger** – JSONL ledger + portalocker lock, hard budget enforcement
* **CLI & Demo Scripts** – one‑command prompt‑to‑program pipeline

---

## End‑to‑End Success Criteria

1. **Hello‑World Milestone**
   `python -m conclave.demo_agentic_build --milestones examples/hello.yaml`
   ✔ Generates `workspace/hello.py` + test, all pytest green, spend ≤ budget.

2. **Parallel Feature Build**
   `python scripts/run_parallel_example.py --milestones examples/milestones_large.yaml`
   ✔ All milestones pass, merged without conflict, ledger totals within global limits.

3. **Budget Safety Demo**
   `python cost_cap_demo.py`
   ✔ Raises `CostCapExceeded` exactly once over cap; run continues safely.

---

## Upcoming (Phase 4 – Enhancements)

* **T15‑b** – ContextVar & ledger read‑lock polish (PR #231)
* **T16** – External tracing: LangSmith adapter, span tree, cost events
* **T17** – Human‑in‑loop approval gates, git‑style merge conflicts
* **T1x** – Multi‑host scheduler & autoscaling

---

## References

* **OpenAI Agents SDK** – [https://platform.openai.com/docs/assistants/](https://platform.openai.com/docs/assistants/)
* **A2A Protocol** – [https://github.com/google/A2A](https://github.com/google/A2A)
* **Portalocker** – [https://pypi.org/project/portalocker/](https://pypi.org/project/portalocker/)
* **LangSmith Observability** – [https://docs.smith.langchain.com/observability](https://docs.smith.langchain.com/observability)

---

> Conclave is licensed under Apache‑2.0.
> © 2025 Your Org Inc.  All trademarks are property of their respective owners.
