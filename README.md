# Virtual Technomancy Conclave

Self-organizing hierarchy of LLM agents (Technomancers) that plan, code, test, document, and ship features with minimal human intervention.

## Installation

Requires Python 3.12. Install dependencies:
```bash
pip install openai>=1.15 pydantic pytest
```

## Usage

```bash
python main.py "<goal>"
```

## Testing

```bash
pytest -q
```

## Project Structure

- agents/: Agent classes
  - base.py: Base agent classes and utilities
  - arch.py: ArchTechnomancer orchestrator
  - high_*.py: HighTechnomancer leads
  - technomancer_*.py: Technomancer worker agents
- services/: Memory store and search tool wrappers
- tools/: Token and cost tracking utilities
- tests/: Unit tests and bootstrap tests
- docs/: Documentation including milestones and governance
- config/: YAML configuration for roles, guardrails, and project manifest
- config/loader.py: Typed loader for guardrails.yaml and roles.yaml (pydantic validation, caching)
- main.py: CLI entrypoint

## Contributing

- Every PR must include or update a test in `tests/` and pass `pytest -q`.
- No network egress during test runs.
- See docs/GOVERNANCE.md for governance and contribution guidelines.

## Cost Tracking & Guardrails

The Conclave tracks token and cost usage per role, enforcing a default cap of $50 USD per run. Limits can be customized in `config/guardrails.yaml` under the `global` and `roles` sections:

```yaml
global:
  max_cost_usd: 50

roles:
  ArchTechnomancer:
    max_cost_usd: 50
    max_tokens: 100000
```
