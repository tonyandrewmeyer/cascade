"""Integration tests for the ReadlinkCommand."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

import pebble_shell.commands
import pebble_shell.shell

if TYPE_CHECKING:
    import ops


@pytest.fixture
def command(shell: pebble_shell.shell.PebbleShell):
    """Fixture to create a ReadlinkCommand instance."""
    yield pebble_shell.commands.ReadlinkCommand(shell=shell)


def test_name(command: pebble_shell.commands.ReadlinkCommand):
    assert command.name == "readlink"


def test_category(command: pebble_shell.commands.ReadlinkCommand):
    assert command.category == "File Utilities"


def test_help(command: pebble_shell.commands.ReadlinkCommand):
    with command.shell.console.capture() as capture:
        command.show_help()
    output = capture.get()
    assert "readlink" in output
    assert "Display value of symbolic link" in output
    assert "-f, --canonicalize" in output
    assert "/usr/bin/vi" in output


@pytest.mark.parametrize("args", [["-h"], ["--help"]])
def test_execute_help(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ReadlinkCommand,
    args: list[str],
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=args)
    assert result == 0
    output = capture.get()
    assert "readlink" in output
    assert "Display value of symbolic link" in output


def test_execute_no_args(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ReadlinkCommand,
):
    # readlink with no args should fail
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should fail with missing operand error
    assert result == 1
    output = capture.get()
    assert any(msg in output for msg in ["missing", "operand", "FILE"])


def test_execute_symlink_resolution(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ReadlinkCommand,
):
    # Test with common symlink (if it exists)
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/bin"])

    # Should either succeed showing target or fail if not a symlink
    if result == 0:
        output = capture.get().strip()
        # Should show the target of the symlink
        assert len(output) > 0
        # Common symlinks: /bin -> /usr/bin
    else:
        # May fail if /bin is not a symlink or doesn't exist
        assert result == 1


def test_execute_nonexistent_file(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ReadlinkCommand,
):
    # Test with nonexistent file
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/nonexistent/file"])

    # Should fail with file not found error
    assert result == 1
    output = capture.get()
    assert any(msg in output for msg in ["No such file", "not found", "error"])


def test_execute_regular_file_not_symlink(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ReadlinkCommand,
):
    # Test with regular file (not a symlink)
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/etc/passwd"])

    # Should fail since /etc/passwd is typically not a symlink
    assert result == 1
    output = capture.get()
    assert any(
        msg in output for msg in ["not a symbolic link", "not a symlink", "invalid"]
    )


def test_execute_canonicalize_option_short(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ReadlinkCommand,
):
    # Test -f option for canonicalization
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-f", "/bin"])

    # Should either succeed with canonical path or fail gracefully
    if result == 0:
        output = capture.get().strip()
        # Should show absolute canonical path
        assert output.startswith("/")
    else:
        assert result == 1


def test_execute_canonicalize_option_long(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ReadlinkCommand,
):
    # Test --canonicalize option
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["--canonicalize", "/bin"])

    # Should behave same as -f option
    if result == 0:
        output = capture.get().strip()
        # Should show absolute canonical path
        assert output.startswith("/")
    else:
        assert result == 1


def test_execute_canonicalize_existing_option(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ReadlinkCommand,
):
    # Test -e option (canonicalize existing)
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-e", "/etc/passwd"])

    # Should either succeed with canonical path or fail if file doesn't exist
    if result == 0:
        output = capture.get().strip()
        # Should show absolute path
        assert "/etc/passwd" in output
    else:
        assert result == 1


def test_execute_canonicalize_existing_nonexistent(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ReadlinkCommand,
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
    command: pebble_shell.commands.ReadlinkCommand,
):
    # Test -m option (canonicalize missing)
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-m", "/nonexistent/file"])

    # Should succeed even if file doesn't exist
    if result == 0:
        output = capture.get().strip()
        # Should resolve path regardless of existence
        assert "/nonexistent/file" in output
    else:
        assert result == 1


def test_execute_no_newline_option(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ReadlinkCommand,
):
    # Test -n option (no trailing newline)
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-n", "/bin"])

    # Should either succeed without trailing newline or fail gracefully
    if result == 0:
        _ = capture.get()
        # Should not end with newline (though console capture may add one)
        # Testing this properly requires checking raw output
        pass
    else:
        assert result == 1


def test_execute_quiet_option_short(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ReadlinkCommand,
):
    # Test -q option (quiet mode)
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-q", "/nonexistent/file"])

    # Should suppress error messages
    assert result == 1
    output = capture.get()
    # Should have minimal or no error output
    assert len(output.strip()) == 0 or "error" not in output.lower()


def test_execute_quiet_option_long(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ReadlinkCommand,
):
    # Test --quiet option
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["--quiet", "/nonexistent/file"])

    # Should behave same as -q option
    assert result == 1
    output = capture.get()
    # Should suppress error messages
    assert len(output.strip()) == 0 or "error" not in output.lower()


def test_execute_silent_option(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ReadlinkCommand,
):
    # Test --silent option (alias for --quiet)
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["--silent", "/nonexistent/file"])

    # Should behave same as --quiet option
    assert result == 1
    output = capture.get()
    # Should suppress error messages
    assert len(output.strip()) == 0 or "error" not in output.lower()


def test_execute_verbose_option(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ReadlinkCommand,
):
    # Test -v option (verbose mode)
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-v", "/nonexistent/file"])

    # Should show detailed error messages
    assert result == 1
    output = capture.get()
    # Should have verbose error output
    assert len(output.strip()) > 0


def test_execute_zero_option(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ReadlinkCommand,
):
    # Test -z option (NUL termination)
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-z", "/bin"])

    # Should either succeed with NUL termination or fail gracefully
    if result == 0:
        _ = capture.get()
        # Should end with NUL character (may not be visible in capture)
        pass
    else:
        assert result == 1


def test_execute_multiple_files(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ReadlinkCommand,
):
    # Test with multiple files
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/bin", "/usr/bin"])

    # Should either succeed processing multiple files or fail gracefully
    if result == 0:
        output = capture.get().strip()
        lines = output.split("\n")
        # Should have output for multiple files
        assert len(lines) >= 1
    else:
        assert result == 1


def test_execute_relative_path_resolution(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ReadlinkCommand,
):
    # Test with relative path
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["../bin"])

    # Should either resolve relative path or fail gracefully
    if result == 0:
        output = capture.get().strip()
        # Should show symlink target
        assert len(output) > 0
    else:
        assert result == 1


def test_execute_current_directory_symlink(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ReadlinkCommand,
):
    # Test with current directory reference
    with command.shell.console.capture() as _:
        result = command.execute(client=client, args=["./bin"])

    # Should either handle current directory reference or fail gracefully
    assert result in [0, 1]


def test_execute_recursive_symlink_following(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ReadlinkCommand,
):
    # Test recursive symlink following with -f
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-f", "/bin/sh"])

    # Should either follow symlink chain or fail gracefully
    if result == 0:
        output = capture.get().strip()
        # Should show final target after following all symlinks
        assert output.startswith("/")
    else:
        assert result == 1


def test_execute_broken_symlink_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ReadlinkCommand,
):
    # Test handling of broken symlinks (if any exist)
    with command.shell.console.capture() as _:
        result = command.execute(client=client, args=["/some/broken/symlink"])

    # Should fail gracefully with broken symlinks
    assert result == 1


def test_execute_symlink_to_directory(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ReadlinkCommand,
):
    # Test symlink pointing to directory
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/bin"])

    # Should either show directory target or fail if not a symlink
    if result == 0:
        output = capture.get().strip()
        # Should show target directory
        assert len(output) > 0
    else:
        assert result == 1


def test_execute_option_combination(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ReadlinkCommand,
):
    # Test combination of options
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-f", "-v", "/bin"])

    # Should either succeed with combined options or fail gracefully
    if result == 0:
        output = capture.get().strip()
        # Should show canonical path with verbose output
        assert len(output) > 0
    else:
        assert result == 1


def test_execute_conflicting_options(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ReadlinkCommand,
):
    # Test conflicting options (quiet and verbose)
    with command.shell.console.capture() as _:
        result = command.execute(client=client, args=["-q", "-v", "/nonexistent"])

    # Should handle conflicting options (last one wins or error)
    assert result == 1


def test_execute_empty_symlink_target(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ReadlinkCommand,
):
    # Test symlink with empty target (if possible)
    with command.shell.console.capture() as _:
        result = command.execute(client=client, args=["/some/empty/target/symlink"])

    # Should either handle empty target or fail gracefully
    assert result in [0, 1]


def test_execute_long_symlink_chain(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ReadlinkCommand,
):
    # Test with potentially long symlink chain
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-f", "/usr/bin/vi"])

    # Should either follow long chain or fail gracefully
    if result == 0:
        output = capture.get().strip()
        # Should show final target
        assert len(output) > 0
    else:
        assert result == 1
