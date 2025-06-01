# tests/conftest.py
import pytest

@pytest.fixture
def anyio_backend():
    """
    Force pytest-anyio to run every async test only on the asyncio backend.
    This prevents trio/curio parametrisation and the nursery errors you’re seeing.
    """
    return "asyncio"
