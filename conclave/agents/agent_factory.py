from __future__ import annotations

import pathlib
from types import MappingProxyType
from typing import Dict, Type

import yaml

from .exceptions import ConfigError, UnknownRoleError
from .technomancer_base import TechnomancerBase

# ---------------------------------------------------------------------------

_CFG_PATH = (
    pathlib.Path(__file__).resolve().parents[1] / "config" / "roles.yaml"
)
_REQUIRED_KEYS = {"prompt", "rank", "cost_cap_usd", "token_cap"}


class AgentFactory:
    """Dynamically builds Conclave*Technomancer classes from YAML templates."""

    def __init__(self) -> None:
        self.registry: Dict[str, Type[TechnomancerBase]] = {}
        self._load_and_build()

    # ---------------------------------------------------------------------
    # public helpers
    # ---------------------------------------------------------------------
    def spawn(self, role_name: str, **overrides) -> TechnomancerBase:
        """
        Return a live agent instance of *role_name*.

        `overrides` let callers tweak template values (rare).
        """
        try:
            cls = self.registry[role_name]
        except KeyError as exc:  # pragma: no cover
            raise UnknownRoleError(role_name) from exc

        # merge template attrs with call-time overrides
        merged = {**cls._template_attrs, **overrides}  # type: ignore[attr-defined]
        return cls(role_name=role_name, **merged)

    # ---------------------------------------------------------------------
    # private helpers
    # ---------------------------------------------------------------------
    def _load_and_build(self) -> None:
        if not _CFG_PATH.is_file():
            raise ConfigError(f"roles.yaml not found: {_CFG_PATH}")

        data = yaml.safe_load(_CFG_PATH.read_text())  # safe_load avoids code-exec 🔒
        if not isinstance(data, dict):  # pragma: no cover
            raise ConfigError("roles.yaml must map role-name → template")

        for role, template in data.items():
            missing = _REQUIRED_KEYS - template.keys()
            if missing:
                raise ConfigError(f"{role} missing keys: {', '.join(missing)}")

            attrs = {
                "role_prompt": template["prompt"],
                "rank": int(template["rank"]),
                "cost_cap_usd": float(template["cost_cap_usd"]),
                "token_cap": int(template["token_cap"]),
                "debate_rounds": int(template.get("debate_rounds", 0)),
            }
            # keep original dict for quick spawn-time merge
            attrs["_template_attrs"] = attrs.copy()

            cls_name = f"Conclave{role}"
            dynamic_cls = type(cls_name, (TechnomancerBase,), attrs)
            self.registry[role] = dynamic_cls

        # freeze – callers can read but not mutate
        self.registry = MappingProxyType(self.registry)

    # -------------------- convenience helpers -------------------- #
    def spawn_one_high_with_one_technomancer(self):
        """Utility for smoke-tests: returns (high, tech)."""
        high = self.spawn("HighTechnomancer")
        tech = self.spawn("Technomancer")
        return high, tech

# convenience singleton
factory = AgentFactory()
