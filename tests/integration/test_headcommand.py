"""Integration tests for the HeadCommand."""

from __future__ import annotations

import os
import tempfile
from typing import TYPE_CHECKING

import pytest

import pebble_shell.commands
import pebble_shell.shell

if TYPE_CHECKING:
    import ops


@pytest.fixture
def command(shell: pebble_shell.shell.PebbleShell):
    """Fixture to create a HeadCommand instance."""
    yield pebble_shell.commands.HeadCommand(shell=shell)


def test_name(command: pebble_shell.commands.HeadCommand):
    assert command.name == "head"


def test_category(command: pebble_shell.commands.HeadCommand):
    assert command.category == "Filesystem Commands"


def test_help(command: pebble_shell.commands.HeadCommand):
    with command.shell.console.capture() as capture:
        command.show_help()
    assert "Display first lines of file" in capture.get()


@pytest.mark.parametrize("args", [["-h"], ["--help"]])
def test_execute_help(
    client: ops.pebble.Client,
    command: pebble_shell.commands.HeadCommand,
    args: list[str],
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=args)
    assert result == 0
    assert "Display first lines of file" in capture.get()


def test_execute_no_args(
    client: ops.pebble.Client,
    command: pebble_shell.commands.HeadCommand,
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])
    assert result == 1
    assert "Error: At least 1 argument(s) required" in capture.get()


def test_execute_with_temp_file(
    client: ops.pebble.Client,
    command: pebble_shell.commands.HeadCommand,
):
    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        temp_file.write(b"Line 1\nLine 2\nLine 3\nLine 4\nLine 5\n")
        temp_file_path = temp_file.name
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[temp_file_path])
    assert result == 0
    output = capture.get()
    assert "Line 1" in output
    assert "Line 2" in output
    assert "Line 3" in output
    assert "Line 4" in output
    assert "Line 5" in output
    os.remove(temp_file_path)


def test_execute_with_lines_option(
    client: ops.pebble.Client,
    command: pebble_shell.commands.HeadCommand,
):
    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        temp_file.write(b"Line 1\nLine 2\nLine 3\nLine 4\nLine 5\n")
        temp_file_path = temp_file.name
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-n", "3", temp_file_path])
    assert result == 0
    output = capture.get()
    assert "Line 1" in output
    assert "Line 2" in output
    assert "Line 3" in output
    assert "Line 4" not in output
    assert "Line 5" not in output
    os.remove(temp_file_path)


def test_execute_default_shows_10_lines(
    client: ops.pebble.Client,
    command: pebble_shell.commands.HeadCommand,
):
    """Default head shows first 10 lines."""
    content = "\n".join([f"Line {i}" for i in range(1, 16)]) + "\n"
    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        temp_file.write(content.encode())
        temp_file_path = temp_file.name
    try:
        with command.shell.console.capture() as capture:
            result = command.execute(client=client, args=[temp_file_path])
        assert result == 0
        output = capture.get()
        for i in range(1, 11):
            assert f"Line {i}" in output
        assert "Line 11" not in output
    finally:
        os.remove(temp_file_path)


def test_execute_n5_shows_first_5_lines(
    client: ops.pebble.Client,
    command: pebble_shell.commands.HeadCommand,
):
    """head -n 5 shows first 5 lines."""
    content = "\n".join([f"Line {i}" for i in range(1, 16)]) + "\n"
    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        temp_file.write(content.encode())
        temp_file_path = temp_file.name
    try:
        with command.shell.console.capture() as capture:
            result = command.execute(client=client, args=["-n", "5", temp_file_path])
        assert result == 0
        output = capture.get()
        for i in range(1, 6):
            assert f"Line {i}" in output
        assert "Line 6" not in output
    finally:
        os.remove(temp_file_path)


def test_execute_c_flag_bytes(
    client: ops.pebble.Client,
    command: pebble_shell.commands.HeadCommand,
):
    """head -c 10 shows first 10 bytes."""
    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        temp_file.write(b"ABCDEFGHIJKLMNOP")
        temp_file_path = temp_file.name
    try:
        with command.shell.console.capture() as capture:
            result = command.execute(client=client, args=["-c", "10", temp_file_path])
        assert result == 0
        output = capture.get()
        assert "ABCDEFGHIJ" in output
        assert "K" not in output
    finally:
        os.remove(temp_file_path)


def test_execute_multiple_files_with_headers(
    client: ops.pebble.Client,
    command: pebble_shell.commands.HeadCommand,
):
    """Multiple files show ==> filename <== headers."""
    with tempfile.NamedTemporaryFile(delete=False, suffix="_a.txt") as f1:
        f1.write(b"File A content\n")
        path1 = f1.name
    with tempfile.NamedTemporaryFile(delete=False, suffix="_b.txt") as f2:
        f2.write(b"File B content\n")
        path2 = f2.name
    try:
        with command.shell.console.capture() as capture:
            result = command.execute(client=client, args=[path1, path2])
        assert result == 0
        output = capture.get()
        assert f"==> {path1} <==" in output
        assert f"==> {path2} <==" in output
        assert "File A content" in output
        assert "File B content" in output
    finally:
        os.remove(path1)
        os.remove(path2)


def test_execute_quiet_suppresses_headers(
    client: ops.pebble.Client,
    command: pebble_shell.commands.HeadCommand,
):
    """head -q suppresses headers even for multiple files."""
    with tempfile.NamedTemporaryFile(delete=False, suffix="_a.txt") as f1:
        f1.write(b"File A\n")
        path1 = f1.name
    with tempfile.NamedTemporaryFile(delete=False, suffix="_b.txt") as f2:
        f2.write(b"File B\n")
        path2 = f2.name
    try:
        with command.shell.console.capture() as capture:
            result = command.execute(client=client, args=["-q", path1, path2])
        assert result == 0
        output = capture.get()
        assert "==>" not in output
        assert "File A" in output
        assert "File B" in output
    finally:
        os.remove(path1)
        os.remove(path2)


def test_execute_verbose_forces_headers(
    client: ops.pebble.Client,
    command: pebble_shell.commands.HeadCommand,
):
    """head -v forces headers even for single file."""
    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        temp_file.write(b"Content here\n")
        temp_file_path = temp_file.name
    try:
        with command.shell.console.capture() as capture:
            result = command.execute(client=client, args=["-v", temp_file_path])
        assert result == 0
        output = capture.get()
        assert f"==> {temp_file_path} <==" in output
        assert "Content here" in output
    finally:
        os.remove(temp_file_path)


def test_execute_exit_code_missing_file(
    client: ops.pebble.Client,
    command: pebble_shell.commands.HeadCommand,
):
    """head returns 1 for missing file."""
    with command.shell.console.capture():
        result = command.execute(client=client, args=["/nonexistent/path/to/file.txt"])
    assert result == 1
