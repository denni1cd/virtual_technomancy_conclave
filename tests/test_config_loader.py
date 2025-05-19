# SPDX-License-Identifier: MIT

"""Tests for configuration loader."""

import config.loader as loader

def test_arch_config_loader_cap():
    """ArchTechnomancer cost cap should be 50 USD."""
    gconf = loader.load_guardrails()
    assert gconf.global_.max_cost_usd == 50
    rconf = loader.load_roles()
    assert "ArchTechnomancer" in rconf
    assert rconf["ArchTechnomancer"].limits.max_cost_usd == 50