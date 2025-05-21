# SPDX-License-Identifier: MIT
"""
agents.factory
~~~~~~~~~~~~~~
Factory for creating agent instances based on roles.yaml.

Current behaviour
-----------------
* Looks up a role entry in the cached `config.ROLES`.
* Dynamically imports the class via `dynamic_import`.
* Instantiates the class, optionally checking for missing template parameters.

(To-do: attach limits/tools/memory and handle template roles.)
"""

from __future__ import annotations

import logging
from typing import Any

from config import ROLES
from agents.import_utils import RoleImportError, dynamic_import
from services.memory import MemoryStore


class AgentFactoryError(Exception):
    """Raised when an agent cannot be created."""


class AgentFactory:
    """Create agent instances from the roles configuration."""

    @staticmethod
    def create_agent(role_name: str, **kwargs: Any):
        """
        Parameters
        ----------
        role_name : str
            The role key exactly as it appears in roles.yaml.
        **kwargs
            Optional template parameters (unused unless the role entry
            declares a ``parameters`` mapping).

        Returns
        -------
        object
            A fully-instantiated agent.

        Raises
        ------
        AgentFactoryError
            If the role is unknown, the class cannot be imported, or any
            required template parameters are missing.
        """
        # 1 – lookup role config
        try:
            rc = ROLES[role_name]
        except KeyError as exc:
            raise AgentFactoryError(
                f"Role '{role_name}' not found in configuration"
            ) from exc

        # 2 – import class dynamically
        try:
            cls = dynamic_import(rc.module, rc.class_name)
        except RoleImportError as exc:
            raise AgentFactoryError(
                f"Failed to import class for role '{role_name}': {exc}"
            ) from exc

        # 3 – check template parameters (if any)
        params = getattr(rc, "parameters", None)
        if params:
            missing = [p for p in params if p not in kwargs]
            if missing:
                raise AgentFactoryError(
                    f"Missing parameters for role '{role_name}': {missing}"
                )
            instance = cls(**kwargs)
        else:
            instance = cls()

        # 4 – (optional) attach per-agent memory (example shown, not yet used)
        # instance.memory = MemoryStore.for_agent(role_name, "epic")

        return instance


# Log role keys at import for traceability
logging.getLogger(__name__).info(
    "AgentFactory initialized with roles: %s",
    list(ROLES.keys()),
)
