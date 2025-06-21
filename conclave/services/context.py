"""
Context isolation helpers for Conclave agents.

This module provides utilities to manage ContextVar isolation across asyncio tasks,
ensuring that each task sees its own role_id and never another agent's.
"""

import contextvars
from typing import Any, Callable, Coroutine
import asyncio


# Global ContextVar for current role/agent context
_CURRENT_ROLE_VAR: contextvars.ContextVar[str] = contextvars.ContextVar("current_role")


def set_role(role_name: str) -> None:
    """Set the current role in the context."""
    _CURRENT_ROLE_VAR.set(role_name)


def get_role() -> str:
    """Get the current role from context."""
    try:
        return _CURRENT_ROLE_VAR.get()
    except LookupError:
        # Fallback to a default if no role is set
        return "Unknown"


def create_task_with_context(
    coro: Coroutine[Any, Any, Any], 
    role_name: str,
    name: str | None = None
) -> asyncio.Task[Any]:
    """
    Create an asyncio task with isolated context.
    
    This ensures that the child task gets a copy of the current context
    with the specified role_name, preventing context leakage between tasks.
    """
    # Create a new context with the role set
    ctx = contextvars.copy_context()
    ctx.run(set_role, role_name)
    
    # Create the task with the isolated context
    return asyncio.create_task(coro, name=name, context=ctx)


def run_with_context(func: Callable[..., Any], role_name: str, *args, **kwargs) -> Any:
    """
    Run a function with isolated context.
    
    This is useful for synchronous functions that need role context.
    """
    ctx = contextvars.copy_context()
    ctx.run(set_role, role_name)
    return ctx.run(func, *args, **kwargs) 