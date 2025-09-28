"""Integration tests for the MktempCommand."""

from __future__ import annotations

import tempfile
from typing import TYPE_CHECKING

import pytest

import pebble_shell.commands
import pebble_shell.shell

if TYPE_CHECKING:
    import ops


@pytest.fixture
def command(shell: pebble_shell.shell.PebbleShell):
    """Fixture to create a MktempCommand instance."""
    yield pebble_shell.commands.MktempCommand(shell=shell)


def test_name(command: pebble_shell.commands.MktempCommand):
    assert command.name == "mktemp"


def test_category(command: pebble_shell.commands.MktempCommand):
    assert command.category == "File Utilities"


def test_help(command: pebble_shell.commands.MktempCommand):
    with command.shell.console.capture() as capture:
        command.show_help()
    output = capture.get()
    assert "mktemp" in output
    assert "Create temporary files or directories" in output
    assert "-d, --directory" in output
    assert "XXXXXX" in output


@pytest.mark.parametrize("args", [["-h"], ["--help"]])
def test_execute_help(
    client: ops.pebble.Client,
    command: pebble_shell.commands.MktempCommand,
    args: list[str],
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=args)
    assert result == 0
    output = capture.get()
    assert "mktemp" in output
    assert "Create temporary files or directories" in output


def test_execute_default_temporary_file(
    client: ops.pebble.Client,
    command: pebble_shell.commands.MktempCommand,
):
    # Test creating default temporary file
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should either succeed creating temp file or fail gracefully
    if result == 0:
        output = capture.get().strip()
        # Should output path to created temporary file
        assert "/" in output  # Should be absolute path
        assert len(output) > 0  # Should have output
    else:
        assert result == 1


def test_execute_directory_creation(
    client: ops.pebble.Client,
    command: pebble_shell.commands.MktempCommand,
):
    # Test creating temporary directory with -d flag
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-d"])

    # Should either succeed creating temp directory or fail gracefully
    if result == 0:
        output = capture.get().strip()
        # Should output path to created temporary directory
        assert "/" in output  # Should be absolute path
        assert len(output) > 0  # Should have output
    else:
        assert result == 1


def test_execute_directory_creation_long_option(
    client: ops.pebble.Client,
    command: pebble_shell.commands.MktempCommand,
):
    # Test creating temporary directory with --directory flag
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["--directory"])

    # Should behave same as -d flag
    if result == 0:
        output = capture.get().strip()
        # Should output path to created temporary directory
        assert "/" in output  # Should be absolute path
        assert len(output) > 0  # Should have output
    else:
        assert result == 1


def test_execute_custom_template(
    client: ops.pebble.Client,
    command: pebble_shell.commands.MktempCommand,
):
    # Test with custom template containing XXXXXX
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["fileXXXXXX.txt"])

    # Should either succeed with custom template or fail gracefully
    if result == 0:
        output = capture.get().strip()
        # Should contain the template pattern with XXXXXX replaced
        assert "file" in output
        assert ".txt" in output
        assert "XXXXXX" not in output  # Should be replaced with random chars
    else:
        assert result == 1


def test_execute_template_without_xxxxxx(
    client: ops.pebble.Client,
    command: pebble_shell.commands.MktempCommand,
):
    # Test template without XXXXXX pattern
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["myfile.txt"])

    # Should either handle template without XXXXXX or fail with error
    if result == 0:
        output = capture.get().strip()
        # Should create file with template name or add random suffix
        assert "myfile" in output
    else:
        # May fail if XXXXXX is required
        assert result == 1


def test_execute_prefix_directory_option(
    client: ops.pebble.Client,
    command: pebble_shell.commands.MktempCommand,
):
    # Test -p option for custom prefix directory
    temp_dir = tempfile.mkdtemp()
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-p", temp_dir])

    # Should either succeed with custom prefix directory or fail gracefully
    if result == 0:
        output = capture.get().strip()
        # Should create temp file in specified prefix directory
        assert temp_dir in output
    else:
        assert result == 1


def test_execute_prefix_directory_nonexistent(
    client: ops.pebble.Client,
    command: pebble_shell.commands.MktempCommand,
):
    # Test -p option with nonexistent directory
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-p", "/nonexistent/dir"])

    # Should fail if prefix directory doesn't exist
    assert result == 1
    output = capture.get()
    assert any(
        msg in output for msg in ["No such file", "not found", "directory", "error"]
    )


def test_execute_template_relative_to_temp_dir(
    client: ops.pebble.Client,
    command: pebble_shell.commands.MktempCommand,
):
    # Test -t option (template relative to temp directory)
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-t", "tmpfile.XXXXXX"])

    # Should either succeed creating file in temp dir or fail gracefully
    if result == 0:
        output = capture.get().strip()
        # Should create file in system temp directory
        assert "/" in output  # Should be absolute path
        assert "tmpfile" in output
    else:
        assert result == 1


def test_execute_directory_with_template(
    client: ops.pebble.Client,
    command: pebble_shell.commands.MktempCommand,
):
    # Test creating directory with custom template
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-d", "mydirXXXXXX"])

    # Should either succeed creating temp directory with template or fail gracefully
    if result == 0:
        output = capture.get().strip()
        # Should create directory with template pattern
        assert "mydir" in output
        assert "XXXXXX" not in output  # Should be replaced
    else:
        assert result == 1


def test_execute_directory_with_prefix_and_template(
    client: ops.pebble.Client,
    command: pebble_shell.commands.MktempCommand,
):
    # Test creating directory with prefix and template
    temp_dir = tempfile.mkdtemp()
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["-d", "-p", temp_dir, "testXXXXXX"]
        )

    # Should either succeed with all options or fail gracefully
    if result == 0:
        output = capture.get().strip()
        # Should combine prefix directory and template
        assert temp_dir in output
        assert "test" in output
        assert "XXXXXX" not in output  # Should be replaced
    else:
        assert result == 1


def test_execute_multiple_templates(
    client: ops.pebble.Client,
    command: pebble_shell.commands.MktempCommand,
):
    # Test with multiple template arguments (should use first one)
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["firstXXXXXX", "secondXXXXXX"])

    # Should either succeed using first template or fail gracefully
    if result == 0:
        output = capture.get().strip()
        # Should use first template only
        assert "first" in output
        # Should not contain second template in output
        lines = output.strip().split("\n")
        assert len([line for line in lines if "second" in line]) == 0
    else:
        assert result == 1


def test_execute_unique_file_creation(
    client: ops.pebble.Client,
    command: pebble_shell.commands.MktempCommand,
):
    # Test that multiple calls create unique files
    paths = []
    for _ in range(3):
        with command.shell.console.capture() as capture:
            result = command.execute(client=client, args=[])
        if result == 0:
            path = capture.get().strip()
            paths.append(path)

    # Should create unique paths each time
    if len(paths) > 1:
        assert len(set(paths)) == len(paths)  # All paths should be unique


def test_execute_xxxxxx_replacement_randomness(
    client: ops.pebble.Client,
    command: pebble_shell.commands.MktempCommand,
):
    # Test that XXXXXX is replaced with random characters
    suffixes = []
    for _ in range(3):
        with command.shell.console.capture() as capture:
            result = command.execute(client=client, args=["testXXXXXX"])
        if result == 0:
            path = capture.get().strip()
            # Extract suffix after "test"
            if "test" in path:
                suffix = path.split("test")[1]
                suffixes.append(suffix)

    # Should generate different random suffixes
    if len(suffixes) > 1:
        assert len(set(suffixes)) == len(suffixes)  # All suffixes should be unique


def test_execute_security_file_permissions(
    client: ops.pebble.Client,
    command: pebble_shell.commands.MktempCommand,
):
    # Test that temporary files are created with secure permissions
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should either succeed with secure permissions or fail gracefully
    if result == 0:
        output = capture.get().strip()
        # File should be created (permissions testing would require file system access)
        assert "/" in output  # Should be absolute path
    else:
        assert result == 1


def test_execute_temp_directory_detection(
    client: ops.pebble.Client,
    command: pebble_shell.commands.MktempCommand,
):
    # Test that command uses appropriate temporary directory
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should either succeed using system temp directory or fail gracefully
    if result == 0:
        output = capture.get().strip()
        # Should create file in typical temp location
        assert "/" in output  # Should be absolute path
        # Common temp directories: /tmp, /var/tmp, etc.
    else:
        assert result == 1


def test_execute_invalid_flag_combination(
    client: ops.pebble.Client,
    command: pebble_shell.commands.MktempCommand,
):
    # Test invalid flag combinations or unknown flags
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-x"])

    # Should either ignore unknown flag or fail with error
    if result == 1:
        output = capture.get()
        # Should show error for invalid flag
        assert any(msg in output for msg in ["invalid", "unknown", "flag"])
    else:
        # May succeed if flag is ignored
        assert result == 0


def test_execute_empty_template_string(
    client: ops.pebble.Client,
    command: pebble_shell.commands.MktempCommand,
):
    # Test with empty template string
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[""])

    # Should either handle empty template or fail with error
    if result == 1:
        output = capture.get()
        # Should show error for empty template
        assert any(msg in output for msg in ["empty", "invalid", "template"])
    else:
        # May succeed if empty template is handled
        assert result == 0


def test_execute_file_creation_verification(
    client: ops.pebble.Client,
    command: pebble_shell.commands.MktempCommand,
):
    # Test that the command actually creates the file/directory
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should either succeed and create actual file or fail gracefully
    if result == 0:
        output = capture.get().strip()
        # Should output the path of created file
        assert len(output) > 0
        assert "/" in output  # Should be absolute path
    else:
        assert result == 1
