# SPDX-License-Identifier: MIT

from pathlib import Path
from .loader import load_guardrails, load_roles

GUARDRAILS = load_guardrails()
ROLES = load_roles()

__all__ = ["GUARDRAILS", "ROLES", "load_guardrails", "load_roles"]