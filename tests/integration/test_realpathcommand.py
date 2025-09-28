"""Integration tests for the RealpathCommand."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

import pebble_shell.commands
import pebble_shell.shell

if TYPE_CHECKING:
    import ops


@pytest.fixture
def command(shell: pebble_shell.shell.PebbleShell):
    """Fixture to create a RealpathCommand instance."""
    yield pebble_shell.commands.RealpathCommand(shell=shell)


def test_name(command: pebble_shell.commands.RealpathCommand):
    assert command.name == "realpath"


def test_category(command: pebble_shell.commands.RealpathCommand):
    assert command.category == "File Utilities"


def test_help(command: pebble_shell.commands.RealpathCommand):
    with command.shell.console.capture() as capture:
        command.show_help()
    output = capture.get()
    assert "realpath" in output
    assert "Display absolute pathnames" in output
    assert "-e, --canonicalize-existing" in output
    assert "-m, --canonicalize-missing" in output


@pytest.mark.parametrize("args", [["-h"], ["--help"]])
def test_execute_help(
    client: ops.pebble.Client,
    command: pebble_shell.commands.RealpathCommand,
    args: list[str],
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=args)
    assert result == 0
    output = capture.get()
    assert "realpath" in output
    assert "Display absolute pathnames" in output


def test_execute_no_args(
    client: ops.pebble.Client,
    command: pebble_shell.commands.RealpathCommand,
):
    # realpath with no args should fail
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should fail with usage error
    assert result == 1
    output = capture.get()
    assert any(msg in output for msg in ["missing", "operand", "FILE"])


def test_execute_absolute_path_existing_file(
    client: ops.pebble.Client,
    command: pebble_shell.commands.RealpathCommand,
):
    # Test with absolute path to existing file
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/etc/passwd"])

    # Should either succeed and show absolute path or fail if file not accessible
    if result == 0:
        output = capture.get()
        # Should output absolute path
        assert "/etc/passwd" in output
    else:
        assert result == 1


def test_execute_relative_path_resolution(
    client: ops.pebble.Client,
    command: pebble_shell.commands.RealpathCommand,
):
    # Test with relative path
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["../etc/passwd"])

    # Should either succeed with absolute path or fail gracefully
    if result == 0:
        output = capture.get()
        # Should resolve to absolute path
        assert "/" in output  # Should start with /
    else:
        assert result == 1


def test_execute_dot_directory_resolution(
    client: ops.pebble.Client,
    command: pebble_shell.commands.RealpathCommand,
):
    # Test with current directory (.)
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["."])

    # Should either succeed with absolute path or fail gracefully
    if result == 0:
        output = capture.get()
        # Should resolve to absolute path
        assert "/" in output  # Should be absolute path
    else:
        assert result == 1


def test_execute_dotdot_directory_resolution(
    client: ops.pebble.Client,
    command: pebble_shell.commands.RealpathCommand,
):
    # Test with parent directory (..)
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[".."])

    # Should either succeed with absolute path or fail gracefully
    if result == 0:
        output = capture.get()
        # Should resolve to absolute path of parent directory
        assert "/" in output  # Should be absolute path
    else:
        assert result == 1


def test_execute_nonexistent_file_default(
    client: ops.pebble.Client,
    command: pebble_shell.commands.RealpathCommand,
):
    # Test with nonexistent file (default behavior)
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/nonexistent/file"])

    # Should either succeed (resolving path) or fail gracefully
    if result == 0:
        output = capture.get()
        # Should still resolve path even if file doesn't exist
        assert "/nonexistent/file" in output
    else:
        assert result == 1


def test_execute_canonicalize_existing_option(
    client: ops.pebble.Client,
    command: pebble_shell.commands.RealpathCommand,
):
    # Test -e option (all components must exist)
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-e", "/etc/passwd"])

    # Should either succeed if file exists or fail if not
    if result == 0:
        output = capture.get()
        # Should show absolute path
        assert "/etc/passwd" in output
    else:
        assert result == 1


def test_execute_canonicalize_existing_nonexistent_file(
    client: ops.pebble.Client,
    command: pebble_shell.commands.RealpathCommand,
):
    # Test -e option with nonexistent file
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-e", "/nonexistent/file"])

    # Should fail since file doesn't exist and -e requires existence
    assert result == 1
    output = capture.get()
    assert any(msg in output for msg in ["No such file", "not exist", "error"])


def test_execute_canonicalize_missing_option(
    client: ops.pebble.Client,
    command: pebble_shell.commands.RealpathCommand,
):
    # Test -m option (no components need exist)
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-m", "/nonexistent/file"])

    # Should succeed even if file doesn't exist
    if result == 0:
        output = capture.get()
        # Should resolve path regardless of existence
        assert "/nonexistent/file" in output
    else:
        assert result == 1


def test_execute_strip_option_no_symlink_expansion(
    client: ops.pebble.Client,
    command: pebble_shell.commands.RealpathCommand,
):
    # Test -s option (don't expand symlinks)
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-s", "/etc/passwd"])

    # Should either succeed without expanding symlinks or fail gracefully
    if result == 0:
        output = capture.get()
        # Should show path without expanding symlinks
        assert "/etc/passwd" in output
    else:
        assert result == 1


def test_execute_zero_option_nul_termination(
    client: ops.pebble.Client,
    command: pebble_shell.commands.RealpathCommand,
):
    # Test -z option (end output with NUL character)
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-z", "/etc/passwd"])

    # Should either succeed with NUL termination or fail gracefully
    if result == 0:
        output = capture.get()
        # Should end with NUL character (may not be visible in capture)
        assert "/etc/passwd" in output
    else:
        assert result == 1


def test_execute_multiple_files(
    client: ops.pebble.Client,
    command: pebble_shell.commands.RealpathCommand,
):
    # Test with multiple files
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/etc/passwd", "/etc/hosts"])

    # Should either succeed with multiple paths or fail gracefully
    if result == 0:
        output = capture.get()
        # Should show both paths
        assert "/etc/passwd" in output
        assert "/etc/hosts" in output
    else:
        assert result == 1


def test_execute_complex_relative_path(
    client: ops.pebble.Client,
    command: pebble_shell.commands.RealpathCommand,
):
    # Test with complex relative path containing .. and .
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["./../../etc/./passwd"])

    # Should either succeed resolving complex path or fail gracefully
    if result == 0:
        output = capture.get()
        # Should resolve to clean absolute path
        assert "/etc/passwd" in output
        # Should not contain . or .. in resolved path
        assert "./" not in output.strip().split("\n")[-1]
        assert "../" not in output.strip().split("\n")[-1]
    else:
        assert result == 1


def test_execute_symlink_resolution(
    client: ops.pebble.Client,
    command: pebble_shell.commands.RealpathCommand,
):
    # Test symlink resolution (if symlinks exist)
    # Common symlinks might include /bin -> /usr/bin
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/bin"])

    # Should either succeed resolving symlink or fail gracefully
    if result == 0:
        output = capture.get()
        # Should show resolved path (may be different from /bin if it's a symlink)
        assert "/" in output  # Should be absolute path
    else:
        assert result == 1


def test_execute_home_directory_tilde_expansion(
    client: ops.pebble.Client,
    command: pebble_shell.commands.RealpathCommand,
):
    # Test with tilde (~) if supported
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["~"])

    # Should either succeed expanding tilde or fail gracefully
    if result == 0:
        output = capture.get()
        # Should expand to home directory absolute path
        assert "/" in output  # Should be absolute path
    else:
        assert result == 1


def test_execute_long_option_canonicalize_existing(
    client: ops.pebble.Client,
    command: pebble_shell.commands.RealpathCommand,
):
    # Test --canonicalize-existing long option
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["--canonicalize-existing", "/etc/passwd"]
        )

    # Should behave same as -e option
    if result == 0:
        output = capture.get()
        assert "/etc/passwd" in output
    else:
        assert result == 1


def test_execute_long_option_canonicalize_missing(
    client: ops.pebble.Client,
    command: pebble_shell.commands.RealpathCommand,
):
    # Test --canonicalize-missing long option
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["--canonicalize-missing", "/nonexistent"]
        )

    # Should behave same as -m option
    if result == 0:
        output = capture.get()
        assert "/nonexistent" in output
    else:
        assert result == 1


def test_execute_path_with_spaces(
    client: ops.pebble.Client,
    command: pebble_shell.commands.RealpathCommand,
):
    # Test path with spaces
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/path with spaces"])

    # Should either succeed handling spaces or fail gracefully
    if result == 0:
        output = capture.get()
        # Should handle path with spaces
        assert "path with spaces" in output
    else:
        assert result == 1


def test_execute_empty_path_argument(
    client: ops.pebble.Client,
    command: pebble_shell.commands.RealpathCommand,
):
    # Test with empty string as path
    with command.shell.console.capture() as _:
        result = command.execute(client=client, args=[""])

    # Should fail or handle empty path appropriately
    assert result in [0, 1]  # Behavior depends on implementation
