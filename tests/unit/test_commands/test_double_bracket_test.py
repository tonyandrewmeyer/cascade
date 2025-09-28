"""Unit tests for [[ (double bracket test) command."""

from unittest.mock import MagicMock

import ops.pebble

from pebble_shell.commands.advanced_utils import DoubleBracketTestCommand
from pebble_shell.shell import PebbleShell


class TestDoubleBracketTestCommand:
    """Test the [[ (double bracket test) command."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_client = MagicMock()
        self.mock_shell = MagicMock(spec=PebbleShell)
        self.command = DoubleBracketTestCommand(self.mock_shell)

    def test_missing_closing_bracket(self):
        """Test error when closing brackets are missing."""
        result = self.command.execute(self.mock_client, ["-f", "/etc/passwd"])
        assert result == 2

    def test_empty_expression(self):
        """Test empty expression returns false."""
        result = self.command.execute(self.mock_client, ["]]"])
        assert result == 1

    def test_pattern_matching_with_wildcards(self):
        """Test pattern matching with wildcards."""
        result = self.command.execute(
            self.mock_client, ["hello.txt", "==", "*.txt", "]]"]
        )
        assert result == 0

        result = self.command.execute(
            self.mock_client, ["hello.doc", "==", "*.txt", "]]"]
        )
        assert result == 1

    def test_pattern_non_matching(self):
        """Test pattern non-matching."""
        result = self.command.execute(
            self.mock_client, ["hello.doc", "!=", "*.txt", "]]"]
        )
        assert result == 0

        result = self.command.execute(
            self.mock_client, ["hello.txt", "!=", "*.txt", "]]"]
        )
        assert result == 1

    def test_regex_matching(self):
        """Test regular expression matching."""
        result = self.command.execute(
            self.mock_client, ["123", "=~", r"^[0-9]+$", "]]"]
        )
        assert result == 0

        result = self.command.execute(
            self.mock_client, ["abc", "=~", r"^[0-9]+$", "]]"]
        )
        assert result == 1

    def test_invalid_regex(self):
        """Test invalid regex pattern handling."""
        result = self.command.execute(self.mock_client, ["test", "=~", "[", "]]"])
        assert result == 1  # Should return false for invalid regex

    def test_short_circuit_and(self):
        """Test short-circuit AND operator."""
        # Both true
        result = self.command.execute(self.mock_client, ["hello", "&&", "world", "]]"])
        assert result == 0

        # First false (should short-circuit)
        result = self.command.execute(self.mock_client, ["", "&&", "world", "]]"])
        assert result == 1

    def test_short_circuit_or(self):
        """Test short-circuit OR operator."""
        # First true (should short-circuit)
        result = self.command.execute(self.mock_client, ["hello", "||", "", "]]"])
        assert result == 0

        # Both false
        result = self.command.execute(self.mock_client, ["", "||", "", "]]"])
        assert result == 1

    def test_complex_logical_expression(self):
        """Test complex logical expressions."""
        # Test: [[ "hello" == "hello" && -n "world" ]]
        result = self.command.execute(
            self.mock_client, ["hello", "==", "hello", "&&", "-n", "world", "]]"]
        )
        assert result == 0

    def test_negation_with_pattern(self):
        """Test negation with pattern matching."""
        result = self.command.execute(
            self.mock_client, ["!", "hello.txt", "==", "*.doc", "]]"]
        )
        assert result == 0  # NOT (hello.txt matches *.doc) = true

    def test_file_operations_same_as_bracket(self):
        """Test that file operations work the same as single bracket."""
        # Mock file exists
        self.mock_client.pull.return_value.__enter__.return_value = MagicMock()
        result = self.command.execute(self.mock_client, ["-f", "/etc/passwd", "]]"])
        assert result == 0

        # Mock file doesn't exist
        self.mock_client.pull.side_effect = ops.pebble.PathError("path", "not found")
        result = self.command.execute(self.mock_client, ["-f", "/nonexistent", "]]"])
        assert result == 1

    def test_numeric_operations_same_as_bracket(self):
        """Test that numeric operations work the same as single bracket."""
        result = self.command.execute(self.mock_client, ["5", "-lt", "10", "]]"])
        assert result == 0

        result = self.command.execute(self.mock_client, ["10", "-eq", "10", "]]"])
        assert result == 0

    def test_string_length_operations_same_as_bracket(self):
        """Test that string length operations work the same as single bracket."""
        result = self.command.execute(self.mock_client, ["-z", "", "]]"])
        assert result == 0  # Empty string

        result = self.command.execute(self.mock_client, ["-n", "hello", "]]"])
        assert result == 0  # Non-empty string

    def test_backward_compatibility_with_old_operators(self):
        """Test backward compatibility with -a and -o operators."""
        result = self.command.execute(self.mock_client, ["hello", "-a", "world", "]]"])
        assert result == 0

        result = self.command.execute(self.mock_client, ["", "-o", "world", "]]"])
        assert result == 0

    def test_help_flag(self):
        """Test help flag."""
        result = self.command.execute(self.mock_client, ["--help"])
        assert result == 0

    def test_wildcard_question_mark(self):
        """Test single character wildcard."""
        result = self.command.execute(self.mock_client, ["cat", "==", "c?t", "]]"])
        assert result == 0

        result = self.command.execute(self.mock_client, ["cart", "==", "c?t", "]]"])
        assert result == 1

    def test_complex_pattern_matching(self):
        """Test complex pattern matching scenarios."""
        # Test multiple wildcards
        result = self.command.execute(
            self.mock_client, ["test.log.backup", "==", "*.log.*", "]]"]
        )
        assert result == 0

        # Test character classes (basic fnmatch support)
        result = self.command.execute(
            self.mock_client, ["file1", "==", "file[0-9]", "]]"]
        )
        assert result == 0

    def test_regex_with_special_characters(self):
        """Test regex matching with special characters."""
        result = self.command.execute(
            self.mock_client, ["user@domain.com", "=~", r".*@.*\.com$", "]]"]
        )
        assert result == 0

        result = self.command.execute(
            self.mock_client, ["invalid-email", "=~", r".*@.*\.com$", "]]"]
        )
        assert result == 1

    def test_single_argument_evaluation(self):
        """Test single argument evaluation (truthiness)."""
        result = self.command.execute(self.mock_client, ["non-empty", "]]"])
        assert result == 0

        result = self.command.execute(self.mock_client, ["", "]]"])
        assert result == 1

    def test_parentheses_not_supported(self):
        """Test that parentheses are treated as literal strings."""
        # This should be treated as comparing literal strings
        result = self.command.execute(self.mock_client, ["(", "==", "(", "]]"])
        assert result == 0

    def test_combined_and_or_operators(self):
        """Test combining && and || operators."""
        # Test: [[ "a" == "a" || "b" == "c" && "d" == "d" ]]
        # Should evaluate as: (a==a) || ((b==c) && (d==d)) = true || (false && true) = true
        result = self.command.execute(
            self.mock_client,
            ["a", "==", "a", "||", "b", "==", "c", "&&", "d", "==", "d", "]]"],
        )
        # Due to left-to-right evaluation, this will be: ((a==a) || (b==c)) && (d==d) = true && true = true
        assert result == 0
