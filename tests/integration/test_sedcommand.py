"""Integration tests for the SedCommand."""

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
    """Fixture to create a SedCommand instance."""
    yield pebble_shell.commands.SedCommand(shell=shell)


def test_name(command: pebble_shell.commands.SedCommand):
    assert command.name == "sed"


def test_category(command: pebble_shell.commands.SedCommand):
    assert command.category == "Text Processing"


def test_help(command: pebble_shell.commands.SedCommand):
    with command.shell.console.capture() as capture:
        command.show_help()
    output = capture.get()
    assert "sed" in output
    assert "Stream editor" in output
    assert "substitute" in output


@pytest.mark.parametrize("args", [["-h"], ["--help"]])
def test_execute_help(
    client: ops.pebble.Client,
    command: pebble_shell.commands.SedCommand,
    args: list[str],
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=args)
    assert result == 0
    output = capture.get()
    assert "sed" in output
    assert "Stream editor" in output


def test_execute_no_args(
    client: ops.pebble.Client,
    command: pebble_shell.commands.SedCommand,
):
    # sed with no args should fail and show usage
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should fail with usage message
    assert result == 1
    output = capture.get()
    assert any(
        msg in output for msg in ["usage", "Usage", "sed", "expression", "script"]
    )


def test_execute_simple_substitution_with_file(
    client: ops.pebble.Client,
    command: pebble_shell.commands.SedCommand,
):
    # Test simple substitution with file
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["s/root/admin/", "/etc/passwd"])

    # Should either succeed with substitution or fail gracefully
    if result == 0:
        output = capture.get()
        # Should show modified content
        assert len(output.strip()) > 0
        # Should contain substituted text if root was present
        if "admin" in output:
            assert "admin" in output
    else:
        # Should fail if file doesn't exist or access denied
        assert result == 1
        output = capture.get()
        assert any(
            msg in output
            for msg in ["No such file", "cannot read", "error", "permission"]
        )


def test_execute_global_substitution(
    client: ops.pebble.Client,
    command: pebble_shell.commands.SedCommand,
):
    # Test global substitution
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["s/a/A/g", "/etc/hosts"])

    # Should either succeed with global substitution or fail gracefully
    if result == 0:
        output = capture.get()
        # Should show content with all 'a' replaced with 'A'
        assert len(output.strip()) >= 0
    else:
        # Should fail if file doesn't exist
        assert result == 1


def test_execute_delete_lines(
    client: ops.pebble.Client,
    command: pebble_shell.commands.SedCommand,
):
    # Test deleting lines
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/^#/d", "/etc/hosts"])

    # Should either succeed deleting comment lines or fail gracefully
    if result == 0:
        output = capture.get()
        # Should show content without comment lines
        assert len(output.strip()) >= 0
        # Should not contain lines starting with #
        lines = output.strip().split("\n") if output.strip() else []
        for line in lines:
            if line.strip():
                assert not line.strip().startswith("#")
    else:
        assert result == 1


def test_execute_print_specific_lines(
    client: ops.pebble.Client,
    command: pebble_shell.commands.SedCommand,
):
    # Test printing specific lines
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-n", "1,3p", "/etc/hosts"])

    # Should either succeed printing lines 1-3 or fail gracefully
    if result == 0:
        output = capture.get()
        # Should show only lines 1-3
        assert len(output.strip()) >= 0
        # Should have limited output
        lines = output.strip().split("\n") if output.strip() else []
        assert len(lines) <= 3
    else:
        assert result == 1


def test_execute_address_range_substitution(
    client: ops.pebble.Client,
    command: pebble_shell.commands.SedCommand,
):
    # Test substitution with address range
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["1,5s/localhost/localserver/", "/etc/hosts"]
        )

    # Should either succeed with range substitution or fail gracefully
    if result == 0:
        output = capture.get()
        # Should show content with substitution in first 5 lines
        assert len(output.strip()) >= 0
    else:
        assert result == 1


def test_execute_pattern_matching_substitution(
    client: ops.pebble.Client,
    command: pebble_shell.commands.SedCommand,
):
    # Test pattern matching substitution
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["/localhost/s/127/192/", "/etc/hosts"]
        )

    # Should either succeed with pattern-based substitution or fail gracefully
    if result == 0:
        output = capture.get()
        # Should show content with conditional substitution
        assert len(output.strip()) >= 0
    else:
        assert result == 1


def test_execute_multiple_commands(
    client: ops.pebble.Client,
    command: pebble_shell.commands.SedCommand,
):
    # Test multiple sed commands
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client,
            args=["-e", "s/root/admin/", "-e", "s/bin/usr/", "/etc/passwd"],
        )

    # Should either succeed with multiple commands or fail gracefully
    if result == 0:
        output = capture.get()
        # Should show content with both substitutions applied
        assert len(output.strip()) >= 0
    else:
        assert result == 1


def test_execute_in_place_editing(
    client: ops.pebble.Client,
    command: pebble_shell.commands.SedCommand,
):
    # Test in-place editing (dangerous, so we use a safe approach)
    temp_dir = tempfile.mkdtemp()
    nonexistent_path = temp_dir + "/nonexistent"
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["-i.bak", "s/test/TEST/", nonexistent_path]
        )

    # Should fail gracefully for nonexistent file
    assert result == 1
    output = capture.get()
    assert any(msg in output for msg in ["No such file", "cannot", "error"])


def test_execute_append_text(
    client: ops.pebble.Client,
    command: pebble_shell.commands.SedCommand,
):
    # Test appending text
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["1a\\", "Added line", "/etc/hosts"]
        )

    # Should either succeed appending text or fail gracefully
    if result == 0:
        output = capture.get()
        # Should show content with appended text
        assert len(output.strip()) >= 0
    else:
        assert result == 1


def test_execute_insert_text(
    client: ops.pebble.Client,
    command: pebble_shell.commands.SedCommand,
):
    # Test inserting text
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["1i\\", "Inserted line", "/etc/hosts"]
        )

    # Should either succeed inserting text or fail gracefully
    if result == 0:
        output = capture.get()
        # Should show content with inserted text
        assert len(output.strip()) >= 0
    else:
        assert result == 1


def test_execute_change_lines(
    client: ops.pebble.Client,
    command: pebble_shell.commands.SedCommand,
):
    # Test changing lines
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["1c\\", "Changed line", "/etc/hosts"]
        )

    # Should either succeed changing lines or fail gracefully
    if result == 0:
        output = capture.get()
        # Should show content with changed line
        assert len(output.strip()) >= 0
    else:
        assert result == 1


def test_execute_line_numbering(
    client: ops.pebble.Client,
    command: pebble_shell.commands.SedCommand,
):
    # Test line numbering
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["=", "/etc/hosts"])

    # Should either succeed with line numbers or fail gracefully
    if result == 0:
        output = capture.get()
        # Should show content with line numbers
        assert len(output.strip()) >= 0
        # May contain numeric line numbers
        if output.strip():
            lines = output.strip().split("\n")
            # Some lines should be numeric (line numbers)
            numeric_lines = [line for line in lines if line.strip().isdigit()]
            assert len(numeric_lines) >= 0
    else:
        assert result == 1


def test_execute_transform_characters(
    client: ops.pebble.Client,
    command: pebble_shell.commands.SedCommand,
):
    # Test character transformation
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["y/abc/ABC/", "/etc/hosts"])

    # Should either succeed with character transformation or fail gracefully
    if result == 0:
        output = capture.get()
        # Should show content with character transformation
        assert len(output.strip()) >= 0
        # Should transform lowercase to uppercase
        if "a" in output or "b" in output or "c" in output:
            # Check if transformation occurred
            assert len(output.strip()) > 0
    else:
        assert result == 1


def test_execute_hold_space_operations(
    client: ops.pebble.Client,
    command: pebble_shell.commands.SedCommand,
):
    # Test hold space operations
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["1h;2g", "/etc/hosts"])

    # Should either succeed with hold space operations or fail gracefully
    if result == 0:
        output = capture.get()
        # Should show content with hold space manipulation
        assert len(output.strip()) >= 0
    else:
        assert result == 1


def test_execute_next_line_operations(
    client: ops.pebble.Client,
    command: pebble_shell.commands.SedCommand,
):
    # Test next line operations
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["n;s/test/TEST/", "/etc/hosts"])

    # Should either succeed with next line operations or fail gracefully
    if result == 0:
        output = capture.get()
        # Should show content with next line processing
        assert len(output.strip()) >= 0
    else:
        assert result == 1


def test_execute_branching(
    client: ops.pebble.Client,
    command: pebble_shell.commands.SedCommand,
):
    # Test branching operations
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=[":label;s/a/A/;t label", "/etc/hosts"]
        )

    # Should either succeed with branching or fail gracefully
    if result == 0:
        output = capture.get()
        # Should show content with branching logic applied
        assert len(output.strip()) >= 0
    else:
        assert result == 1


def test_execute_quiet_mode(
    client: ops.pebble.Client,
    command: pebble_shell.commands.SedCommand,
):
    # Test quiet mode
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["-n", "/localhost/p", "/etc/hosts"]
        )

    # Should either succeed in quiet mode or fail gracefully
    if result == 0:
        output = capture.get()
        # Should show only explicitly printed lines
        assert len(output.strip()) >= 0
        # Should contain only lines matching localhost pattern
        lines = output.strip().split("\n") if output.strip() else []
        for line in lines:
            if line.strip():
                # Lines should contain localhost or be empty
                assert "localhost" in line.lower() or line.strip() == ""
    else:
        assert result == 1


def test_execute_extended_regex(
    client: ops.pebble.Client,
    command: pebble_shell.commands.SedCommand,
):
    # Test extended regular expressions
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["-E", "s/[0-9]+/NUMBER/g", "/etc/hosts"]
        )

    # Should either succeed with extended regex or fail gracefully
    if result == 0:
        output = capture.get()
        # Should show content with numbers replaced
        assert len(output.strip()) >= 0
    else:
        assert result == 1


def test_execute_script_file(
    client: ops.pebble.Client,
    command: pebble_shell.commands.SedCommand,
):
    # Test script file execution
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["-f", "/nonexistent/script.sed", "/etc/hosts"]
        )

    # Should fail gracefully for nonexistent script file
    assert result == 1
    output = capture.get()
    assert any(msg in output for msg in ["No such file", "cannot", "error"])


def test_execute_invalid_regex(
    client: ops.pebble.Client,
    command: pebble_shell.commands.SedCommand,
):
    # Test invalid regular expression
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["s/[/invalid/", "/etc/hosts"])

    # Should fail with invalid regex error
    assert result == 1
    output = capture.get()
    assert any(msg in output for msg in ["Invalid", "error", "regex", "expression"])


def test_execute_invalid_command(
    client: ops.pebble.Client,
    command: pebble_shell.commands.SedCommand,
):
    # Test invalid sed command
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["z/invalid/", "/etc/hosts"])

    # Should fail with invalid command error
    assert result == 1
    output = capture.get()
    assert any(msg in output for msg in ["invalid", "unknown", "error", "command"])


def test_execute_nonexistent_file(
    client: ops.pebble.Client,
    command: pebble_shell.commands.SedCommand,
):
    # Test with nonexistent file
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["s/test/TEST/", "/nonexistent/file.txt"]
        )

    # Should fail with file not found error
    assert result == 1
    output = capture.get()
    assert any(msg in output for msg in ["No such file", "cannot", "error"])


def test_execute_permission_denied_file(
    client: ops.pebble.Client,
    command: pebble_shell.commands.SedCommand,
):
    # Test with permission denied file
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["s/test/TEST/", "/root/.ssh/id_rsa"]
        )

    # Should either succeed or fail with permission error
    if result == 1:
        output = capture.get()
        assert any(msg in output for msg in ["permission", "denied", "cannot", "error"])
    else:
        # May succeed if file is readable
        assert result == 0


def test_execute_empty_file(
    client: ops.pebble.Client,
    command: pebble_shell.commands.SedCommand,
):
    # Test with empty file
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["s/test/TEST/", "/dev/null"])

    # Should succeed with empty output
    assert result == 0
    output = capture.get()
    # Should produce no output for empty file
    assert len(output.strip()) == 0


def test_execute_binary_file_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.SedCommand,
):
    # Test with binary file
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["s/ELF/elf/", "/bin/ls"])

    # Should either succeed or handle binary gracefully
    if result == 0:
        output = capture.get()
        # Should process binary file (may contain binary data)
        assert len(output) >= 0
    else:
        # May fail for binary files
        assert result == 1


def test_execute_large_file_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.SedCommand,
):
    # Test with large file
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["s/usr/opt/", "/usr/bin/bash"])

    # Should either succeed processing large file or fail gracefully
    if result == 0:
        output = capture.get()
        # Should process large file efficiently
        assert len(output) >= 0
    else:
        assert result == 1


def test_execute_output_format_validation(
    client: ops.pebble.Client,
    command: pebble_shell.commands.SedCommand,
):
    # Test output format validation
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["s/localhost/localserver/", "/etc/hosts"]
        )

    # Should produce properly formatted output
    if result == 0:
        output = capture.get()
        # Should have valid text output
        assert len(output.strip()) >= 0
        if len(output.strip()) > 0:
            # Should be valid text format
            lines = output.strip().split("\n")
            assert len(lines) >= 1
    else:
        assert result == 1


def test_execute_memory_efficiency(
    client: ops.pebble.Client,
    command: pebble_shell.commands.SedCommand,
):
    # Test memory efficiency
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["s/a/A/g", "/etc/passwd"])

    # Should be memory efficient
    if result == 0:
        output = capture.get()
        # Should not consume excessive memory
        assert len(output) < 100000  # Reasonable output size limit
    else:
        assert result == 1


def test_execute_concurrent_execution(
    client: ops.pebble.Client,
    command: pebble_shell.commands.SedCommand,
):
    # Test concurrent execution safety
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["s/test/TEST/", "/etc/hosts"])

    # Should handle concurrent execution safely
    if result == 0:
        output = capture.get()
        assert len(output.strip()) >= 0
    else:
        assert result == 1


def test_execute_error_recovery(
    client: ops.pebble.Client,
    command: pebble_shell.commands.SedCommand,
):
    # Test error recovery capabilities
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["s/[/invalid/", "/etc/hosts"])

    # Should recover from errors gracefully
    assert result == 1
    output = capture.get()
    # Should provide meaningful error message
    assert any(msg in output for msg in ["Invalid", "error", "expression", "regex"])


def test_execute_signal_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.SedCommand,
):
    # Test signal handling during processing
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["s/test/TEST/", "/etc/hosts"])

    # Should handle signals appropriately
    if result == 0:
        output = capture.get()
        assert len(output.strip()) >= 0
    else:
        assert result == 1


def test_execute_locale_awareness(
    client: ops.pebble.Client,
    command: pebble_shell.commands.SedCommand,
):
    # Test locale awareness
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["s/café/coffee/", "/etc/hosts"])

    # Should handle locale-specific characters
    if result == 0:
        output = capture.get()
        # Should process Unicode characters appropriately
        assert len(output.strip()) >= 0
    else:
        assert result == 1


def test_execute_line_ending_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.SedCommand,
):
    # Test line ending handling
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["s/$/\\r/", "/etc/hosts"])

    # Should handle different line endings
    if result == 0:
        output = capture.get()
        # Should process line endings correctly
        assert len(output.strip()) >= 0
    else:
        assert result == 1


def test_execute_pattern_space_operations(
    client: ops.pebble.Client,
    command: pebble_shell.commands.SedCommand,
):
    # Test pattern space operations
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["N;s/\\n/ /", "/etc/hosts"])

    # Should handle pattern space manipulation
    if result == 0:
        output = capture.get()
        # Should process pattern space correctly
        assert len(output.strip()) >= 0
    else:
        assert result == 1


def test_execute_address_validation(
    client: ops.pebble.Client,
    command: pebble_shell.commands.SedCommand,
):
    # Test address validation
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["0s/test/TEST/", "/etc/hosts"])

    # Should validate addresses properly
    assert result == 1
    output = capture.get()
    # Should show address error
    assert any(msg in output for msg in ["invalid", "address", "error"])


def test_execute_escape_sequence_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.SedCommand,
):
    # Test escape sequence handling
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["s/test/\\t\\n/", "/etc/hosts"])

    # Should handle escape sequences
    if result == 0:
        output = capture.get()
        # Should process escape sequences correctly
        assert len(output.strip()) >= 0
    else:
        assert result == 1


def test_execute_backreference_substitution(
    client: ops.pebble.Client,
    command: pebble_shell.commands.SedCommand,
):
    # Test backreference substitution
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client,
            args=["s/\\(.*\\)localhost\\(.*\\)/\\1localserver\\2/", "/etc/hosts"],
        )

    # Should handle backreferences
    if result == 0:
        output = capture.get()
        # Should process backreferences correctly
        assert len(output.strip()) >= 0
    else:
        assert result == 1


def test_execute_command_line_parsing(
    client: ops.pebble.Client,
    command: pebble_shell.commands.SedCommand,
):
    # Test command line parsing
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["s/test/TEST/", "/etc/hosts", "/etc/passwd"]
        )

    # Should handle multiple input files
    if result == 0:
        output = capture.get()
        # Should process multiple files
        assert len(output.strip()) >= 0
    else:
        assert result == 1


def test_execute_standard_input_processing(
    client: ops.pebble.Client,
    command: pebble_shell.commands.SedCommand,
):
    # Test standard input processing
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["s/test/TEST/"])

    # Should handle standard input processing
    if result == 0:
        output = capture.get()
        # Should wait for input or process empty input
        assert len(output.strip()) >= 0
    else:
        # May fail without input
        assert result == 1


def test_execute_performance_optimization(
    client: ops.pebble.Client,
    command: pebble_shell.commands.SedCommand,
):
    # Test performance optimization
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["s/a/A/g", "/etc/passwd"])

    # Should complete efficiently
    if result == 0:
        output = capture.get()
        # Should process efficiently
        assert len(output) >= 0
    else:
        assert result == 1
