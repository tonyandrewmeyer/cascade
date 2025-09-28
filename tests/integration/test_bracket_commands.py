"""Integration tests for [ and [[ commands."""

from unittest.mock import MagicMock

from pebble_shell.commands.advanced_utils import (
    BracketTestCommand,
    DoubleBracketTestCommand,
)
from pebble_shell.shell import PebbleShell


class TestBracketCommandsIntegration:
    """Integration tests for bracket test commands."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_client = MagicMock()
        self.mock_shell = MagicMock(spec=PebbleShell)
        self.bracket_command = BracketTestCommand(self.mock_shell)
        self.double_bracket_command = DoubleBracketTestCommand(self.mock_shell)

    def test_bracket_command_basic_functionality(self):
        """Test basic functionality of [ command."""
        # String comparison
        result = self.bracket_command.execute(
            self.mock_client, ["hello", "=", "hello", "]"]
        )
        assert result == 0

        # Numeric comparison
        result = self.bracket_command.execute(self.mock_client, ["5", "-eq", "5", "]"])
        assert result == 0

        # String length test
        result = self.bracket_command.execute(self.mock_client, ["-z", "", "]"])
        assert result == 0

    def test_double_bracket_command_extended_functionality(self):
        """Test extended functionality of [[ command."""
        # Pattern matching
        result = self.double_bracket_command.execute(
            self.mock_client, ["test.txt", "==", "*.txt", "]]"]
        )
        assert result == 0

        # Regex matching
        result = self.double_bracket_command.execute(
            self.mock_client, ["123", "=~", r"^[0-9]+$", "]]"]
        )
        assert result == 0

        # Short-circuit AND
        result = self.double_bracket_command.execute(
            self.mock_client, ["hello", "&&", "world", "]]"]
        )
        assert result == 0

    def test_bracket_vs_double_bracket_compatibility(self):
        """Test that [[ is backward compatible with [ for basic operations."""
        test_cases = [
            (["hello", "=", "hello", "]"], ["hello", "=", "hello", "]]"]),
            (["5", "-eq", "5", "]"], ["5", "-eq", "5", "]]"]),
            (["-z", "", "]"], ["-z", "", "]]"]),
            (["-n", "hello", "]"], ["-n", "hello", "]]"]),
        ]

        for bracket_args, double_bracket_args in test_cases:
            bracket_result = self.bracket_command.execute(
                self.mock_client, bracket_args
            )
            double_bracket_result = self.double_bracket_command.execute(
                self.mock_client, double_bracket_args
            )
            assert bracket_result == double_bracket_result, (
                f"Results differ for {bracket_args}"
            )

    def test_error_handling_consistency(self):
        """Test that both commands handle errors consistently."""
        # Missing closing bracket
        bracket_result = self.bracket_command.execute(self.mock_client, ["hello"])
        double_bracket_result = self.double_bracket_command.execute(
            self.mock_client, ["hello"]
        )
        assert bracket_result == 2
        assert double_bracket_result == 2

    def test_help_functionality(self):
        """Test help functionality for both commands."""
        bracket_result = self.bracket_command.execute(self.mock_client, ["--help"])
        double_bracket_result = self.double_bracket_command.execute(
            self.mock_client, ["--help"]
        )
        assert bracket_result == 0
        assert double_bracket_result == 0

    def test_command_names(self):
        """Test that command names are set correctly."""
        assert self.bracket_command.name == "["
        assert self.double_bracket_command.name == "[["

    def test_complex_integration_scenarios(self):
        """Test complex real-world scenarios."""
        # Test file existence check (simulated)
        import ops.pebble

        self.mock_client.pull.side_effect = ops.pebble.PathError("path", "not found")

        # Both commands should handle file tests the same way
        bracket_result = self.bracket_command.execute(
            self.mock_client, ["-f", "/nonexistent", "]"]
        )
        double_bracket_result = self.double_bracket_command.execute(
            self.mock_client, ["-f", "/nonexistent", "]]"]
        )
        assert bracket_result == 1
        assert double_bracket_result == 1

    def test_logical_operators_integration(self):
        """Test logical operators in both commands."""
        # Test AND operation
        bracket_result = self.bracket_command.execute(
            self.mock_client, ["hello", "-a", "world", "]"]
        )
        double_bracket_result = self.double_bracket_command.execute(
            self.mock_client, ["hello", "-a", "world", "]]"]
        )
        assert bracket_result == 0
        assert double_bracket_result == 0

        # Test OR operation
        bracket_result = self.bracket_command.execute(
            self.mock_client, ["", "-o", "world", "]"]
        )
        double_bracket_result = self.double_bracket_command.execute(
            self.mock_client, ["", "-o", "world", "]]"]
        )
        assert bracket_result == 0
        assert double_bracket_result == 0

    def test_negation_integration(self):
        """Test negation operator in both commands."""
        bracket_result = self.bracket_command.execute(self.mock_client, ["!", "", "]"])
        double_bracket_result = self.double_bracket_command.execute(
            self.mock_client, ["!", "", "]]"]
        )
        assert bracket_result == 0
        assert double_bracket_result == 0

    def test_numeric_comparison_edge_cases(self):
        """Test numeric comparison edge cases."""
        # Large numbers
        bracket_result = self.bracket_command.execute(
            self.mock_client, ["1000000", "-gt", "999999", "]"]
        )
        double_bracket_result = self.double_bracket_command.execute(
            self.mock_client, ["1000000", "-gt", "999999", "]]"]
        )
        assert bracket_result == 0
        assert double_bracket_result == 0

        # Negative numbers
        bracket_result = self.bracket_command.execute(
            self.mock_client, ["-5", "-lt", "0", "]"]
        )
        double_bracket_result = self.double_bracket_command.execute(
            self.mock_client, ["-5", "-lt", "0", "]]"]
        )
        assert bracket_result == 0
        assert double_bracket_result == 0

    def test_string_comparison_edge_cases(self):
        """Test string comparison edge cases."""
        # Empty strings
        bracket_result = self.bracket_command.execute(
            self.mock_client, ["", "=", "", "]"]
        )
        double_bracket_result = self.double_bracket_command.execute(
            self.mock_client, ["", "=", "", "]]"]
        )
        assert bracket_result == 0
        assert double_bracket_result == 0

        # Strings with spaces
        bracket_result = self.bracket_command.execute(
            self.mock_client, ["hello world", "=", "hello world", "]"]
        )
        double_bracket_result = self.double_bracket_command.execute(
            self.mock_client, ["hello world", "=", "hello world", "]]"]
        )
        assert bracket_result == 0
        assert double_bracket_result == 0
