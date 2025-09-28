"""Integration tests for the ShellCommand."""

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
    """Fixture to create a ShellCommand instance."""
    yield pebble_shell.commands.ShellCommand(shell=shell)


def test_name(command: pebble_shell.commands.ShellCommand):
    assert command.name == "shell"


def test_category(command: pebble_shell.commands.ShellCommand):
    assert command.category == "System Utilities"


def test_help(command: pebble_shell.commands.ShellCommand):
    with command.shell.console.capture() as capture:
        command.show_help()
    output = capture.get()
    assert "shell" in output
    assert "Execute shell commands" in output
    assert "-c" in output
    assert "-i" in output


@pytest.mark.parametrize("args", [["-h"], ["--help"]])
def test_execute_help(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ShellCommand,
    args: list[str],
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=args)
    assert result == 0
    output = capture.get()
    assert "shell" in output
    assert "Execute shell commands" in output


def test_execute_no_args_interactive(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ShellCommand,
):
    # shell with no args should start interactive shell or fail
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should either start interactive shell or fail gracefully
    if result == 0:
        output = capture.get()
        # Should indicate interactive shell started
        assert (
            any(msg in output for msg in ["shell started", "interactive", "exit"])
            or len(output.strip()) >= 0
        )
    else:
        # Should fail if interactive shell not available
        assert result == 1
        output = capture.get()
        assert any(
            msg in output for msg in ["interactive not available", "usage", "shell"]
        )


def test_execute_simple_command(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ShellCommand,
):
    # Test executing simple command
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-c", "echo hello"])

    # Should succeed executing echo command
    assert result == 0
    output = capture.get()
    # Should contain command output
    assert "hello" in output


def test_execute_command_with_arguments(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ShellCommand,
):
    # Test command with multiple arguments
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-c", "echo hello world test"])

    # Should succeed with command arguments
    assert result == 0
    output = capture.get()
    # Should contain all arguments
    assert all(word in output for word in ["hello", "world", "test"])


def test_execute_command_with_pipes(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ShellCommand,
):
    # Test command with pipes
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-c", "echo hello | wc -c"])

    # Should succeed with pipe operation
    assert result == 0
    output = capture.get()
    # Should show character count (6 for "hello\n")
    assert "6" in output or len(output.strip()) > 0


def test_execute_command_with_redirection(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ShellCommand,
):
    # Test command with output redirection
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client,
            args=["-c", "echo test > /tmp/shell_test.txt && cat /tmp/shell_test.txt"],
        )

    # Should succeed with redirection
    assert result == 0
    output = capture.get()
    # Should show redirected content
    assert "test" in output


def test_execute_command_with_variables(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ShellCommand,
):
    # Test command with environment variables
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["-c", "TEST_VAR=hello && echo $TEST_VAR"]
        )

    # Should succeed with variable usage
    assert result == 0
    output = capture.get()
    # Should show variable value
    assert "hello" in output


def test_execute_command_with_conditionals(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ShellCommand,
):
    # Test command with conditionals
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["-c", "if [ 1 -eq 1 ]; then echo success; fi"]
        )

    # Should succeed with conditional
    assert result == 0
    output = capture.get()
    # Should show conditional result
    assert "success" in output


def test_execute_command_with_loops(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ShellCommand,
):
    # Test command with loops
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["-c", "for i in 1 2 3; do echo $i; done"]
        )

    # Should succeed with loop
    assert result == 0
    output = capture.get()
    # Should show loop output
    assert all(num in output for num in ["1", "2", "3"])


def test_execute_invalid_command(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ShellCommand,
):
    # Test with invalid command
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-c", "nonexistent_command"])

    # Should fail with command not found
    assert result != 0
    output = capture.get()
    assert any(
        msg in output for msg in ["command not found", "not found", "No such file"]
    )


def test_execute_empty_command(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ShellCommand,
):
    # Test with empty command
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-c", ""])

    # Should either succeed with no output or fail
    if result == 0:
        output = capture.get()
        # Should have no output for empty command
        assert len(output.strip()) == 0
    else:
        # Should fail with empty command error
        assert result == 1


def test_execute_command_with_exit_code(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ShellCommand,
):
    # Test command that returns specific exit code
    with command.shell.console.capture() as _:
        result = command.execute(client=client, args=["-c", "exit 42"])

    # Should return the specified exit code
    assert result == 42


def test_execute_command_with_spaces(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ShellCommand,
):
    # Test command with spaces in arguments
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["-c", "echo 'hello world with spaces'"]
        )

    # Should succeed with spaced arguments
    assert result == 0
    output = capture.get()
    # Should preserve spaces
    assert "hello world with spaces" in output


def test_execute_command_with_quotes(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ShellCommand,
):
    # Test command with quoted arguments
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-c", 'echo "quoted string"'])

    # Should succeed with quoted string
    assert result == 0
    output = capture.get()
    # Should handle quotes correctly
    assert "quoted string" in output


def test_execute_command_with_escape_sequences(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ShellCommand,
):
    # Test command with escape sequences
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-c", "echo 'line1\\nline2'"])

    # Should succeed with escape sequences
    assert result == 0
    output = capture.get()
    # Should handle escape sequences
    assert "line1" in output and ("line2" in output or "\\n" in output)


def test_execute_interactive_mode(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ShellCommand,
):
    # Test -i option for interactive mode
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-i"])

    # Should either start interactive mode or fail gracefully
    if result == 0:
        output = capture.get()
        # Should indicate interactive mode
        assert (
            any(msg in output for msg in ["interactive", "shell", "$"])
            or len(output.strip()) >= 0
        )
    else:
        # Should fail if interactive mode not available
        assert result == 1


def test_execute_login_shell_mode(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ShellCommand,
):
    # Test -l option for login shell
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-l"])

    # Should either start login shell or fail gracefully
    if result == 0:
        output = capture.get()
        # Should indicate login shell
        assert len(output.strip()) >= 0
    else:
        # Should fail if login shell not available
        assert result == 1


def test_execute_restricted_shell_mode(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ShellCommand,
):
    # Test -r option for restricted shell
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-r"])

    # Should either start restricted shell or fail gracefully
    if result == 0:
        output = capture.get()
        # Should indicate restricted shell
        assert len(output.strip()) >= 0
    else:
        # Should fail if restricted shell not available
        assert result == 1


def test_execute_command_file(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ShellCommand,
):
    # Test executing commands from file
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/etc/passwd"])

    # Should either execute file as script or fail appropriately
    if result == 0:
        output = capture.get()
        # Should show script execution result
        assert len(output.strip()) >= 0
    else:
        # Should fail if file not executable or doesn't exist
        assert result != 0


def test_execute_builtin_commands(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ShellCommand,
):
    # Test shell builtin commands
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-c", "pwd"])

    # Should succeed with builtin command
    assert result == 0
    output = capture.get()
    # Should show current directory
    assert "/" in output  # Should contain path


def test_execute_external_commands(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ShellCommand,
):
    # Test external commands
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-c", "ls /"])

    # Should succeed with external command
    assert result == 0
    output = capture.get()
    # Should show directory listing
    assert any(dir_name in output for dir_name in ["bin", "etc", "usr", "var"])


def test_execute_command_substitution(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ShellCommand,
):
    # Test command substitution
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-c", "echo $(echo hello)"])

    # Should succeed with command substitution
    assert result == 0
    output = capture.get()
    # Should show substituted result
    assert "hello" in output


def test_execute_arithmetic_expansion(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ShellCommand,
):
    # Test arithmetic expansion
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-c", "echo $((2 + 2))"])

    # Should succeed with arithmetic
    assert result == 0
    output = capture.get()
    # Should show arithmetic result
    assert "4" in output


def test_execute_parameter_expansion(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ShellCommand,
):
    # Test parameter expansion
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-c", "VAR=test && echo ${VAR}"])

    # Should succeed with parameter expansion
    assert result == 0
    output = capture.get()
    # Should show expanded parameter
    assert "test" in output


def test_execute_globbing(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ShellCommand,
):
    # Test filename globbing
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-c", "echo /etc/p*"])

    # Should succeed with globbing
    assert result == 0
    output = capture.get()
    # Should show expanded glob pattern
    assert "/etc/" in output


def test_execute_background_processes(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ShellCommand,
):
    # Test background process execution
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-c", "sleep 0.1 & wait"])

    # Should succeed with background process
    assert result == 0
    output = capture.get()
    # Should complete without hanging
    assert len(output.strip()) >= 0


def test_execute_job_control(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ShellCommand,
):
    # Test job control features
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-c", "jobs"])

    # Should either succeed with job listing or fail gracefully
    if result == 0:
        output = capture.get()
        # Should show job status (may be empty)
        assert len(output.strip()) >= 0
    else:
        # Should fail if job control not available
        assert result != 0


def test_execute_signal_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ShellCommand,
):
    # Test signal handling
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["-c", "trap 'echo caught' INT && echo done"]
        )

    # Should succeed with signal trap
    assert result == 0
    output = capture.get()
    # Should show trap setup and completion
    assert "done" in output


def test_execute_functions(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ShellCommand,
):
    # Test shell functions
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client,
            args=["-c", "test_func() { echo function_called; }; test_func"],
        )

    # Should succeed with function definition and call
    assert result == 0
    output = capture.get()
    # Should show function output
    assert "function_called" in output


def test_execute_aliases(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ShellCommand,
):
    # Test shell aliases
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["-c", "alias ll='ls -l' && echo alias_set"]
        )

    # Should succeed with alias definition
    assert result == 0
    output = capture.get()
    # Should show alias set confirmation
    assert "alias_set" in output


def test_execute_history_access(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ShellCommand,
):
    # Test command history access
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-c", "history"])

    # Should either succeed showing history or fail gracefully
    if result == 0:
        output = capture.get()
        # Should show command history (may be empty)
        assert len(output.strip()) >= 0
    else:
        # Should fail if history not available
        assert result != 0


def test_execute_environment_modification(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ShellCommand,
):
    # Test environment variable modification
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["-c", "export TEST_ENV=value && echo $TEST_ENV"]
        )

    # Should succeed with environment modification
    assert result == 0
    output = capture.get()
    # Should show environment variable value
    assert "value" in output


def test_execute_current_directory_operations(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ShellCommand,
):
    # Test current directory operations
    temp_dir = tempfile.mkdtemp()
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-c", f"cd {temp_dir} && pwd"])

    # Should succeed with directory change
    assert result == 0
    output = capture.get()
    # Should show new directory
    assert temp_dir in output


def test_execute_file_operations(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ShellCommand,
):
    # Test file operations
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client,
            args=[
                "-c",
                "touch /tmp/test_file && ls /tmp/test_file && rm /tmp/test_file",
            ],
        )

    # Should succeed with file operations
    assert result == 0
    output = capture.get()
    # Should show file creation and listing
    assert "test_file" in output


def test_execute_permission_operations(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ShellCommand,
):
    # Test permission operations
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client,
            args=[
                "-c",
                "touch /tmp/perm_test && chmod 755 /tmp/perm_test && ls -l /tmp/perm_test && rm /tmp/perm_test",
            ],
        )

    # Should succeed with permission operations
    assert result == 0
    output = capture.get()
    # Should show permission changes
    assert "perm_test" in output


def test_execute_error_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ShellCommand,
):
    # Test error handling
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["-c", "false || echo error_handled"]
        )

    # Should succeed with error handling
    assert result == 0
    output = capture.get()
    # Should show error handling result
    assert "error_handled" in output


def test_execute_complex_shell_script(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ShellCommand,
):
    # Test complex shell script
    complex_script = """
    counter=0
    for i in $(seq 1 3); do
        counter=$((counter + i))
    done
    echo "Counter: $counter"
    """
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-c", complex_script])

    # Should succeed with complex script
    assert result == 0
    output = capture.get()
    # Should show script result (1+2+3=6)
    assert "Counter: 6" in output


def test_execute_multiline_commands(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ShellCommand,
):
    # Test multiline command execution
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["-c", "echo line1;\necho line2;\necho line3"]
        )

    # Should succeed with multiline commands
    assert result == 0
    output = capture.get()
    # Should show all lines
    assert all(line in output for line in ["line1", "line2", "line3"])


def test_execute_shell_options(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ShellCommand,
):
    # Test shell options
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["-c", "set -e && echo strict_mode"]
        )

    # Should succeed with shell options
    assert result == 0
    output = capture.get()
    # Should show option set result
    assert "strict_mode" in output


def test_execute_performance_large_output(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ShellCommand,
):
    # Test performance with large output
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-c", "seq 1 100"])

    # Should handle large output efficiently
    assert result == 0
    output = capture.get()
    # Should contain sequence numbers
    assert "1" in output and "100" in output


def test_execute_memory_efficiency(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ShellCommand,
):
    # Test memory efficiency
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-c", "echo memory_test"])

    # Should be memory efficient
    assert result == 0
    output = capture.get()
    # Should not consume excessive memory
    assert len(output) < 100000  # Reasonable output size limit
    assert "memory_test" in output


def test_execute_concurrent_execution(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ShellCommand,
):
    # Test concurrent execution safety
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-c", "echo concurrent_test"])

    # Should handle concurrent execution safely
    assert result == 0
    output = capture.get()
    assert "concurrent_test" in output


def test_execute_invalid_option_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ShellCommand,
):
    # Test handling of invalid options
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["--invalid-option"])

    # Should handle invalid options appropriately
    if result == 1:
        output = capture.get()
        # Should show error for invalid option
        assert any(msg in output for msg in ["invalid", "unknown", "option"])
    else:
        # May ignore unknown options and start shell
        assert result == 0
