"""Unit tests for [ (bracket test) command."""

import tempfile
from unittest.mock import MagicMock, patch

import ops.pebble

from pebble_shell.commands.advanced_utils import BracketTestCommand
from pebble_shell.shell import PebbleShell


class TestBracketTestCommand:
    """Test the [ (bracket test) command."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_client = MagicMock()
        self.mock_shell = MagicMock(spec=PebbleShell)
        self.command = BracketTestCommand(self.mock_shell)

    def test_missing_closing_bracket(self):
        """Test error when closing bracket is missing."""
        result = self.command.execute(self.mock_client, ["-f", "/etc/passwd"])
        assert result == 2

    def test_empty_expression(self):
        """Test empty expression returns false."""
        result = self.command.execute(self.mock_client, ["]"])
        assert result == 1

    def test_string_test_non_empty(self):
        """Test non-empty string returns true."""
        result = self.command.execute(self.mock_client, ["hello", "]"])
        assert result == 0

    def test_string_test_empty(self):
        """Test empty string returns false."""
        result = self.command.execute(self.mock_client, ["", "]"])
        assert result == 1

    def test_string_equality(self):
        """Test string equality operator."""
        result = self.command.execute(self.mock_client, ["hello", "=", "hello", "]"])
        assert result == 0

        result = self.command.execute(self.mock_client, ["hello", "=", "world", "]"])
        assert result == 1

    def test_string_inequality(self):
        """Test string inequality operator."""
        result = self.command.execute(self.mock_client, ["hello", "!=", "world", "]"])
        assert result == 0

        result = self.command.execute(self.mock_client, ["hello", "!=", "hello", "]"])
        assert result == 1

    def test_numeric_equality(self):
        """Test numeric equality operators."""
        result = self.command.execute(self.mock_client, ["5", "-eq", "5", "]"])
        assert result == 0

        result = self.command.execute(self.mock_client, ["5", "-eq", "10", "]"])
        assert result == 1

    def test_numeric_comparison(self):
        """Test numeric comparison operators."""
        result = self.command.execute(self.mock_client, ["5", "-lt", "10", "]"])
        assert result == 0

        result = self.command.execute(self.mock_client, ["10", "-lt", "5", "]"])
        assert result == 1

        result = self.command.execute(self.mock_client, ["10", "-gt", "5", "]"])
        assert result == 0

    def test_string_length_tests(self):
        """Test string length operators."""
        result = self.command.execute(self.mock_client, ["-z", "", "]"])
        assert result == 0  # Empty string

        result = self.command.execute(self.mock_client, ["-z", "hello", "]"])
        assert result == 1  # Non-empty string

        result = self.command.execute(self.mock_client, ["-n", "hello", "]"])
        assert result == 0  # Non-empty string

        result = self.command.execute(self.mock_client, ["-n", "", "]"])
        assert result == 1  # Empty string

    def test_file_exists_operator(self):
        """Test file existence operator."""
        # Mock file exists
        self.mock_client.pull.return_value.__enter__.return_value = MagicMock()
        result = self.command.execute(self.mock_client, ["-e", "/etc/passwd", "]"])
        assert result == 0

        # Mock file doesn't exist
        self.mock_client.pull.side_effect = ops.pebble.PathError("path", "not found")
        result = self.command.execute(self.mock_client, ["-e", "/nonexistent", "]"])
        assert result == 1

    def test_file_type_operators(self):
        """Test file type operators."""
        # Mock regular file
        self.mock_client.pull.return_value.__enter__.return_value = MagicMock()
        result = self.command.execute(self.mock_client, ["-f", "/etc/passwd", "]"])
        assert result == 0

        # Mock directory
        self.mock_client.pull.side_effect = ops.pebble.PathError("path", "not found")
        self.mock_client.list_files.return_value = []
        temp_dir = tempfile.mkdtemp()
        result = self.command.execute(self.mock_client, ["-d", temp_dir, "]"])
        assert result == 0

    def test_logical_and_operator(self):
        """Test logical AND operator."""
        # Both true
        result = self.command.execute(self.mock_client, ["hello", "-a", "world", "]"])
        assert result == 0

        # First false
        result = self.command.execute(self.mock_client, ["", "-a", "world", "]"])
        assert result == 1

        # Second false
        result = self.command.execute(self.mock_client, ["hello", "-a", "", "]"])
        assert result == 1

    def test_logical_or_operator(self):
        """Test logical OR operator."""
        # Both true
        result = self.command.execute(self.mock_client, ["hello", "-o", "world", "]"])
        assert result == 0

        # First true, second false
        result = self.command.execute(self.mock_client, ["hello", "-o", "", "]"])
        assert result == 0

        # First false, second true
        result = self.command.execute(self.mock_client, ["", "-o", "world", "]"])
        assert result == 0

        # Both false
        result = self.command.execute(self.mock_client, ["", "-o", "", "]"])
        assert result == 1

    def test_negation_operator(self):
        """Test logical NOT operator."""
        result = self.command.execute(self.mock_client, ["!", "", "]"])
        assert result == 0  # NOT false = true

        result = self.command.execute(self.mock_client, ["!", "hello", "]"])
        assert result == 1  # NOT true = false

    def test_help_flag(self):
        """Test help flag."""
        result = self.command.execute(self.mock_client, ["--help"])
        assert result == 0

    def test_executable_file_test(self):
        """Test executable file test (approximate)."""
        # Test executable path
        result = self.command.execute(self.mock_client, ["-x", "/bin/bash", "]"])
        assert result == 0

        # Test non-executable path
        result = self.command.execute(self.mock_client, ["-x", "/etc/passwd", "]"])
        assert result == 1

    def test_non_empty_file_test(self):
        """Test non-empty file test."""
        with patch("pebble_shell.commands.advanced_utils.safe_read_file") as mock_read:
            # Mock non-empty file
            mock_read.return_value = "content"
            result = self.command.execute(self.mock_client, ["-s", "/etc/passwd", "]"])
            assert result == 0

            # Mock empty file
            mock_read.return_value = ""
            result = self.command.execute(self.mock_client, ["-s", "/empty", "]"])
            assert result == 1

    def test_complex_expression(self):
        """Test complex logical expression."""
        # Test: [ "hello" = "hello" -a -n "world" ]
        result = self.command.execute(
            self.mock_client, ["hello", "=", "hello", "-a", "-n", "world", "]"]
        )
        assert result == 0

    def test_invalid_numeric_comparison(self):
        """Test invalid numeric values in comparison."""
        # Should handle gracefully when values aren't numeric
        result = self.command.execute(self.mock_client, ["hello", "-eq", "world", "]"])
        assert result == 1  # Should be false since they're not numbers
