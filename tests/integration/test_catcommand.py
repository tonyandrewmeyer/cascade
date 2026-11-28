"""Integration tests for the CatCommand."""

from __future__ import annotations

import os
import tempfile
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import ops

import pytest

import pebble_shell.commands
import pebble_shell.shell


@pytest.fixture
def command(shell: pebble_shell.shell.PebbleShell):
    """Fixture to create a CatCommand instance."""
    yield pebble_shell.commands.CatCommand(shell=shell)


def test_name(command: pebble_shell.commands.CatCommand):
    assert command.name == "cat"


def test_category(command: pebble_shell.commands.CatCommand):
    assert command.category == "Filesystem Commands"


def test_help(command: pebble_shell.commands.CatCommand):
    with command.shell.console.capture() as capture:
        command.show_help()
    assert "Display file contents" in capture.get()


@pytest.mark.parametrize("args", [["-h"], ["--help"]])
def test_execute_help(
    client: ops.pebble.Client,
    command: pebble_shell.commands.CatCommand,
    args: list[str],
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=args)
    assert result == 0
    assert "Display file contents" in capture.get()


def test_execute_no_args(
    client: ops.pebble.Client,
    command: pebble_shell.commands.CatCommand,
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])
    assert result == 1
    assert "Usage: cat [-nbETAs]" in capture.get()


def test_execute_temp_file(
    client: ops.pebble.Client,
    command: pebble_shell.commands.CatCommand,
):
    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        temp_file.write(b"Hello, World!")
        temp_file_path = temp_file.name
    try:
        with command.shell.console.capture() as capture:
            result = command.execute(client=client, args=[temp_file_path])
        assert result == 0
        assert "Hello, World!" in capture.get()
    finally:
        os.remove(temp_file_path)


def test_execute_nonexistent_file(
    client: ops.pebble.Client,
    command: pebble_shell.commands.CatCommand,
):
    with command.shell.console.capture() as _:
        result = command.execute(client=client, args=["/nonexistent/file"])
    assert result == 1


def _push_temp_file(client: ops.pebble.Client, content: str) -> str:
    """Push content to a temporary file on Pebble and return its path."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as f:
        temp_path = f.name
    client.push(temp_path, content)
    return temp_path


def test_number_lines(
    client: ops.pebble.Client,
    command: pebble_shell.commands.CatCommand,
):
    """Test -n flag numbers all lines correctly."""
    path = _push_temp_file(client, "alpha\nbeta\ngamma\n")
    try:
        with command.shell.console.capture() as capture:
            result = command.execute(client=client, args=["-n", path])
        assert result == 0
        output = capture.get()
        # Rich expands tabs, so check number and content are present on same line
        lines = output.strip().split("\n")
        assert any("1" in ln and "alpha" in ln for ln in lines)
        assert any("2" in ln and "beta" in ln for ln in lines)
        assert any("3" in ln and "gamma" in ln for ln in lines)
    finally:
        os.remove(path)


def test_number_nonblank(
    client: ops.pebble.Client,
    command: pebble_shell.commands.CatCommand,
):
    """Test -b flag numbers only non-blank lines."""
    path = _push_temp_file(client, "alpha\n\nbeta\n")
    try:
        with command.shell.console.capture() as capture:
            result = command.execute(client=client, args=["-b", path])
        assert result == 0
        output = capture.get()
        lines = output.strip().split("\n")
        assert any("1" in ln and "alpha" in ln for ln in lines)
        assert any("2" in ln and "beta" in ln for ln in lines)
        # The blank line should not have a number prefix
        lines = output.strip().split("\n")
        blank_lines = [ln for ln in lines if ln.strip() == ""]
        assert len(blank_lines) >= 1
    finally:
        os.remove(path)


def test_show_ends(
    client: ops.pebble.Client,
    command: pebble_shell.commands.CatCommand,
):
    """Test -E flag shows $ at end of lines."""
    path = _push_temp_file(client, "hello\nworld\n")
    try:
        with command.shell.console.capture() as capture:
            result = command.execute(client=client, args=["-E", path])
        assert result == 0
        output = capture.get()
        assert "hello$" in output
        assert "world$" in output
    finally:
        os.remove(path)


def test_show_tabs(
    client: ops.pebble.Client,
    command: pebble_shell.commands.CatCommand,
):
    """Test -T flag shows ^I for tabs."""
    path = _push_temp_file(client, "col1\tcol2\n")
    try:
        with command.shell.console.capture() as capture:
            result = command.execute(client=client, args=["-T", path])
        assert result == 0
        output = capture.get()
        assert "col1^Icol2" in output
    finally:
        os.remove(path)


def test_show_all(
    client: ops.pebble.Client,
    command: pebble_shell.commands.CatCommand,
):
    """Test -A flag combines -E and -T."""
    path = _push_temp_file(client, "hello\tworld\n")
    try:
        with command.shell.console.capture() as capture:
            result = command.execute(client=client, args=["-A", path])
        assert result == 0
        output = capture.get()
        assert "^I" in output
        assert "$" in output
    finally:
        os.remove(path)


def test_squeeze_blank(
    client: ops.pebble.Client,
    command: pebble_shell.commands.CatCommand,
):
    """Test -s flag squeezes repeated blank lines."""
    path = _push_temp_file(client, "line1\n\n\n\nline2\n")
    try:
        with command.shell.console.capture() as capture:
            result = command.execute(client=client, args=["-s", path])
        assert result == 0
        output = capture.get()
        assert "line1" in output
        assert "line2" in output
        # Should not have 3 consecutive blank lines
        assert "\n\n\n" not in output
    finally:
        os.remove(path)


def test_multiple_files(
    client: ops.pebble.Client,
    command: pebble_shell.commands.CatCommand,
):
    """Test multiple files with headers between them."""
    path1 = _push_temp_file(client, "file1 content\n")
    path2 = _push_temp_file(client, "file2 content\n")
    try:
        with command.shell.console.capture() as capture:
            result = command.execute(client=client, args=[path1, path2])
        assert result == 0
        output = capture.get()
        assert "file1 content" in output
        assert "file2 content" in output
        # Should have file headers
        assert f"==> {path1} <==" in output
        assert f"==> {path2} <==" in output
    finally:
        os.remove(path1)
        os.remove(path2)


def test_exit_code_success(
    client: ops.pebble.Client,
    command: pebble_shell.commands.CatCommand,
):
    """Test exit code is 0 on success."""
    path = _push_temp_file(client, "test\n")
    try:
        with command.shell.console.capture() as _:
            result = command.execute(client=client, args=[path])
        assert result == 0
    finally:
        os.remove(path)


def test_exit_code_missing_file(
    client: ops.pebble.Client,
    command: pebble_shell.commands.CatCommand,
):
    """Test exit code is 1 on missing file."""
    with command.shell.console.capture() as _:
        result = command.execute(client=client, args=["/nonexistent/file.txt"])
    assert result == 1
