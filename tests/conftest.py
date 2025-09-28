"""Pytest configuration for integration tests."""

import contextlib
import os
import uuid

import ops.pebble
import pytest


def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line("markers", "integration: marks tests as integration tests")
    config.addinivalue_line(
        "markers", "pebble: marks tests that require a Pebble server"
    )


def pytest_collection_modifyitems(config, items):
    """Automatically mark tests based on their location and content."""
    for item in items:
        # Mark integration tests
        if "integration" in item.nodeid.lower():
            item.add_marker(pytest.mark.integration)

        # Mark tests that use Pebble
        if "pebble" in item.nodeid.lower() or "test_integration" in item.nodeid:
            item.add_marker(pytest.mark.pebble)


@pytest.fixture(scope="session")
def pebble_available():
    """Check if a Pebble server is available."""
    socket_path = os.environ.get("PEBBLE_SOCKET", "/charm/containers/*/pebble.sock")

    try:
        # Try to connect to Pebble
        client = ops.pebble.Client(socket_path=socket_path)
        client.get_system_info()
        return True
    except Exception:
        return False


@pytest.fixture(scope="session")
def pebble_client(pebble_available):
    """Get a connected Pebble client if available."""
    if not pebble_available:
        pytest.skip("No Pebble server available")

    socket_path = os.environ.get("PEBBLE_SOCKET", "/charm/containers/*/pebble.sock")
    client = ops.pebble.Client(socket_path=socket_path)
    client.get_system_info()  # Test connection
    return client


@pytest.fixture
def temp_pebble_file(pebble_client):
    """Create a temporary file in Pebble and clean it up after the test."""

    # Generate a unique filename using a more secure temp directory
    import tempfile

    temp_dir = tempfile.gettempdir()
    filename = f"{temp_dir}/cascade_test_{uuid.uuid4().hex[:8]}.txt"

    yield filename

    # Clean up
    with contextlib.suppress(Exception):
        pebble_client.remove_path(filename)


@pytest.fixture
def temp_pebble_dir(pebble_client):
    """Create a temporary directory in Pebble and clean it up after the test."""

    # Generate a unique directory name using a more secure temp directory
    import tempfile

    temp_dir = tempfile.gettempdir()
    dirname = f"{temp_dir}/cascade_test_dir_{uuid.uuid4().hex[:8]}"

    yield dirname

    # Clean up
    with contextlib.suppress(Exception):
        pebble_client.remove_path(dirname)


def pytest_runtest_setup(item):
    """Skip tests that require Pebble if no server is available."""
    if item.get_closest_marker("pebble"):
        # Check if Pebble is available
        socket_path = os.environ.get("PEBBLE_SOCKET", "/charm/containers/*/pebble.sock")
        try:
            client = ops.pebble.Client(socket_path=socket_path)
            client.get_system_info()
        except Exception:
            pytest.skip("No Pebble server available")


def pytest_addoption(parser):
    """Add command line options for integration tests."""
    parser.addoption(
        "--pebble-socket",
        action="store",
        default="/charm/containers/*/pebble.sock",
        help="Pebble socket path for integration tests",
    )
    parser.addoption(
        "--run-slow",
        action="store_true",
        default=False,
        help="Run slow integration tests",
    )


def pytest_ignore_collect(collection_path, config):
    """Skip integration tests if not explicitly requested."""
    return "test_integration" in str(collection_path) and not config.getoption(
        "--run-slow"
    )
