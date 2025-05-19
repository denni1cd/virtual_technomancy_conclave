# SPDX-License-Identifier: MIT

"""cost_tracker.py: Tracks token and dollar spend per agent, enforcing guardrails."""

import json
from pathlib import Path
from config.loader import load_guardrails, load_roles

class CostCapExceeded(Exception):
  """Raised when a cost or token cap is exceeded."""
  pass

# Removed load_limits(): using typed configuration loader instead

class Ledger:
  """Ledger for recording and summarizing usage per role."""
  def __init__(self):
    """Initialize ledger storage."""
    self._dir = Path.home() / ".conclave_ledger"
    self._dir.mkdir(parents=True, exist_ok=True)
    self._file = self._dir / "ledger.jsonl"

  def record(self, role: str, tokens: int, cost_usd: float):
    """Append a usage entry for a role."""
    entry = {"role": role, "tokens": tokens, "cost_usd": cost_usd}
    with self._file.open("a", encoding="utf-8") as f:
      f.write(json.dumps(entry) + "\n")

  def totals(self, role: str) -> dict:
    """Compute total tokens and cost_usd for a given role."""
    total_tokens = 0
    total_cost = 0.0
    if not self._file.exists():
      return {"tokens": total_tokens, "cost_usd": total_cost}
    for line in self._file.read_text(encoding="utf-8").splitlines():
      try:
        entry = json.loads(line)
      except json.JSONDecodeError:
        continue
      if entry.get("role") == role:
        total_tokens += entry.get("tokens", 0)
        total_cost += entry.get("cost_usd", 0.0)
    return {"tokens": total_tokens, "cost_usd": total_cost}

def enforce_cost(role_name: str):
  """Decorator to enforce cost and token guardrails for OpenAI calls.

  Args:
    role_name: Name of the role to apply limits for.

  Raises:
    CostCapExceeded: If cumulative cost or tokens exceed role or global limits.
  """
  def decorator(fn):
    def wrapper(*args, **kwargs):
      gconf = load_guardrails()
      rconf = load_roles()
      resp = fn(*args, **kwargs)
      usage = resp.get("usage", {})
      tokens = usage.get("total_tokens", 0)
      cost_usd = tokens * 0.00001
      ledger = Ledger()
      ledger.record(role_name, tokens, cost_usd)
      totals = ledger.totals(role_name)
      # Determine max limits
      global_max_cost = gconf.global_.max_cost_usd
      global_max_tokens = gconf.global_.max_tokens
      role_conf = rconf.get(role_name)
      role_max_cost = (role_conf.limits.max_cost_usd
                       if role_conf and role_conf.limits and role_conf.limits.max_cost_usd is not None
                       else global_max_cost)
      role_max_tokens = (role_conf.limits.max_tokens
                         if role_conf and role_conf.limits and role_conf.limits.max_tokens is not None
                         else global_max_tokens)
      if ((role_max_cost is not None and totals["cost_usd"] > role_max_cost) or
          (role_max_tokens is not None and totals["tokens"] > role_max_tokens)):
        raise CostCapExceeded(
          f"Role '{role_name}' exceeded limits: tokens={totals['tokens']} (max {role_max_tokens}), "
          f"cost_usd={totals['cost_usd']:.6f} (max {role_max_cost})"
        )
      return resp
    return wrapper
  return decorator

if __name__ == "__main__":
  gconf = load_guardrails()
  rconf = load_roles()
  ledger = Ledger()
  print("Current usage per role:")
  for role in rconf:
    t = ledger.totals(role)
    print(f"{role}: tokens={t['tokens']}, cost_usd={t['cost_usd']:.6f}")