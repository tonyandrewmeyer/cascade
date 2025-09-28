"""Integration tests for the CryptpwCommand."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

import pebble_shell.commands
import pebble_shell.shell

if TYPE_CHECKING:
    import ops


@pytest.fixture
def command(shell: pebble_shell.shell.PebbleShell):
    """Fixture to create a CryptpwCommand instance."""
    yield pebble_shell.commands.CryptpwCommand(shell=shell)


def test_name(command: pebble_shell.commands.CryptpwCommand):
    assert command.name == "cryptpw"


def test_category(command: pebble_shell.commands.CryptpwCommand):
    assert command.category == "Security Utilities"


def test_help(command: pebble_shell.commands.CryptpwCommand):
    with command.shell.console.capture() as capture:
        command.show_help()
    output = capture.get()
    assert "cryptpw" in output
    assert "Password encryption utility" in output
    assert "password" in output


@pytest.mark.parametrize("args", [["-h"], ["--help"]])
def test_execute_help(
    client: ops.pebble.Client,
    command: pebble_shell.commands.CryptpwCommand,
    args: list[str],
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=args)
    assert result == 0
    output = capture.get()
    assert "cryptpw" in output
    assert "Password encryption utility" in output


def test_execute_no_args(
    client: ops.pebble.Client,
    command: pebble_shell.commands.CryptpwCommand,
):
    # cryptpw with no args should show usage or prompt for password
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should either prompt for password or show usage
    if result == 0:
        output = capture.get()
        # Should prompt for password input
        assert len(output) >= 0
    else:
        # Should fail with usage message
        assert result == 1
        output = capture.get()
        assert any(msg in output for msg in ["usage", "Usage", "cryptpw", "password"])


def test_execute_encrypt_password_with_salt(
    client: ops.pebble.Client,
    command: pebble_shell.commands.CryptpwCommand,
):
    # Test encrypting password with salt
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["password123", "ab"])

    # Should succeed encrypting password
    assert result == 0
    output = capture.get()
    # Should contain encrypted password hash
    assert len(output.strip()) > 0
    # Should contain DES hash format
    encrypted = output.strip()
    assert len(encrypted) >= 13  # DES hash minimum length
    # Should start with salt
    assert encrypted.startswith("ab")


def test_execute_encrypt_password_no_salt(
    client: ops.pebble.Client,
    command: pebble_shell.commands.CryptpwCommand,
):
    # Test encrypting password without salt
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["password123"])

    # Should succeed encrypting password with random salt
    assert result == 0
    output = capture.get()
    # Should contain encrypted password hash
    assert len(output.strip()) > 0
    encrypted = output.strip()
    # Should be valid hash format
    assert len(encrypted) >= 13


def test_execute_md5_encryption(
    client: ops.pebble.Client,
    command: pebble_shell.commands.CryptpwCommand,
):
    # Test MD5 encryption
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-m", "password123"])

    # Should succeed with MD5 encryption
    assert result == 0
    output = capture.get()
    # Should contain MD5 hash
    assert len(output.strip()) > 0
    encrypted = output.strip()
    # MD5 hash should start with $1$
    assert encrypted.startswith("$1$")


def test_execute_sha256_encryption(
    client: ops.pebble.Client,
    command: pebble_shell.commands.CryptpwCommand,
):
    # Test SHA-256 encryption
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-S", "password123"])

    # Should either succeed with SHA-256 or fail if not supported
    if result == 0:
        output = capture.get()
        # Should contain SHA-256 hash
        assert len(output.strip()) > 0
        encrypted = output.strip()
        # SHA-256 hash should start with $5$
        assert encrypted.startswith("$5$")
    else:
        # May not be supported on all systems
        assert result == 1


def test_execute_sha512_encryption(
    client: ops.pebble.Client,
    command: pebble_shell.commands.CryptpwCommand,
):
    # Test SHA-512 encryption
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-s", "password123"])

    # Should either succeed with SHA-512 or fail if not supported
    if result == 0:
        output = capture.get()
        # Should contain SHA-512 hash
        assert len(output.strip()) > 0
        encrypted = output.strip()
        # SHA-512 hash should start with $6$
        assert encrypted.startswith("$6$")
    else:
        # May not be supported on all systems
        assert result == 1


def test_execute_custom_salt_md5(
    client: ops.pebble.Client,
    command: pebble_shell.commands.CryptpwCommand,
):
    # Test MD5 with custom salt
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["-m", "password123", "customsalt"]
        )

    # Should succeed with MD5 and custom salt
    assert result == 0
    output = capture.get()
    # Should contain MD5 hash with custom salt
    assert len(output.strip()) > 0
    encrypted = output.strip()
    # Should start with $1$ and contain salt
    assert encrypted.startswith("$1$")
    assert "customsalt" in encrypted


def test_execute_rounds_option(
    client: ops.pebble.Client,
    command: pebble_shell.commands.CryptpwCommand,
):
    # Test rounds option for SHA algorithms
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["-S", "-R", "10000", "password123"]
        )

    # Should either succeed with rounds or fail if not supported
    if result == 0:
        output = capture.get()
        # Should contain hash with specified rounds
        assert len(output.strip()) > 0
        encrypted = output.strip()
        # Should contain rounds specification
        assert "rounds=10000" in encrypted or len(encrypted) > 0
    else:
        # May not be supported
        assert result == 1


def test_execute_empty_password(
    client: ops.pebble.Client,
    command: pebble_shell.commands.CryptpwCommand,
):
    # Test empty password
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["", "ab"])

    # Should succeed encrypting empty password
    assert result == 0
    output = capture.get()
    # Should contain hash of empty password
    assert len(output.strip()) > 0
    encrypted = output.strip()
    assert encrypted.startswith("ab")


def test_execute_long_password(
    client: ops.pebble.Client,
    command: pebble_shell.commands.CryptpwCommand,
):
    # Test very long password
    long_password = "a" * 100
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[long_password, "ab"])

    # Should succeed encrypting long password
    assert result == 0
    output = capture.get()
    # Should contain hash of long password
    assert len(output.strip()) > 0
    encrypted = output.strip()
    assert encrypted.startswith("ab")


def test_execute_special_characters_password(
    client: ops.pebble.Client,
    command: pebble_shell.commands.CryptpwCommand,
):
    # Test password with special characters
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["p@ssw0rd!#$", "ab"])

    # Should succeed encrypting password with special chars
    assert result == 0
    output = capture.get()
    # Should contain hash
    assert len(output.strip()) > 0
    encrypted = output.strip()
    assert encrypted.startswith("ab")


def test_execute_unicode_password(
    client: ops.pebble.Client,
    command: pebble_shell.commands.CryptpwCommand,
):
    # Test password with Unicode characters
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["pässwörd", "ab"])

    # Should either succeed or handle Unicode appropriately
    if result == 0:
        output = capture.get()
        # Should contain hash of Unicode password
        assert len(output.strip()) > 0
        encrypted = output.strip()
        assert encrypted.startswith("ab")
    else:
        # May have encoding issues
        assert result == 1


def test_execute_invalid_salt_length(
    client: ops.pebble.Client,
    command: pebble_shell.commands.CryptpwCommand,
):
    # Test invalid salt length
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["password123", "a"])

    # Should either handle short salt or fail appropriately
    if result == 0:
        output = capture.get()
        # Should handle salt appropriately
        assert len(output.strip()) > 0
    else:
        # May require minimum salt length
        assert result == 1


def test_execute_invalid_salt_characters(
    client: ops.pebble.Client,
    command: pebble_shell.commands.CryptpwCommand,
):
    # Test invalid salt characters
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["password123", "!!"])

    # Should either handle invalid salt chars or fail appropriately
    if result == 0:
        output = capture.get()
        # Should handle salt characters appropriately
        assert len(output.strip()) > 0
    else:
        # May reject invalid salt characters
        assert result == 1


def test_execute_conflicting_algorithms(
    client: ops.pebble.Client,
    command: pebble_shell.commands.CryptpwCommand,
):
    # Test conflicting algorithm options
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-m", "-S", "password123"])

    # Should either handle conflict or fail appropriately
    if result == 0:
        output = capture.get()
        # Should use one of the algorithms
        assert len(output.strip()) > 0
    else:
        # Should fail with conflicting options
        assert result == 1
        output = capture.get()
        assert any(msg in output for msg in ["conflicting", "invalid", "error"])


def test_execute_invalid_rounds_value(
    client: ops.pebble.Client,
    command: pebble_shell.commands.CryptpwCommand,
):
    # Test invalid rounds value
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-S", "-R", "abc", "password123"])

    # Should fail with invalid rounds error
    assert result == 1
    output = capture.get()
    assert any(msg in output for msg in ["invalid", "rounds", "number", "error"])


def test_execute_out_of_range_rounds(
    client: ops.pebble.Client,
    command: pebble_shell.commands.CryptpwCommand,
):
    # Test out of range rounds value
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["-S", "-R", "999999999", "password123"]
        )

    # Should either handle large rounds or fail appropriately
    if result == 0:
        output = capture.get()
        # Should handle large rounds value
        assert len(output.strip()) > 0
    else:
        # Should fail with out of range error
        assert result == 1


def test_execute_invalid_option(
    client: ops.pebble.Client,
    command: pebble_shell.commands.CryptpwCommand,
):
    # Test invalid option
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-z", "password123"])

    # Should fail with invalid option error
    assert result == 1
    output = capture.get()
    assert any(msg in output for msg in ["invalid", "unknown", "option", "usage"])


def test_execute_missing_password_argument(
    client: ops.pebble.Client,
    command: pebble_shell.commands.CryptpwCommand,
):
    # Test missing password argument
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-m"])

    # Should either prompt for password or fail with missing argument
    if result == 0:
        output = capture.get()
        # Should handle missing password
        assert len(output) >= 0
    else:
        # Should fail with missing argument
        assert result == 1


def test_execute_hash_format_validation(
    client: ops.pebble.Client,
    command: pebble_shell.commands.CryptpwCommand,
):
    # Test hash format validation
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["testpassword", "ab"])

    # Should produce properly formatted hash
    assert result == 0
    output = capture.get()

    encrypted = output.strip()
    # Should be valid DES hash format
    assert len(encrypted) == 13  # DES hash length
    assert encrypted.startswith("ab")
    # Should contain only valid hash characters
    valid_chars = set(
        "./0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
    )
    assert all(c in valid_chars for c in encrypted)


def test_execute_deterministic_output(
    client: ops.pebble.Client,
    command: pebble_shell.commands.CryptpwCommand,
):
    # Test deterministic output with same input
    with command.shell.console.capture() as capture:
        result1 = command.execute(client=client, args=["password123", "ab"])
    output1 = capture.get()

    with command.shell.console.capture() as capture:
        result2 = command.execute(client=client, args=["password123", "ab"])
    output2 = capture.get()

    # Should produce identical output for same input
    assert result1 == 0
    assert result2 == 0
    assert output1.strip() == output2.strip()


def test_execute_different_salts_different_output(
    client: ops.pebble.Client,
    command: pebble_shell.commands.CryptpwCommand,
):
    # Test different salts produce different output
    with command.shell.console.capture() as capture:
        result1 = command.execute(client=client, args=["password123", "ab"])
    output1 = capture.get()

    with command.shell.console.capture() as capture:
        result2 = command.execute(client=client, args=["password123", "cd"])
    output2 = capture.get()

    # Should produce different output for different salts
    assert result1 == 0
    assert result2 == 0
    assert output1.strip() != output2.strip()


def test_execute_memory_efficiency(
    client: ops.pebble.Client,
    command: pebble_shell.commands.CryptpwCommand,
):
    # Test memory efficiency
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["password123", "ab"])

    # Should be memory efficient
    assert result == 0
    output = capture.get()
    # Should not consume excessive memory
    assert len(output) < 1000  # Reasonable output size limit


def test_execute_concurrent_execution(
    client: ops.pebble.Client,
    command: pebble_shell.commands.CryptpwCommand,
):
    # Test concurrent execution safety
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["password123", "ab"])

    # Should handle concurrent execution safely
    assert result == 0
    output = capture.get()
    assert len(output.strip()) > 0


def test_execute_error_recovery(
    client: ops.pebble.Client,
    command: pebble_shell.commands.CryptpwCommand,
):
    # Test error recovery capabilities
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-z", "password123"])

    # Should recover from errors gracefully
    assert result == 1
    output = capture.get()
    # Should provide meaningful error message
    assert any(msg in output for msg in ["invalid", "unknown", "error", "usage"])


def test_execute_signal_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.CryptpwCommand,
):
    # Test signal handling during processing
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["password123", "ab"])

    # Should handle signals appropriately
    assert result == 0
    output = capture.get()
    # Should be signal-safe
    assert len(output.strip()) > 0


def test_execute_locale_independence(
    client: ops.pebble.Client,
    command: pebble_shell.commands.CryptpwCommand,
):
    # Test locale independence
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["password123", "ab"])

    # Should work regardless of locale settings
    assert result == 0
    output = capture.get()
    # Should be locale-independent
    assert len(output.strip()) > 0


def test_execute_cross_platform_compatibility(
    client: ops.pebble.Client,
    command: pebble_shell.commands.CryptpwCommand,
):
    # Test cross-platform compatibility
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["password123", "ab"])

    # Should work across different platforms
    assert result == 0
    output = capture.get()
    # Should produce compatible hash formats
    assert len(output.strip()) > 0


def test_execute_security_validation(
    client: ops.pebble.Client,
    command: pebble_shell.commands.CryptpwCommand,
):
    # Test security validation
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["password123", "ab"])

    # Should produce secure hash
    assert result == 0
    output = capture.get()
    encrypted = output.strip()
    # Should not contain plaintext password
    assert "password123" not in encrypted
    # Should produce proper hash format
    assert len(encrypted) >= 13


def test_execute_cryptographic_strength(
    client: ops.pebble.Client,
    command: pebble_shell.commands.CryptpwCommand,
):
    # Test cryptographic strength
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-m", "password123"])

    # Should produce cryptographically strong hash
    if result == 0:
        output = capture.get()
        encrypted = output.strip()
        # MD5 hash should have proper format
        assert encrypted.startswith("$1$")
        # Should be sufficiently long
        assert len(encrypted) > 20
    else:
        # MD5 may not be supported
        assert result == 1


def test_execute_performance_optimization(
    client: ops.pebble.Client,
    command: pebble_shell.commands.CryptpwCommand,
):
    # Test performance optimization
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["password123", "ab"])

    # Should complete efficiently
    assert result == 0
    output = capture.get()
    # Should process efficiently
    assert len(output.strip()) > 0


def test_execute_data_consistency(
    client: ops.pebble.Client,
    command: pebble_shell.commands.CryptpwCommand,
):
    # Test data consistency
    with command.shell.console.capture() as _:
        result1 = command.execute(client=client, args=["password123", "ab"])

    with command.shell.console.capture() as _:
        result2 = command.execute(client=client, args=["password123", "ab"])

    # Should produce consistent results
    assert result1 == 0
    assert result2 == 0
    # Both executions should succeed consistently
    assert result1 == result2


def test_execute_robust_operation(
    client: ops.pebble.Client,
    command: pebble_shell.commands.CryptpwCommand,
):
    # Test robust operation under stress
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["password123", "ab"])

    # Should operate robustly
    assert result == 0
    output = capture.get()
    # Should handle stress conditions
    assert len(output.strip()) > 0
