# SPDX-License-Identifier: MIT

import pytest
from agents.import_utils import dynamic_import, RoleImportError

def test_dynamic_import_module_not_found():
    with pytest.raises(RoleImportError) as exc:
        dynamic_import('nonexistent.module', 'SomeClass')
    assert "Module 'nonexistent.module' not found" in str(exc.value)
