# Governance and Contribution Guidelines

This document defines governance, roles, and merge criteria for the Virtual Technomancy Conclave.

## Roles
- **ArchTechnomancer**: Orchestrates planning, controls costs, and merges changes.  
- **HighTechnomancer-Engineering**: Breaks epics into tickets and reviews PRs.  
- **HighTechnomancer-QA**: Stubs tests and ensures quality.  
- **Technomancer-<Expertise>**: Implements code and tests.  
- **ApprenticeTechnomancer-<Expertise>**: Handles small fixes, lint/tests, and asks clarifying questions.  

## Contribution Guidelines
- All code must target Python 3.12 as specified in `config/guardrails.yaml`.  
- Allowed dependencies: `openai>=1.15`, `pydantic`, `pytest`.  
- Every PR must include new or updated tests under `tests/` and pass `pytest -q`.  
- No network egress during test runs (`tests_network_egress: false`).  
- Use `tools/cost_tracker.py` to verify that token/dollar spend per milestone remains under $0.10.  

## Merge Criteria
- **Engineering Lead** (HighTechnomancer-Engineering) must approve code changes.  
- **QA Lead** (HighTechnomancer-QA) must approve test coverage.  
- **ArchTechnomancer** merges only after tests pass and cost budget is below cap.  

## Repository Structure
Refer to `README.md` for the full project layout and file organization.