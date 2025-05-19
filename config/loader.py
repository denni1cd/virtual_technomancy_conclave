# SPDX-License-Identifier: MIT
"""
config.loader
~~~~~~~~~~~~~
Typed helpers for loading and validating Conclave configuration files.

• load_guardrails() → GuardrailConfig
• load_roles()      → dict[str, RoleConfig]

Both functions cache their results, so repeated calls are cheap.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Optional

import yaml
from pydantic import BaseModel, Field, ValidationError


# ────────────────────────────────────────────────────────────────────────────
# Pydantic models
# ────────────────────────────────────────────────────────────────────────────


class RoleLimits(BaseModel):
    max_cost_usd: Optional[float] = None
    max_tokens: Optional[int] = None


class RoleConfig(BaseModel):
    module: str
    class_name: str = Field(alias="class")  # keep YAML key `class`
    description: str
    tools: List[str]
    limits: Optional[RoleLimits] = None

    # Allow extra fields (e.g., templates may carry `parameters`)
    model_config = {"extra": "allow"}


class GlobalLimits(BaseModel):
    max_cost_usd: float
    max_tokens: int
    max_recursion_depth: int


class NetworkPolicy(BaseModel):
    internet_access: str
    tests_network_egress: bool


class GuardrailConfig(BaseModel):
    version: int
    python_version: str
    runtime: dict
    global_: GlobalLimits = Field(alias="global")
    network: NetworkPolicy
    roles: Dict[str, RoleLimits]
    tools: dict
    logging: dict


# ────────────────────────────────────────────────────────────────────────────
# Loader helpers
# ────────────────────────────────────────────────────────────────────────────


_CONFIG_DIR = Path(__file__).parent
_ROLES_FILE = _CONFIG_DIR / "roles.yaml"
_GUARDRAILS_FILE = _CONFIG_DIR / "guardrails.yaml"


def _read_yaml(path: Path) -> dict:
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:  # pragma: no cover
        raise RuntimeError(f"Failed to parse YAML at {path}: {exc}") from exc
    except FileNotFoundError as exc:  # pragma: no cover
        raise RuntimeError(f"Missing configuration file: {path}") from exc


@lru_cache(maxsize=1)
def load_guardrails() -> GuardrailConfig:
    """Return parsed & validated guardrail configuration."""
    raw = _read_yaml(_GUARDRAILS_FILE)
    try:
        return GuardrailConfig(**raw)
    except ValidationError as exc:  # pragma: no cover
        raise RuntimeError(f"Invalid guardrails.yaml format:\n{exc}") from exc


@lru_cache(maxsize=1)
def load_roles() -> Dict[str, RoleConfig]:
    """Return a dict of role-name → RoleConfig."""
    raw = _read_yaml(_ROLES_FILE).get("roles", {})
    roles: Dict[str, RoleConfig] = {}
    for name, cfg in raw.items():
        try:
            roles[name] = RoleConfig(model_copy=False, **cfg)
        except ValidationError as exc:  # pragma: no cover
            raise RuntimeError(f"Invalid roles.yaml entry for '{name}':\n{exc}") from exc
    return roles


# ────────────────────────────────────────────────────────────────────────────
# Conveniences for interactive debugging
# ────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("Guardrails summary:")
    print(load_guardrails().model_dump(mode="json", indent=2))

    print("\nRoles loaded:")
    for role, cfg in load_roles().items():
        print(f"• {role} -> {cfg.module}.{cfg.class_name}")
