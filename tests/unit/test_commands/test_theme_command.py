"""Tests for theme command."""

from unittest.mock import Mock

import pytest

from pebble_shell.commands.theme_command import ThemeCommand


class TestThemeCommand:
    """Test cases for ThemeCommand."""

    @pytest.fixture
    def command(self):
        """Create ThemeCommand instance."""
        mock_shell = Mock()
        mock_shell.console = Mock()
        return ThemeCommand(mock_shell)

    def test_execute_no_args_shows_current(self, command):
        """Test theme command with no arguments shows current theme."""
        result = command.execute(Mock(), [])

        assert result == 0
        command.shell.console.print.assert_called()
        # Should show current theme information

    def test_execute_list_shows_available_themes(self, command):
        """Test theme list command."""
        result = command.execute(Mock(), ["list"])

        assert result == 0
        command.shell.console.print.assert_called()
        # Should show available themes

    def test_execute_show_shows_current(self, command):
        """Test theme show command."""
        result = command.execute(Mock(), ["show"])

        assert result == 0
        command.shell.console.print.assert_called()

    def test_execute_set_valid_theme(self, command):
        """Test setting a valid theme."""
        for theme_name in ["default", "dark", "light", "minimal"]:
            command.shell.console.reset_mock()
            result = command.execute(Mock(), ["set", theme_name])

            assert result == 0
            command.shell.console.print.assert_called()

    def test_execute_set_invalid_theme(self, command):
        """Test setting an invalid theme."""
        result = command.execute(Mock(), ["set", "nonexistent"])

        assert result == 1
        command.shell.console.print.assert_called()

    def test_execute_set_no_theme_name(self, command):
        """Test set command without theme name."""
        result = command.execute(Mock(), ["set"])

        assert result == 1
        command.shell.console.print.assert_called()

    def test_execute_preview_valid_theme(self, command):
        """Test previewing a valid theme."""
        for theme_name in ["default", "dark", "light", "minimal"]:
            command.shell.console.reset_mock()
            result = command.execute(Mock(), ["preview", theme_name])

            assert result == 0
            command.shell.console.print.assert_called()

    def test_execute_preview_invalid_theme(self, command):
        """Test previewing an invalid theme."""
        result = command.execute(Mock(), ["preview", "nonexistent"])

        assert result == 1
        command.shell.console.print.assert_called()

    def test_execute_preview_no_theme_name(self, command):
        """Test preview command without theme name."""
        result = command.execute(Mock(), ["preview"])

        assert result == 1
        command.shell.console.print.assert_called()

    def test_execute_unknown_subcommand(self, command):
        """Test unknown subcommand."""
        result = command.execute(Mock(), ["unknown"])

        assert result == 1
        command.shell.console.print.assert_called()

    def test_help_flag(self, command):
        """Test help flag handling."""
        result = command.execute(Mock(), ["-h"])

        assert result == 0
        command.shell.console.print.assert_called()

    def test_case_insensitive_subcommands(self, command):
        """Test that subcommands are case insensitive."""
        result = command.execute(Mock(), ["LIST"])
        assert result == 0

        result = command.execute(Mock(), ["Show"])
        assert result == 0

        result = command.execute(Mock(), ["SET", "dark"])
        assert result == 0

        result = command.execute(Mock(), ["PREVIEW", "light"])
        assert result == 0

    def test_case_insensitive_theme_names(self, command):
        """Test that theme names are case insensitive."""
        result = command.execute(Mock(), ["set", "DARK"])
        assert result == 0

        result = command.execute(Mock(), ["preview", "LIGHT"])
        assert result == 0
