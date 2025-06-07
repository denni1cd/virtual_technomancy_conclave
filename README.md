# Conclave

Conclave is a **fully agentic, cost‑aware software engineering swarm** that couples the **OpenAI Agents SDK** (for vertical orchestration and tool use via the Responses API) with Google’s **Agent‑to‑Agent (A2A) protocol** for horizontal peer‑to‑peer communication.

Phase 1 (complete) scaffolds the foundation:

- dynamic runtime role hierarchy
- cost‑ledger + configurable guardrails
- Portalocker‑safe file & search tools
- OpenAI tracing hooks (via `.env` key)
- majority‑vote Debate Manager
- CLI smoke test
- CI suite with 10 green tests

Phase 2 (in progress) turns this into a real swarm:
- real model calls via **OpenAI Agents SDK + Responses API**
- A2A peer messaging via FastAPI
- enforcement of cost caps
- milestone state machine with retry/approval cycles

---

## Project Summary

Conclave is designed as a **hierarchical, autonomous dev team** composed of AI agents called *Technomancers*, governed by a cost ledger, peer communication, and role-specific duties. Each role spawns others as needed, escalating to a **HighTechnomancer** or **ArchTechnomancer** when tasks require orchestration or milestone-wide coordination.

**Agents use the latest OpenAI GPT‑4.1 model**, defaulting to the **Responses API** for tool interaction and reasoning. A2A communication is backed by an SSE/POST protocol, allowing agents to synchronize across processes.

---

## Quick Start

```bash
# 1 – clone & install
$ git clone https://github.com/your-org/conclave.git
$ cd conclave
$ conda create -n conclave python=3.12 -y && conda activate conclave
$ pip install -r requirements.txt   # portalocker, python-dotenv, pytest, httpx

# 2 – create a .env with your OpenAI key
OPENAI_API_KEY=sk-...

# 3 – run tests
$ pytest -q    # All tests should pass

# 4 – smoke demo
$ python main.py "refactor logging module"
```

Outputs include:
- artefacts in `workspace/`
- JSONL cost ledger at `conclave_usage.jsonl`
- live OpenAI trace link per call

---

## Directory Layout (Phase 2+)

```
conclave/
├─ config/            # guardrails.yaml • roles.yaml
├─ agents/            # technomancer_base.py • high_technomancer.py • agent_factory.py
├─ tools/             # file_io.py • web_search.py • peer_chat_a2a.py
├─ services/          # cost_ledger.py • trace_utils.py • a2a_server.py
├─ consensus/         # debate_manager.py
├─ workspace/         # generated code & artefacts
├─ tests/             # 15+ tests for CLI, tools, and agents
└─ main.py            # CLI entry point
```

---

## Runtime Role Hierarchy

| Role                 | Responsibility                     | Cap ($ / tokens)  | Debate Rounds |
|----------------------|-------------------------------------|--------------------|---------------|
| **ArchTechnomancer** | Final milestone gate & retry logic | \$50 / 200 k       | 0             |
| **HighTechnomancer** | Spawns Technomancers per task      | \$25 / 50 k        | 3             |
| **Technomancer**     | Implements tasks                   | \$10 / 25 k        | 2             |
| **Apprentice**       | Refactors, lints, tests            | \$5 / 5 k          | 0             |

Caps are defined in `roles.yaml` and enforced at runtime via the **cost ledger** and upcoming **guard decorators**.

---

## Core Features

- **OpenAI Agents SDK** – default to GPT‑4.1, use `Responses API` for tool integration  
- **Function‑calling Tools** – file I/O, search, peer chat exposed as JSON tool schema  
- **A2A Messaging** – FastAPI server (`/tasks`, `/subscribe`) allows real-time peer sync  
- **Majority‑Vote Consensus** – odd‑agent majority vote converges on winning task outcome  
- **Cost Ledger + Guardrails** – safe JSONL ledger with enforcement (in progress)  
- **CLI Orchestration** – single-line interface to launch multi-agent swarm  

---

## Phase Roadmap

| Phase                          | Goal                                           | Tasks                                                                                                                                                   |
|--------------------------------|------------------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Phase 1 – Foundation**<br>*✅ Complete*       | Build scaffold with core architecture          | ✅ Dynamic Roles<br>✅ Cost Ledger<br>✅ Portalocker I/O<br>✅ Tracing Hooks<br>✅ Debate System<br>✅ CLI & Tests                                                           |
| **Phase 2 – Production Agents**<br>*🛠 In Progress* | Enable real agents with communication, enforcement, and task workflow | ✅ Real LLM Calls via SDK<br>✅ HighTechnomancer orchestration<br>✅ A2A SSE peer chat<br>🔄 Cost Cap Enforcement<br>🔄 Milestone FSM               |
| **Phase 3 – Observability & Scaling**<br>*📌 Planned* | Connect external tools and extend capabilities | ⏳ External Tracing (LangSmith)<br>⏳ Multi-host deployments<br>⏳ Plugin scaffolds for human-in-the-loop                                                           |

---

## References

- **Project docs**  
  - [OpenAI Agents SDK docs][agents-sdk] citeturn1news10  
  - [Responses API tool calling guide][responses-api] citeturn0news73  

- **Libraries**  
  - [portalocker][portalocker] citeturn0search2turn0search9  
  - [python-dotenv][dotenv] citeturn0search7  

- **Protocols & Algorithms**  
  - [Agent2Agent (A2A) Protocol][a2a-protocol] citeturn0search3turn0search10  
  - [Boyer–Moore majority vote algorithm][bmvote] citeturn0search4  

- **Observability**  
  - [LangSmith Observability Quickstart][langsmith] citeturn0search5  

- **Standards**  
  - [RFC 3339 Timestamp Spec][rfc3339]  

- **News**  
  navlistRecent Newsturn0news73,turn1news10  

[agents-sdk]: https://platform.openai.com/docs/quickstart/add-some-examples  
[responses-api]: https://platform.openai.com/docs/api-reference/introduction  
[portalocker]: https://pypi.org/project/portalocker/  
[dotenv]: https://pypi.org/project/python-dotenv/  
[a2a-protocol]: https://github.com/google/A2A  
[bmvote]: https://en.wikipedia.org/wiki/Boyer%E2%80%93Moore_majority_vote_algorithm  
[langsmith]: https://docs.smith.langchain.com/observability  
[rfc3339]: https://tools.ietf.org/html/rfc3339  
