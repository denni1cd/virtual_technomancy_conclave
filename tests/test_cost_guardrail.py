# SPDX-License-Identifier: MIT

"""Tests for cost tracking and guardrail enforcement."""

import json
import pytest
import importlib
from pathlib import Path
import tools.cost_tracker as ct
from types import SimpleNamespace

def setup_function(function):
  """Reload the cost_tracker module before each test."""
  importlib.reload(ct)

def test_under_cap(tmp_path, monkeypatch):
  """Under cap should not raise and ledger records entry."""
  # Redirect ledger storage to temporary path
  monkeypatch.setattr(Path, "home", lambda: tmp_path)
  limits = {
    "global": {"max_cost_usd": 1000, "max_tokens": 1000000},
    "roles": {"TestRole": {"max_cost_usd": 1000, "max_tokens": 1000000}}
  }
  monkeypatch.setattr(ct, "load_guardrails", lambda: SimpleNamespace(global_=SimpleNamespace(max_cost_usd=limits["global"]["max_cost_usd"], max_tokens=limits["global"]["max_tokens"])))
  monkeypatch.setattr(ct, "load_roles", lambda: {"TestRole": SimpleNamespace(limits=SimpleNamespace(max_cost_usd=limits["roles"]["TestRole"]["max_cost_usd"], max_tokens=limits["roles"]["TestRole"]["max_tokens"]))})
  @ct.enforce_cost("TestRole")
  def dummy_call():
    return {"usage": {"total_tokens": 100}}
  resp = dummy_call()
  assert resp["usage"]["total_tokens"] == 100
  ledger_file = tmp_path / ".conclave_ledger" / "ledger.jsonl"
  lines = ledger_file.read_text().splitlines()
  assert len(lines) == 1
  entry = json.loads(lines[0])
  assert entry["role"] == "TestRole"
  assert entry["tokens"] == 100

def test_over_cap(tmp_path, monkeypatch):
  """Over cap should raise CostCapExceeded."""
  monkeypatch.setattr(Path, "home", lambda: tmp_path)
  limits = {
    "global": {"max_cost_usd": 0.0005, "max_tokens": 10},
    "roles": {"TestRole": {"max_cost_usd": 0.0005, "max_tokens": 10}}
  }
  monkeypatch.setattr(ct, "load_guardrails", lambda: SimpleNamespace(global_=SimpleNamespace(max_cost_usd=limits["global"]["max_cost_usd"], max_tokens=limits["global"]["max_tokens"])))
  monkeypatch.setattr(ct, "load_roles", lambda: {"TestRole": SimpleNamespace(limits=SimpleNamespace(max_cost_usd=limits["roles"]["TestRole"]["max_cost_usd"], max_tokens=limits["roles"]["TestRole"]["max_tokens"]))})
  @ct.enforce_cost("TestRole")
  def dummy_call():
    return {"usage": {"total_tokens": 100}}
  with pytest.raises(ct.CostCapExceeded):
    dummy_call()