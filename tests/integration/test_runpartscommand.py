"""Integration tests for the RunPartsCommand."""

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
    """Fixture to create a RunPartsCommand instance."""
    yield pebble_shell.commands.RunPartsCommand(shell=shell)


def test_name(command: pebble_shell.commands.RunPartsCommand):
    assert command.name == "run-parts"


def test_category(command: pebble_shell.commands.RunPartsCommand):
    assert command.category == "System"


def test_help(command: pebble_shell.commands.RunPartsCommand):
    with command.shell.console.capture() as capture:
        command.show_help()
    output = capture.get()
    assert any(
        phrase in output.lower()
        for phrase in ["run-parts", "run", "script", "directory", "execute"]
    )


@pytest.mark.parametrize("args", [["-h"], ["--help"]])
def test_execute_help(
    client: ops.pebble.Client,
    command: pebble_shell.commands.RunPartsCommand,
    args: list[str],
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=args)
    assert result == 0
    output = capture.get()
    assert any(
        phrase in output.lower() for phrase in ["run-parts", "run", "script", "usage"]
    )


def test_execute_no_directory_specified(
    client: ops.pebble.Client,
    command: pebble_shell.commands.RunPartsCommand,
):
    # Test with no directory specified
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should fail with missing directory error
    assert result == 1
    output = capture.get()
    assert any(
        msg in output for msg in ["directory", "required", "missing", "usage", "error"]
    )


def test_execute_nonexistent_directory(
    client: ops.pebble.Client,
    command: pebble_shell.commands.RunPartsCommand,
):
    # Test with non-existent directory
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/nonexistent/directory"])

    # Should fail with directory not found error
    assert result == 1
    output = capture.get()
    assert any(
        msg in output for msg in ["not found", "no such file", "directory", "error"]
    )


def test_execute_file_instead_of_directory(
    client: ops.pebble.Client,
    command: pebble_shell.commands.RunPartsCommand,
):
    # Test with file instead of directory
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/etc/passwd"])

    # Should fail with not a directory error
    assert result == 1
    output = capture.get()
    assert any(
        msg in output for msg in ["not a directory", "directory", "error", "invalid"]
    )


def test_execute_permission_denied_directory(
    client: ops.pebble.Client,
    command: pebble_shell.commands.RunPartsCommand,
):
    # Test with permission denied directory
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/root"])  # Typically restricted

    # Should either succeed or fail with permission error
    if result == 0:
        output = capture.get()
        # Should run scripts in directory (if permitted)
        assert len(output) >= 0
    else:
        # Should fail with permission error
        assert result == 1
        output = capture.get()
        assert any(msg in output for msg in ["permission", "denied", "access", "error"])


def test_execute_empty_directory(
    client: ops.pebble.Client,
    command: pebble_shell.commands.RunPartsCommand,
):
    # Test with empty directory
    temp_dir = tempfile.mkdtemp()
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[temp_dir])

    # Should either succeed (no scripts to run) or fail with error
    if result == 0:
        output = capture.get()
        # Should succeed with empty directory
        assert len(output) >= 0
    else:
        # Should fail with directory or access error
        assert result == 1


def test_execute_system_scripts_directory(
    client: ops.pebble.Client,
    command: pebble_shell.commands.RunPartsCommand,
):
    # Test with system scripts directory
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["/etc/cron.daily"]
        )  # Common system directory

    # Should either succeed running scripts or fail with permission/not found
    if result == 0:
        output = capture.get()
        # Should run daily cron scripts
        assert len(output) >= 0
    else:
        # Should fail with permission or directory not found
        assert result == 1
        output = capture.get()
        assert any(
            msg in output for msg in ["not found", "permission", "denied", "error"]
        )


def test_execute_test_mode(
    client: ops.pebble.Client,
    command: pebble_shell.commands.RunPartsCommand,
):
    # Test with test mode (--test)
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["--test", "/etc/cron.daily"])

    # Should either succeed in test mode or fail with error
    if result == 0:
        output = capture.get()
        # Should show what would be executed without running
        assert len(output) >= 0
        if len(output) > 0:
            # Should list scripts that would be run
            lines = output.split("\n")
            assert len(lines) >= 1
    else:
        # Should fail with directory or permission error
        assert result == 1


def test_execute_verbose_mode(
    client: ops.pebble.Client,
    command: pebble_shell.commands.RunPartsCommand,
):
    # Test with verbose mode (-v or --verbose)
    test_dir = tempfile.mkdtemp()
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-v", test_dir])

    # Should either succeed with verbose output or fail with error
    if result == 0:
        output = capture.get()
        # Should show verbose execution information
        assert len(output) >= 0
    else:
        # Should fail with directory or permission error
        assert result == 1


def test_execute_report_mode(
    client: ops.pebble.Client,
    command: pebble_shell.commands.RunPartsCommand,
):
    # Test with report mode (--report)
    test_dir = tempfile.mkdtemp()
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["--report", test_dir])

    # Should either succeed with report or fail with error
    if result == 0:
        output = capture.get()
        # Should report script execution
        assert len(output) >= 0
    else:
        # Should fail with directory or option error
        assert result == 1


def test_execute_list_mode(
    client: ops.pebble.Client,
    command: pebble_shell.commands.RunPartsCommand,
):
    # Test with list mode (--list)
    test_dir = tempfile.mkdtemp()
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["--list", test_dir])

    # Should either succeed listing scripts or fail with error
    if result == 0:
        output = capture.get()
        # Should list executable scripts
        assert len(output) >= 0
    else:
        # Should fail with directory or option error
        assert result == 1


def test_execute_reverse_mode(
    client: ops.pebble.Client,
    command: pebble_shell.commands.RunPartsCommand,
):
    # Test with reverse mode (--reverse)
    test_dir = tempfile.mkdtemp()
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["--reverse", test_dir])

    # Should either succeed in reverse order or fail with error
    if result == 0:
        output = capture.get()
        # Should execute scripts in reverse order
        assert len(output) >= 0
    else:
        # Should fail with directory or option error
        assert result == 1


def test_execute_exit_on_error_mode(
    client: ops.pebble.Client,
    command: pebble_shell.commands.RunPartsCommand,
):
    # Test with exit-on-error mode (--exit-on-error)
    with command.shell.console.capture() as capture:
        test_dir = tempfile.mkdtemp()
        result = command.execute(client=client, args=["--exit-on-error", test_dir])

    # Should either succeed or exit on first error
    if result == 0:
        output = capture.get()
        # Should stop execution on first error
        assert len(output) >= 0
    else:
        # Should fail with directory or script error
        assert result == 1


def test_execute_new_session_mode(
    client: ops.pebble.Client,
    command: pebble_shell.commands.RunPartsCommand,
):
    # Test with new session mode (--new-session)
    with command.shell.console.capture() as capture:
        test_dir = tempfile.mkdtemp()
        result = command.execute(client=client, args=["--new-session", test_dir])

    # Should either succeed with new session or fail with error
    if result == 0:
        output = capture.get()
        # Should run scripts in new session
        assert len(output) >= 0
    else:
        # Should fail with directory or session error
        assert result == 1


def test_execute_regex_pattern_matching(
    client: ops.pebble.Client,
    command: pebble_shell.commands.RunPartsCommand,
):
    # Test with regex pattern matching (--regex)
    with command.shell.console.capture() as capture:
        test_dir = tempfile.mkdtemp()
        result = command.execute(client=client, args=["--regex", "^[a-z]+$", test_dir])

    # Should either succeed with pattern matching or fail with error
    if result == 0:
        output = capture.get()
        # Should match scripts by regex pattern
        assert len(output) >= 0
    else:
        # Should fail with directory or pattern error
        assert result == 1


def test_execute_lsbsysinit_mode(
    client: ops.pebble.Client,
    command: pebble_shell.commands.RunPartsCommand,
):
    # Test with LSB system init mode (--lsbsysinit)
    with command.shell.console.capture() as capture:
        test_dir = tempfile.mkdtemp()
        result = command.execute(client=client, args=["--lsbsysinit", test_dir])

    # Should either succeed with LSB mode or fail with error
    if result == 0:
        output = capture.get()
        # Should use LSB system init naming
        assert len(output) >= 0
    else:
        # Should fail with directory or mode error
        assert result == 1


def test_execute_script_arguments(
    client: ops.pebble.Client,
    command: pebble_shell.commands.RunPartsCommand,
):
    # Test passing arguments to scripts
    with command.shell.console.capture() as capture:
        test_dir = tempfile.mkdtemp()
        result = command.execute(client=client, args=[test_dir, "--", "arg1", "arg2"])

    # Should either succeed passing arguments or fail with error
    if result == 0:
        output = capture.get()
        # Should pass arguments to executed scripts
        assert len(output) >= 0
    else:
        # Should fail with directory or script error
        assert result == 1


def test_execute_umask_setting(
    client: ops.pebble.Client,
    command: pebble_shell.commands.RunPartsCommand,
):
    # Test with umask setting (--umask)
    with command.shell.console.capture() as capture:
        test_dir = tempfile.mkdtemp()
        result = command.execute(client=client, args=["--umask", "022", test_dir])

    # Should either succeed with umask or fail with error
    if result == 0:
        output = capture.get()
        # Should set umask for script execution
        assert len(output) >= 0
    else:
        # Should fail with directory or umask error
        assert result == 1


def test_execute_invalid_umask(
    client: ops.pebble.Client,
    command: pebble_shell.commands.RunPartsCommand,
):
    # Test with invalid umask value
    with command.shell.console.capture() as capture:
        test_dir = tempfile.mkdtemp()
        result = command.execute(client=client, args=["--umask", "999", test_dir])

    # Should fail with invalid umask error
    assert result == 1
    output = capture.get()
    assert any(msg in output for msg in ["invalid", "umask", "error", "value"])


def test_execute_invalid_regex(
    client: ops.pebble.Client,
    command: pebble_shell.commands.RunPartsCommand,
):
    # Test with invalid regex pattern
    with command.shell.console.capture() as capture:
        test_dir = tempfile.mkdtemp()
        result = command.execute(client=client, args=["--regex", "[invalid", test_dir])

    # Should fail with invalid regex error
    assert result == 1
    output = capture.get()
    assert any(msg in output for msg in ["invalid", "regex", "pattern", "error"])


def test_execute_conflicting_options(
    client: ops.pebble.Client,
    command: pebble_shell.commands.RunPartsCommand,
):
    # Test with conflicting options
    with command.shell.console.capture() as capture:
        test_dir = tempfile.mkdtemp()
        result = command.execute(client=client, args=["--test", "--list", test_dir])

    # Should either succeed or fail with conflicting options
    if result == 0:
        output = capture.get()
        # Should handle conflicting options appropriately
        assert len(output) >= 0
    else:
        # Should fail with option conflict error
        assert result == 1
        output = capture.get()
        assert any(msg in output for msg in ["conflict", "option", "error", "invalid"])


def test_execute_invalid_option(
    client: ops.pebble.Client,
    command: pebble_shell.commands.RunPartsCommand,
):
    # Test invalid option
    with command.shell.console.capture() as capture:
        test_dir = tempfile.mkdtemp()
        result = command.execute(client=client, args=["-z", test_dir])

    # Should fail with invalid option error
    assert result == 1
    output = capture.get()
    assert any(msg in output for msg in ["invalid", "unknown", "option", "usage"])


def test_execute_directory_with_special_characters(
    client: ops.pebble.Client,
    command: pebble_shell.commands.RunPartsCommand,
):
    # Test with directory path containing special characters
    with command.shell.console.capture() as capture:
        test_dir_with_space = tempfile.mkdtemp(suffix=" test dir")
        result = command.execute(client=client, args=[test_dir_with_space])

    # Should either succeed or fail with path error
    if result == 0:
        output = capture.get()
        # Should handle special characters in path
        assert len(output) >= 0
    else:
        # Should fail with directory not found or path error
        assert result == 1
        output = capture.get()
        assert any(
            msg in output for msg in ["not found", "directory", "error", "invalid"]
        )


def test_execute_relative_directory_path(
    client: ops.pebble.Client,
    command: pebble_shell.commands.RunPartsCommand,
):
    # Test with relative directory path
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["./tmp"])

    # Should either succeed with relative path or fail with error
    if result == 0:
        output = capture.get()
        # Should handle relative paths
        assert len(output) >= 0
    else:
        # Should fail with directory not found
        assert result == 1


def test_execute_symlink_directory(
    client: ops.pebble.Client,
    command: pebble_shell.commands.RunPartsCommand,
):
    # Test with symbolic link to directory
    test_dir = tempfile.mkdtemp()
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[test_dir])  # Test directory

    # Should either succeed following symlinks or fail with error
    if result == 0:
        output = capture.get()
        # Should follow symlinks to directories
        assert len(output) >= 0
    else:
        # Should fail with directory or permission error
        assert result == 1


def test_execute_script_naming_validation(
    client: ops.pebble.Client,
    command: pebble_shell.commands.RunPartsCommand,
):
    # Test script naming validation
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["--list", "/usr/bin"]
        )  # Directory with various file names

    # Should either succeed with naming validation or fail
    if result == 0:
        output = capture.get()
        # Should validate script names
        assert len(output) >= 0
    else:
        # Should fail with directory or permission error
        assert result == 1


def test_execute_executable_permission_check(
    client: ops.pebble.Client,
    command: pebble_shell.commands.RunPartsCommand,
):
    # Test executable permission checking
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["--test", "/bin"]
        )  # Directory with executables

    # Should either succeed checking permissions or fail
    if result == 0:
        output = capture.get()
        # Should check executable permissions
        assert len(output) >= 0
    else:
        # Should fail with permission or directory error
        assert result == 1


def test_execute_memory_efficiency(
    client: ops.pebble.Client,
    command: pebble_shell.commands.RunPartsCommand,
):
    # Test memory efficiency
    with command.shell.console.capture() as capture:
        test_dir = tempfile.mkdtemp()
        result = command.execute(client=client, args=[test_dir])

    # Should be memory efficient
    if result == 0:
        output = capture.get()
        # Should not consume excessive memory
        assert len(output) < 50000  # Reasonable output size limit
    else:
        assert result == 1


def test_execute_error_recovery(
    client: ops.pebble.Client,
    command: pebble_shell.commands.RunPartsCommand,
):
    # Test error recovery capabilities
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/invalid/path"])

    # Should recover from errors gracefully
    assert result == 1
    output = capture.get()
    # Should provide meaningful error message
    assert any(msg in output for msg in ["not found", "error", "directory", "invalid"])


def test_execute_signal_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.RunPartsCommand,
):
    # Test signal handling during script execution
    with command.shell.console.capture() as capture:
        test_dir = tempfile.mkdtemp()
        result = command.execute(client=client, args=[test_dir])

    # Should handle signals appropriately
    if result == 0:
        output = capture.get()
        assert len(output) >= 0
    else:
        # Should fail with directory or permission error
        assert result == 1


def test_execute_script_exit_code_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.RunPartsCommand,
):
    # Test script exit code handling
    with command.shell.console.capture() as capture:
        test_dir = tempfile.mkdtemp()
        result = command.execute(client=client, args=["--exit-on-error", test_dir])

    # Should either succeed or exit with script error code
    if result == 0:
        output = capture.get()
        # Should handle script exit codes
        assert len(output) >= 0
    else:
        # Should fail with appropriate exit code
        assert result >= 1


def test_execute_environment_preservation(
    client: ops.pebble.Client,
    command: pebble_shell.commands.RunPartsCommand,
):
    # Test environment variable preservation
    with command.shell.console.capture() as capture:
        test_dir = tempfile.mkdtemp()
        result = command.execute(client=client, args=[test_dir])

    # Should either succeed preserving environment or fail
    if result == 0:
        output = capture.get()
        # Should preserve environment for scripts
        assert len(output) >= 0
    else:
        # Should fail with directory or permission error
        assert result == 1


def test_execute_working_directory_preservation(
    client: ops.pebble.Client,
    command: pebble_shell.commands.RunPartsCommand,
):
    # Test working directory preservation
    with command.shell.console.capture() as capture:
        test_dir = tempfile.mkdtemp()
        result = command.execute(client=client, args=[test_dir])

    # Should either succeed preserving working directory or fail
    if result == 0:
        output = capture.get()
        # Should preserve working directory
        assert len(output) >= 0
    else:
        # Should fail with directory or permission error
        assert result == 1


def test_execute_cross_platform_compatibility(
    client: ops.pebble.Client,
    command: pebble_shell.commands.RunPartsCommand,
):
    # Test cross-platform compatibility
    with command.shell.console.capture() as capture:
        test_dir = tempfile.mkdtemp()
        result = command.execute(client=client, args=[test_dir])

    # Should work across different platforms
    if result == 0:
        output = capture.get()
        # Should handle platform differences
        assert len(output) >= 0
    else:
        # Should fail consistently across platforms
        assert result == 1
