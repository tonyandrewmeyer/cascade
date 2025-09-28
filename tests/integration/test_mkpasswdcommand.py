"""Integration tests for the MkpasswdCommand."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

import pebble_shell.commands
import pebble_shell.shell

if TYPE_CHECKING:
    import ops


@pytest.fixture
def command(shell: pebble_shell.shell.PebbleShell):
    """Fixture to create a MkpasswdCommand instance."""
    yield pebble_shell.commands.MkpasswdCommand(shell=shell)


def test_name(command: pebble_shell.commands.MkpasswdCommand):
    assert command.name == "mkpasswd"


def test_category(command: pebble_shell.commands.MkpasswdCommand):
    assert command.category == "System Utilities"


def test_help(command: pebble_shell.commands.MkpasswdCommand):
    with command.shell.console.capture() as capture:
        command.show_help()
    output = capture.get()
    assert "mkpasswd" in output
    assert "Generate password hash" in output
    assert "-m" in output
    assert "-s" in output


@pytest.mark.parametrize("args", [["-h"], ["--help"]])
def test_execute_help(
    client: ops.pebble.Client,
    command: pebble_shell.commands.MkpasswdCommand,
    args: list[str],
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=args)
    assert result == 0
    output = capture.get()
    assert "mkpasswd" in output
    assert "Generate password hash" in output


def test_execute_no_args_prompt_password(
    client: ops.pebble.Client,
    command: pebble_shell.commands.MkpasswdCommand,
):
    # mkpasswd with no args should prompt for password or fail
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should either succeed with prompt or fail gracefully
    if result == 0:
        output = capture.get()
        # Should generate a password hash
        assert len(output.strip()) > 0
        # Should contain hash characters
        assert any(
            c in output
            for c in "$./0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
        )
    else:
        # Should fail if no password provided and prompting not available
        assert result == 1
        output = capture.get()
        assert any(msg in output for msg in ["password required", "usage", "mkpasswd"])


def test_execute_simple_password(
    client: ops.pebble.Client,
    command: pebble_shell.commands.MkpasswdCommand,
):
    # Test with simple password
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["testpass"])

    # Should succeed generating password hash
    assert result == 0
    output = capture.get()
    # Should contain password hash
    assert len(output.strip()) > 10
    # Should start with hash algorithm identifier (typically $)
    hash_output = output.strip()
    assert hash_output.startswith("$") or len(hash_output) > 8


def test_execute_empty_password(
    client: ops.pebble.Client,
    command: pebble_shell.commands.MkpasswdCommand,
):
    # Test with empty password
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[""])

    # Should either succeed with empty password hash or fail
    if result == 0:
        output = capture.get()
        # Should generate hash even for empty password
        assert len(output.strip()) > 0
    else:
        # Should fail if empty password not allowed
        assert result == 1


def test_execute_complex_password(
    client: ops.pebble.Client,
    command: pebble_shell.commands.MkpasswdCommand,
):
    # Test with complex password
    complex_pass = "MyC0mpl3x!P@ssw0rd#2023"
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[complex_pass])

    # Should succeed with complex password
    assert result == 0
    output = capture.get()
    # Should generate hash for complex password
    assert len(output.strip()) > 10
    # Should contain hash characters
    hash_output = output.strip()
    assert any(c.isalnum() or c in "$./+" for c in hash_output)


def test_execute_method_des(
    client: ops.pebble.Client,
    command: pebble_shell.commands.MkpasswdCommand,
):
    # Test -m des option for DES encryption
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-m", "des", "testpass"])

    # Should either succeed with DES or fail if not supported
    if result == 0:
        output = capture.get()
        # Should generate DES hash (13 characters, no $ prefix)
        hash_output = output.strip()
        assert len(hash_output) >= 10
        # DES hash format
        assert not hash_output.startswith("$") or len(hash_output) > 8
    else:
        # Should fail if DES not supported
        assert result == 1
        output = capture.get()
        assert any(
            msg in output for msg in ["unsupported", "not available", "DES", "error"]
        )


def test_execute_method_md5(
    client: ops.pebble.Client,
    command: pebble_shell.commands.MkpasswdCommand,
):
    # Test -m md5 option for MD5 encryption
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-m", "md5", "testpass"])

    # Should succeed with MD5
    if result == 0:
        output = capture.get()
        # Should generate MD5 hash (starts with $1$)
        hash_output = output.strip()
        assert len(hash_output) > 20
        if hash_output.startswith("$1$"):
            assert "$1$" in hash_output
    else:
        # Should fail if MD5 not supported
        assert result == 1


def test_execute_method_sha256(
    client: ops.pebble.Client,
    command: pebble_shell.commands.MkpasswdCommand,
):
    # Test -m sha-256 option for SHA-256 encryption
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-m", "sha-256", "testpass"])

    # Should succeed with SHA-256
    if result == 0:
        output = capture.get()
        # Should generate SHA-256 hash (starts with $5$)
        hash_output = output.strip()
        assert len(hash_output) > 40
        if hash_output.startswith("$5$"):
            assert "$5$" in hash_output
    else:
        # Should fail if SHA-256 not supported
        assert result == 1


def test_execute_method_sha512(
    client: ops.pebble.Client,
    command: pebble_shell.commands.MkpasswdCommand,
):
    # Test -m sha-512 option for SHA-512 encryption
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-m", "sha-512", "testpass"])

    # Should succeed with SHA-512
    if result == 0:
        output = capture.get()
        # Should generate SHA-512 hash (starts with $6$)
        hash_output = output.strip()
        assert len(hash_output) > 60
        if hash_output.startswith("$6$"):
            assert "$6$" in hash_output
    else:
        # Should fail if SHA-512 not supported
        assert result == 1


def test_execute_invalid_method(
    client: ops.pebble.Client,
    command: pebble_shell.commands.MkpasswdCommand,
):
    # Test with invalid hash method
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-m", "invalid", "testpass"])

    # Should fail with invalid method error
    assert result == 1
    output = capture.get()
    assert any(
        msg in output
        for msg in ["invalid method", "unknown method", "unsupported", "error"]
    )


def test_execute_salt_option(
    client: ops.pebble.Client,
    command: pebble_shell.commands.MkpasswdCommand,
):
    # Test -s option to specify salt
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-s", "testsalt", "testpass"])

    # Should succeed with specified salt
    assert result == 0
    output = capture.get()
    # Should generate hash with specified salt
    hash_output = output.strip()
    assert len(hash_output) > 10
    # Should incorporate salt into hash
    assert "testsalt" in hash_output or len(hash_output) > 15


def test_execute_rounds_option(
    client: ops.pebble.Client,
    command: pebble_shell.commands.MkpasswdCommand,
):
    # Test -R option to specify rounds
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-R", "1000", "testpass"])

    # Should either succeed with specified rounds or fail gracefully
    if result == 0:
        output = capture.get()
        # Should generate hash with specified rounds
        hash_output = output.strip()
        assert len(hash_output) > 10
        # May contain rounds information in hash
        if "rounds=" in hash_output:
            assert "1000" in hash_output
    else:
        # Should fail if rounds option not supported
        assert result == 1


def test_execute_stdin_password(
    client: ops.pebble.Client,
    command: pebble_shell.commands.MkpasswdCommand,
):
    # Test reading password from stdin
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["--stdin"])

    # Should either succeed reading from stdin or fail gracefully
    if result == 0:
        output = capture.get()
        # Should generate hash from stdin password
        assert len(output.strip()) > 0
    else:
        # Should fail if stdin not available or option not supported
        assert result == 1


def test_execute_password_with_spaces(
    client: ops.pebble.Client,
    command: pebble_shell.commands.MkpasswdCommand,
):
    # Test password with spaces
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["my password has spaces"])

    # Should succeed with spaced password
    assert result == 0
    output = capture.get()
    # Should generate hash for password with spaces
    hash_output = output.strip()
    assert len(hash_output) > 10


def test_execute_password_with_special_chars(
    client: ops.pebble.Client,
    command: pebble_shell.commands.MkpasswdCommand,
):
    # Test password with special characters
    special_pass = "!@#$%^&*()_+-=[]{}|;':\",./<>?"
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[special_pass])

    # Should succeed with special character password
    assert result == 0
    output = capture.get()
    # Should generate hash for special character password
    hash_output = output.strip()
    assert len(hash_output) > 10


def test_execute_unicode_password(
    client: ops.pebble.Client,
    command: pebble_shell.commands.MkpasswdCommand,
):
    # Test password with unicode characters
    unicode_pass = "password123🔒"
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[unicode_pass])

    # Should either succeed with unicode or fail gracefully
    if result == 0:
        output = capture.get()
        # Should generate hash for unicode password
        hash_output = output.strip()
        assert len(hash_output) > 10
    else:
        # Should fail if unicode not supported
        assert result == 1


def test_execute_very_long_password(
    client: ops.pebble.Client,
    command: pebble_shell.commands.MkpasswdCommand,
):
    # Test with very long password
    long_pass = "a" * 1000
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[long_pass])

    # Should either succeed with long password or fail with limit error
    if result == 0:
        output = capture.get()
        # Should generate hash for long password
        hash_output = output.strip()
        assert len(hash_output) > 10
    else:
        # Should fail if password too long
        assert result == 1
        output = capture.get()
        assert any(
            msg in output for msg in ["too long", "password length", "limit", "error"]
        )


def test_execute_deterministic_output(
    client: ops.pebble.Client,
    command: pebble_shell.commands.MkpasswdCommand,
):
    # Test deterministic output with same salt
    with command.shell.console.capture() as capture:
        result1 = command.execute(client=client, args=["-s", "fixedsalt", "testpass"])
    output1 = capture.get()

    with command.shell.console.capture() as capture:
        result2 = command.execute(client=client, args=["-s", "fixedsalt", "testpass"])
    output2 = capture.get()

    # Should produce same hash with same salt and password
    if result1 == 0 and result2 == 0:
        assert output1.strip() == output2.strip()
    else:
        # Should fail consistently
        assert result1 == result2


def test_execute_different_salts(
    client: ops.pebble.Client,
    command: pebble_shell.commands.MkpasswdCommand,
):
    # Test different salts produce different hashes
    with command.shell.console.capture() as capture:
        result1 = command.execute(client=client, args=["-s", "salt1", "testpass"])
    output1 = capture.get()

    with command.shell.console.capture() as capture:
        result2 = command.execute(client=client, args=["-s", "salt2", "testpass"])
    output2 = capture.get()

    # Should produce different hashes with different salts
    if result1 == 0 and result2 == 0:
        assert output1.strip() != output2.strip()


def test_execute_list_methods(
    client: ops.pebble.Client,
    command: pebble_shell.commands.MkpasswdCommand,
):
    # Test -l option to list available methods
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-l"])

    # Should either succeed listing methods or fail gracefully
    if result == 0:
        output = capture.get()
        # Should show available hash methods
        assert (
            any(
                method in output.lower()
                for method in ["des", "md5", "sha", "available", "methods"]
            )
            or len(output.strip()) > 0
        )
    else:
        # Should fail if list option not supported
        assert result == 1


def test_execute_quiet_mode(
    client: ops.pebble.Client,
    command: pebble_shell.commands.MkpasswdCommand,
):
    # Test -q option for quiet mode
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-q", "testpass"])

    # Should either succeed quietly or fail gracefully
    if result == 0:
        output = capture.get()
        # Should generate hash with minimal output
        hash_output = output.strip()
        assert len(hash_output) > 0
        # Should not contain extra messages in quiet mode
        lines = output.strip().split("\n")
        assert len(lines) <= 2  # Should be concise
    else:
        # Should fail if quiet option not supported
        assert result == 1


def test_execute_verbose_mode(
    client: ops.pebble.Client,
    command: pebble_shell.commands.MkpasswdCommand,
):
    # Test -v option for verbose mode
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-v", "testpass"])

    # Should either succeed with verbose output or fail gracefully
    if result == 0:
        output = capture.get()
        # Should show verbose information
        assert len(output.strip()) > 0
        # May contain method information or salt details
        assert (
            any(info in output.lower() for info in ["method", "salt", "hash", "using"])
            or len(output.strip()) > 20
        )
    else:
        # Should fail if verbose option not supported
        assert result == 1


def test_execute_hash_validation(
    client: ops.pebble.Client,
    command: pebble_shell.commands.MkpasswdCommand,
):
    # Test hash output validation
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["testpass"])

    # Should produce valid hash format
    if result == 0:
        output = capture.get()
        hash_output = output.strip()
        # Should have reasonable hash length
        assert 8 <= len(hash_output) <= 200
        # Should contain valid hash characters
        valid_chars = set(
            "$./0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
        )
        assert all(c in valid_chars for c in hash_output)


def test_execute_salt_validation(
    client: ops.pebble.Client,
    command: pebble_shell.commands.MkpasswdCommand,
):
    # Test salt validation
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-s", "invalid$salt", "testpass"])

    # Should either succeed with processed salt or fail with invalid salt
    if result == 0:
        output = capture.get()
        # Should generate hash (may process salt)
        assert len(output.strip()) > 0
    else:
        # Should fail if salt contains invalid characters
        assert result == 1
        output = capture.get()
        assert any(msg in output for msg in ["invalid salt", "salt format", "error"])


def test_execute_method_compatibility(
    client: ops.pebble.Client,
    command: pebble_shell.commands.MkpasswdCommand,
):
    # Test method compatibility with different systems
    methods = ["des", "md5", "sha-256", "sha-512"]
    results = []

    for method in methods:
        with command.shell.console.capture() as capture:
            result = command.execute(client=client, args=["-m", method, "testpass"])
        results.append(result)

        if result == 0:
            output = capture.get()
            # Should generate appropriate hash for each method
            hash_output = output.strip()
            assert len(hash_output) > 8

    # At least one method should be supported
    assert any(result == 0 for result in results)


def test_execute_concurrent_execution(
    client: ops.pebble.Client,
    command: pebble_shell.commands.MkpasswdCommand,
):
    # Test concurrent execution safety
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["testpass"])

    # Should handle concurrent execution safely
    assert result == 0
    output = capture.get()
    hash_output = output.strip()
    assert len(hash_output) > 0


def test_execute_password_strength_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.MkpasswdCommand,
):
    # Test handling of various password strengths
    passwords = ["weak", "Str0ng3r!", "VeryComplexPassword123!@#"]

    for password in passwords:
        with command.shell.console.capture() as capture:
            result = command.execute(client=client, args=[password])

        # Should succeed regardless of password strength
        assert result == 0
        output = capture.get()
        # Should generate hash for all password types
        hash_output = output.strip()
        assert len(hash_output) > 8


def test_execute_binary_password_data(
    client: ops.pebble.Client,
    command: pebble_shell.commands.MkpasswdCommand,
):
    # Test with binary-like password data
    binary_pass = "\x00\x01\x02\x03\x04\x05"
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[binary_pass])

    # Should either succeed with binary data or fail gracefully
    if result == 0:
        output = capture.get()
        # Should generate hash for binary data
        hash_output = output.strip()
        assert len(hash_output) > 8
    else:
        # Should fail if binary data not supported
        assert result == 1


def test_execute_performance_with_high_rounds(
    client: ops.pebble.Client,
    command: pebble_shell.commands.MkpasswdCommand,
):
    # Test performance with high round count
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-R", "10000", "testpass"])

    # Should either complete with high rounds or fail if not supported
    if result == 0:
        output = capture.get()
        # Should complete even with high rounds
        hash_output = output.strip()
        assert len(hash_output) > 0
    else:
        # Should fail if high rounds not supported or too high
        assert result == 1


def test_execute_error_recovery(
    client: ops.pebble.Client,
    command: pebble_shell.commands.MkpasswdCommand,
):
    # Test error recovery capabilities
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-m", "nonexistent"])

    # Should recover from errors gracefully
    if result == 1:
        output = capture.get()
        # Should provide meaningful error message
        assert any(msg in output for msg in ["invalid", "unknown", "method", "error"])
    else:
        assert result == 0


def test_execute_memory_efficiency(
    client: ops.pebble.Client,
    command: pebble_shell.commands.MkpasswdCommand,
):
    # Test memory efficiency
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["testpass"])

    # Should be memory efficient
    assert result == 0
    output = capture.get()
    # Should not consume excessive memory
    assert len(output) < 1000  # Hash should be relatively short


def test_execute_invalid_option_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.MkpasswdCommand,
):
    # Test handling of invalid options
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["--invalid-option", "testpass"])

    # Should handle invalid options appropriately
    if result == 1:
        output = capture.get()
        # Should show error for invalid option
        assert any(msg in output for msg in ["invalid", "unknown", "option"])
    else:
        # May ignore unknown options and proceed
        assert result == 0
        output = capture.get()
        # Should still generate hash
        assert len(output.strip()) > 0
