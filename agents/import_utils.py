# SPDX-License-Identifier: MIT
"""
Dynamic import helpers for the Virtual Technomancy Conclave.
"""
from importlib import import_module
from types import ModuleType
from typing import Type, Any

class RoleImportError(ImportError):
    """Raised when a role’s module or class cannot be imported."""

def dynamic_import(module_path: str, class_name: str) -> Type[Any]:
    """Return a class object, or raise RoleImportError with a clear message."""
    try:
        module: ModuleType = import_module(module_path)
    except ModuleNotFoundError as exc:
        raise RoleImportError(f"Module '{module_path}' not found") from exc
    try:
        cls: Type[Any] = getattr(module, class_name)
    except AttributeError as exc:
        raise RoleImportError(
            f"Class '{class_name}' not found in module '{module_path}'"
        ) from exc
    return cls