# tests/conftest.py
import pytest
import pytest_asyncio
import asyncio

@pytest.fixture(scope="function")
def event_loop():
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
def anyio_backend():
    """Use asyncio backend for async tests."""
    return "asyncio"

def pytest_configure(config):
    """Configure test defaults."""
    config.addinivalue_line("markers", "asyncio: mark test as async")
