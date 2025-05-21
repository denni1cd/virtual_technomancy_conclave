# SPDX-License-Identifier: MIT
from config import ROLES
from agents.import_utils import dynamic_import, RoleImportError
from services.memory import MemoryStore
import logging


class AgentFactoryError(Exception):
    """Raised when an agent cannot be created."""
    pass


class AgentFactory:
    """Factory for creating agent instances based on roles.yaml configuration."""

    @staticmethod
    def create_agent(role_name: str, **kwargs):
        """Create an agent instance for the given role name."""
        try:
            rc = ROLES[role_name]
        except KeyError as exc:
            raise AgentFactoryError(f"Role '{role_name}' not found in configuration") from exc

        try:
            cls = dynamic_import(rc.module, rc.class_name)
        except RoleImportError as exc:
            raise AgentFactoryError(f"Failed to import class for role '{role_name}': {exc}") from exc

        params = getattr(rc, "parameters", None)
        if params:
            missing = [p for p in params.keys() if p not in kwargs]
            if missing:
                raise AgentFactoryError(f"Missing parameters for role '{role_name}': {missing}")
            return cls(**kwargs)
        else:
            return cls()


# Initialize logger
logging.getLogger(__name__).info(
    "AgentFactory initialized with roles: %s", list(ROLES.keys())
)
