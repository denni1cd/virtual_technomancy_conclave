# Conclave

Conclave is a **fully‑agentic, cost‑aware software‑engineering swarm** that couples the **OpenAI Agents SDK** for vertical orchestration with Google’s **Agent‑to‑Agent (A2A) protocol** for peer‑to‑peer cross‑talk.

Phase 1 (complete) scaffolds:

* dynamic runtime roles
* cost‑ledger & guardrails
* Portalocker‑safe file & search tools
* tracing hooks to the OpenAI dashboard
* majority‑vote Debate Manager
* CLI smoke‑test
  \* and a 10‑green‑test CI suite

Phase 2 (road‑mapped) swaps stubs for real model calls, adds A2A messaging, cost‑cap enforcement, and milestone state‑machines to deliver a production‑grade dev collective.

---

## Quick Start

```bash
# 1 – clone & install
$ git clone https://github.com/your‑org/conclave.git
$ cd conclave
$ conda create -n conclave python=3.12 -y && conda activate conclave
$ pip install -r requirements.txt   # portalocker, python‑dotenv, pytest

# 2 – create a .env with your key
OPENAI_API_KEY=sk‑...

# 3 – run tests
$ pytest -q    # 10 passed

# 4 – smoke demo
$ python main.py "refactor logging module"
```

You will see a debate decision, an artefact in **`workspace/hello.txt`**, a cost ledger line in **`conclave_usage.jsonl`**, and an OpenAI trace link.

---

## Directory Layout (Phase 1)

```
conclave/
├─ config/            # guardrails.yaml • roles.yaml
├─ agents/            # technomancer_base.py • agent_factory.py
├─ tools/             # file_io.py • web_search.py • peer_chat_a2a.py
├─ services/          # cost_ledger.py • trace_utils.py
├─ consensus/         # debate_manager.py
├─ workspace/         # agent‑generated artefacts
├─ tests/             # pytest suite (10 tests)
└─ main.py            # CLI smoke‑test
```

---

## Runtime Role Hierarchy

| Rank                 | Purpose                            | Default Cap      | Debate Rounds |
| -------------------- | ---------------------------------- | ---------------- | ------------- |
| **ArchTechnomancer** | Final milestone gate & tie‑breaker | \$50 / 200 k tkn | 0             |
| **HighTechnomancer** | Own one milestone; spawn Techs     | \$25 / 50 k      | 3             |
| **Technomancer**     | Implement tasks; spawn Apprentices | \$10 / 25 k      | 2             |
| **Apprentice**       | Lint, test, refactor               | \$5 / 5 k        | 0             |

All share the same tool bundle; cost caps are enforced in Phase 2.

---

## Core Features

* **Dynamic roles** – `roles.yaml` → runtime subclasses via `type()`
* **Portalocker file I/O** – atomic writes & shared‑lock reads
* **JSONL cost ledger** – race‑safe, advisory‑locked
* **Tracing hooks** – surfacing `trace_url` per run via `.env` loaded key
* **Debate Manager** – odd‑agent majority vote converges in ≤3 rounds

---

## Phase 2 Roadmap

1. **Real LLM Calls** – replace `think()` stubs with Agents‑SDK `Runner.run()` + function‑tool schemas.
2. **HighTechnomancer Orchestration** – spawn N Technomancers, run debate, merge.
3. **A2A Peer Chat** – JSON‑RPC `/tasks` & `/messages` for cross‑agent messaging.
4. **Cost‑Cap Enforcement** – raise `CostCapExceeded` when ledger totals exceed YAML limits.
5. **Milestone FSM** – Arch approves, rejects, or restarts with lessons‑learned.
6. **External Tracing** – pipe trace IDs to LangSmith / Langfuse for fleet‑wide observability.

---

## Contributing

\* Fork ➜ PR ➜ keep **pytest green**.
\* Write unit tests for every new module.
\* Adhere to Black 24.3 & Google docstring style.
\* Open a GitHub Discussion for major features.

---

## License

MIT — see **LICENSE**.

---

### References

1. OpenAI Agents SDK tracing docs 2. Responses‑API function‑calling guide 3. Portalocker docs 4. Google A2A spec 5. Boyer‑Moore majority‑vote proof 6. JSONL spec 7. OpenAI rate‑limit FAQ 8. python‑dotenv load order 9. RFC 3339 timestamps 10. LangSmith tracing example
