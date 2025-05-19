# SPDX-License-Identifier: MIT

import pytest
from agents.import_utils import dynamic_import, RoleImportError

def test_dynamic_import_success():
    cls = dynamic_import('agents.base', 'AgentBase')
    from agents.base import AgentBase
    assert cls is AgentBase

def test_dynamic_import_module_not_found():
    with pytest.raises(RoleImportError) as exc:
        dynamic_import('nonexistent.module', 'SomeClass')
    assert "Module 'nonexistent.module' not found" in str(exc.value)

def test_dynamic_import_class_not_found():
    with pytest.raises(RoleImportError) as exc:
        dynamic_import('agents.base', 'NonExistentClass')
    assert "Class 'NonExistentClass' not found in module 'agents.base'" in str(exc.value)