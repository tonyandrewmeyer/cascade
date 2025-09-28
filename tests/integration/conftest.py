"""Common utilities for integration tests."""

import pathlib
import subprocess
import time

import ops
import pytest

import pebble_shell.shell


@pytest.fixture(scope="session")
def pebble_socket(tmp_path_factory):
    """Fixture to run a Pebble process in the background."""
    tmp_path = tmp_path_factory.mktemp("pebble")
    cmd = [
        "/snap/bin/pebble",
        "run",
        "--create-dirs",
        "--hold",
    ]
    pebble = subprocess.Popen(cmd, env={"PEBBLE": str(tmp_path)})  # noqa: S603
    time.sleep(1)
    yield tmp_path / ".pebble.socket"
    pebble.terminate()


@pytest.fixture(scope="session")
def client(pebble_socket: pathlib.Path):
    """Fixture to create a pebble client."""
    yield ops.pebble.Client(str(pebble_socket))


@pytest.fixture(scope="session")
def shell(client: ops.pebble.Client):
    """Fixture to create a shell."""
    shell = pebble_shell.shell.PebbleShell(client=client)
    yield shell
