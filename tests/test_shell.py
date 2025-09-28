"""Tests for the main shell implementation."""

from unittest.mock import Mock, patch

import pytest
from ops.pebble import ConnectionError

from pebble_shell.shell import PebbleShell


class TestPebbleShell:
    """Test cases for PebbleShell class."""

    @pytest.fixture
    def mock_client(self):
        """Create a mock Pebble client."""
        client = Mock()
        client.get_system_info.return_value = {"version": "1.0.0"}
        return client

    @pytest.fixture
    def shell(self, mock_client):
        """Create a shell instance for testing."""
        return PebbleShell(mock_client)

    def test_init(self, shell):
        """Test shell initialization."""
        assert shell.client is not None
        assert len(shell.commands) == 34  # All commands including history and alias

    def test_init_with_custom_socket(self, mock_client):
        """Test shell initialization with custom socket path."""
        shell = PebbleShell(mock_client)
        assert shell.client is mock_client

    @patch("pebble_shell.shell.Client")
    def test_connect_success(self, mock_client_class, shell):
        """Test successful connection to Pebble."""
        mock_client = Mock()
        mock_client.get_system_info.return_value = {"version": "1.0.0"}
        mock_client_class.return_value = mock_client

        result = shell.connect()

        assert result is True
        assert shell.client is mock_client
        mock_client_class.assert_called_once_with(socket_path=shell.socket_path)
        mock_client.get_system_info.assert_called_once()

    @patch("pebble_shell.shell.Client")
    def test_connect_failure(self, mock_client_class, shell, capsys):
        """Test failed connection to Pebble."""
        mock_client_class.side_effect = ConnectionError("Connection failed")

        result = shell.connect()

        assert result is False
        assert shell.client is None
        captured = capsys.readouterr()
        assert "Failed to connect to Pebble" in captured.out

    def test_run_command_empty(self, shell):
        """Test running empty command."""
        result = shell.run_command("")
        assert result is True

        result = shell.run_command("   ")
        assert result is True

    def test_run_command_exit(self, shell):
        """Test exit command."""
        result = shell.run_command("exit")
        assert result is False

    def test_run_command_help(self, shell, capsys):
        """Test help command."""
        result = shell.run_command("help")
        assert result is True

        captured = capsys.readouterr()
        assert "Available commands:" in captured.out
        assert "ls [path]" in captured.out

    def test_run_command_no_client(self, shell, capsys):
        """Test running command without client connection."""
        result = shell.run_command("ls /")
        assert result is True

        captured = capsys.readouterr()
        assert "Not connected to Pebble" in captured.out

    def test_run_command_unknown(self, shell, capsys):
        """Test running unknown command."""
        result = shell.run_command("unknown_command")
        assert result is True

        captured = capsys.readouterr()
        assert "Unknown command: unknown_command" in captured.out

    def test_run_command_with_client(self, shell, mock_client):
        """Test running command with connected client."""
        shell.client = mock_client
        mock_command = Mock()
        shell.commands["ls"] = mock_command

        result = shell.run_command("ls /var")

        assert result is True
        mock_command.execute.assert_called_once_with(mock_client, ["/var"])

    @patch("pebble_shell.shell.PipelineExecutor")
    @patch("pebble_shell.shell.get_shell_parser")
    def test_run_command_with_pipeline(
        self, mock_get_parser, mock_executor_class, shell, mock_client
    ):
        """Test running command with pipeline executor."""
        shell.client = mock_client

        mock_parser = Mock()
        mock_parser.parse_command_line.return_value = [Mock()]
        mock_get_parser.return_value = mock_parser

        mock_executor = Mock()
        mock_executor.execute_pipeline.return_value = True
        mock_executor_class.return_value = mock_executor

        result = shell.run_command("ls | grep test")

        assert result is True
        mock_parser.parse_command_line.assert_called_once()
        mock_executor.execute_pipeline.assert_called_once()

    @patch("pebble_shell.shell.get_shell_parser")
    def test_run_command_variable_assignment(self, mock_get_parser, shell, capsys):
        """Test variable assignment."""
        mock_parser = Mock()
        mock_get_parser.return_value = mock_parser

        result = shell.run_command("VAR=value")

        assert result is True
        mock_parser.set_variable.assert_called_once_with("VAR", "value")
        captured = capsys.readouterr()
        assert "VAR=value" in captured.out

    @patch("pebble_shell.shell.get_shell_parser")
    def test_run_command_parse_error(self, mock_get_parser, shell, capsys):
        """Test handling parse errors."""
        mock_parser = Mock()
        mock_parser.parse_command_line.side_effect = Exception("Parse error")
        mock_get_parser.return_value = mock_parser

        result = shell.run_command("invalid command")

        assert result is True
        captured = capsys.readouterr()
        assert "Error parsing command" in captured.out

    @patch("builtins.input")
    @patch("pebble_shell.shell.PebbleShell.connect")
    def test_run_interactive_exit(self, mock_connect, mock_input, shell):
        """Test interactive shell with exit command."""
        mock_connect.return_value = True
        mock_input.return_value = "exit"

        shell.run()

        mock_connect.assert_called_once()
        mock_input.assert_called_once()

    @patch("builtins.input")
    @patch("pebble_shell.shell.PebbleShell.connect")
    def test_run_interactive_keyboard_interrupt(
        self, mock_connect, mock_input, shell, capsys
    ):
        """Test interactive shell with keyboard interrupt."""
        mock_connect.return_value = True
        mock_input.side_effect = [KeyboardInterrupt(), "exit"]

        shell.run()

        captured = capsys.readouterr()
        assert "Use 'exit' to quit." in captured.out

    @patch("builtins.input")
    @patch("pebble_shell.shell.PebbleShell.connect")
    def test_run_interactive_eof(self, mock_connect, mock_input, shell, capsys):
        """Test interactive shell with EOF."""
        mock_connect.return_value = True
        mock_input.side_effect = EOFError()

        shell.run()

        captured = capsys.readouterr()
        assert "Goodbye!" in captured.out

    @patch("sys.exit")
    @patch("pebble_shell.shell.PebbleShell.connect")
    def test_run_connection_failure(self, mock_connect, mock_exit, shell):
        """Test shell run with connection failure."""
        mock_connect.return_value = False

        shell.run()

        mock_exit.assert_called_once_with(1)
