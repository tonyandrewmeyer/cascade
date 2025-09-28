"""Tests for pebble CLI commands."""

from unittest.mock import Mock, patch

import ops.pebble
import pytest

from pebble_shell.commands.pebble_cli import (
    PlanCommand,
    RestartCommand,
    ServicesCommand,
    SignalCommand,
    StartCommand,
    StopCommand,
)


class TestPlanCommand:
    """Test cases for PlanCommand."""

    @pytest.fixture
    def command(self):
        """Create a PlanCommand instance."""
        mock_shell = Mock()
        return PlanCommand(mock_shell)

    @pytest.fixture
    def mock_client(self):
        """Create a mock Pebble client."""
        return Mock(spec=ops.pebble.Client)

    def test_init(self, command):
        """Test command initialization."""
        assert command.name == "pebble-plan"
        assert "plan configuration" in command.help
        assert command.category == "Pebble Management"

    def test_execute_help(self, command, mock_client):
        """Test help flag execution."""
        with patch(
            "pebble_shell.utils.command_helpers.handle_help_flag", return_value=True
        ):
            result = command.execute(mock_client, ["--help"])
            assert result == 0

    def test_execute_default_table_format(self, command, mock_client):
        """Test execution with default table format."""
        mock_plan = {
            "services": {
                "test-service": {
                    "override": "replace",
                    "command": "test-command",
                    "startup": "enabled",
                    "environment": {"TEST": "value"},
                }
            }
        }
        mock_client.get_plan.return_value = Mock(to_dict=Mock(return_value=mock_plan))

        result = command.execute(mock_client, [])

        assert result == 0
        mock_client.get_plan.assert_called_once()

    def test_execute_json_format(self, command, mock_client):
        """Test execution with JSON format."""
        mock_plan = {"services": {}}
        mock_client.get_plan.return_value = Mock(to_dict=Mock(return_value=mock_plan))

        result = command.execute(mock_client, ["--format=json"])

        assert result == 0
        mock_client.get_plan.assert_called_once()

    def test_execute_yaml_format(self, command, mock_client):
        """Test execution with YAML format."""
        mock_plan = {"services": {}}
        mock_client.get_plan.return_value = Mock(to_dict=Mock(return_value=mock_plan))

        result = command.execute(mock_client, ["--format=yaml"])

        assert result == 0
        mock_client.get_plan.assert_called_once()

    def test_execute_invalid_format(self, command, mock_client):
        """Test execution with invalid format."""
        result = command.execute(mock_client, ["--format=invalid"])

        assert result == 1

    def test_execute_format_without_value(self, command, mock_client):
        """Test execution with format flag but no value."""
        result = command.execute(mock_client, ["--format"])

        assert result == 1

    def test_execute_exception(self, command, mock_client):
        """Test execution with client exception."""
        mock_client.get_plan.side_effect = Exception("Connection error")

        result = command.execute(mock_client, [])

        assert result == 1


class TestServicesCommand:
    """Test cases for ServicesCommand."""

    @pytest.fixture
    def command(self):
        """Create a ServicesCommand instance."""
        mock_shell = Mock()
        return ServicesCommand(mock_shell)

    @pytest.fixture
    def mock_client(self):
        """Create a mock Pebble client."""
        return Mock(spec=ops.pebble.Client)

    def test_init(self, command):
        """Test command initialization."""
        assert command.name == "pebble-services"
        assert "List services" in command.help
        assert command.category == "Pebble Management"

    def test_execute_help(self, command, mock_client):
        """Test help flag execution."""
        with patch(
            "pebble_shell.utils.command_helpers.handle_help_flag", return_value=True
        ):
            result = command.execute(mock_client, ["--help"])
            assert result == 0

    def test_execute_default(self, command, mock_client):
        """Test execution with default options."""
        mock_service = Mock()
        mock_service.name = "test-service"
        mock_service.startup = "enabled"
        mock_service.current = "active"
        mock_client.get_services.return_value = [mock_service]

        result = command.execute(mock_client, [])

        assert result == 0
        mock_client.get_services.assert_called_once()

    def test_execute_with_service_names(self, command, mock_client):
        """Test execution with specific service names."""
        mock_service = Mock()
        mock_service.name = "test-service"
        mock_service.startup = "enabled"
        mock_service.current = "active"
        mock_client.get_services.return_value = [mock_service]

        result = command.execute(mock_client, ["test-service"])

        assert result == 0
        mock_client.get_services.assert_called_once_with(["test-service"])

    def test_execute_exception(self, command, mock_client):
        """Test execution with client exception."""
        mock_client.get_services.side_effect = Exception("Connection error")

        result = command.execute(mock_client, [])

        assert result == 1


class TestStartCommand:
    """Test cases for StartCommand."""

    @pytest.fixture
    def command(self):
        """Create a StartCommand instance."""
        mock_shell = Mock()
        return StartCommand(mock_shell)

    @pytest.fixture
    def mock_client(self):
        """Create a mock Pebble client."""
        return Mock(spec=ops.pebble.Client)

    def test_init(self, command):
        """Test command initialization."""
        assert command.name == "pebble-start"
        assert "Start services" in command.help
        assert command.category == "Pebble Management"

    def test_execute_help(self, command, mock_client):
        """Test help flag execution."""
        with patch(
            "pebble_shell.utils.command_helpers.handle_help_flag", return_value=True
        ):
            result = command.execute(mock_client, ["--help"])
            assert result == 0

    def test_execute_no_services(self, command, mock_client):
        """Test execution with no services specified."""
        result = command.execute(mock_client, [])

        assert result == 1

    def test_execute_with_services(self, command, mock_client):
        """Test execution with services specified."""
        result = command.execute(mock_client, ["service1", "service2"])

        assert result == 0
        mock_client.start_services.assert_called_once_with(["service1", "service2"])

    def test_execute_exception(self, command, mock_client):
        """Test execution with client exception."""
        mock_client.start_services.side_effect = Exception("Start failed")

        result = command.execute(mock_client, ["service1"])

        assert result == 1


class TestStopCommand:
    """Test cases for StopCommand."""

    @pytest.fixture
    def command(self):
        """Create a StopCommand instance."""
        mock_shell = Mock()
        return StopCommand(mock_shell)

    @pytest.fixture
    def mock_client(self):
        """Create a mock Pebble client."""
        return Mock(spec=ops.pebble.Client)

    def test_init(self, command):
        """Test command initialization."""
        assert command.name == "pebble-stop"
        assert "Stop services" in command.help
        assert command.category == "Pebble Management"

    def test_execute_help(self, command, mock_client):
        """Test help flag execution."""
        with patch(
            "pebble_shell.utils.command_helpers.handle_help_flag", return_value=True
        ):
            result = command.execute(mock_client, ["--help"])
            assert result == 0

    def test_execute_no_services(self, command, mock_client):
        """Test execution with no services specified."""
        result = command.execute(mock_client, [])

        assert result == 1

    def test_execute_with_services(self, command, mock_client):
        """Test execution with services specified."""
        result = command.execute(mock_client, ["service1", "service2"])

        assert result == 0
        mock_client.stop_services.assert_called_once_with(["service1", "service2"])

    def test_execute_exception(self, command, mock_client):
        """Test execution with client exception."""
        mock_client.stop_services.side_effect = Exception("Stop failed")

        result = command.execute(mock_client, ["service1"])

        assert result == 1


class TestRestartCommand:
    """Test cases for RestartCommand."""

    @pytest.fixture
    def command(self):
        """Create a RestartCommand instance."""
        mock_shell = Mock()
        return RestartCommand(mock_shell)

    @pytest.fixture
    def mock_client(self):
        """Create a mock Pebble client."""
        return Mock(spec=ops.pebble.Client)

    def test_init(self, command):
        """Test command initialization."""
        assert command.name == "pebble-restart"
        assert "Restart services" in command.help
        assert command.category == "Pebble Management"

    def test_execute_help(self, command, mock_client):
        """Test help flag execution."""
        with patch(
            "pebble_shell.utils.command_helpers.handle_help_flag", return_value=True
        ):
            result = command.execute(mock_client, ["--help"])
            assert result == 0

    def test_execute_no_services(self, command, mock_client):
        """Test execution with no services specified."""
        result = command.execute(mock_client, [])

        assert result == 1

    def test_execute_with_services(self, command, mock_client):
        """Test execution with services specified."""
        result = command.execute(mock_client, ["service1", "service2"])

        assert result == 0
        mock_client.restart_services.assert_called_once_with(["service1", "service2"])

    def test_execute_exception(self, command, mock_client):
        """Test execution with client exception."""
        mock_client.restart_services.side_effect = Exception("Restart failed")

        result = command.execute(mock_client, ["service1"])

        assert result == 1


class TestSignalCommand:
    """Test cases for SignalCommand."""

    @pytest.fixture
    def command(self):
        """Create a SignalCommand instance."""
        mock_shell = Mock()
        return SignalCommand(mock_shell)

    @pytest.fixture
    def mock_client(self):
        """Create a mock Pebble client."""
        return Mock(spec=ops.pebble.Client)

    def test_init(self, command):
        """Test command initialization."""
        assert command.name == "pebble-signal"
        assert "Send signals" in command.help
        assert command.category == "Pebble Management"

    def test_execute_help(self, command, mock_client):
        """Test help flag execution."""
        with patch(
            "pebble_shell.utils.command_helpers.handle_help_flag", return_value=True
        ):
            result = command.execute(mock_client, ["--help"])
            assert result == 0

    def test_execute_with_service_and_signal(self, command, mock_client):
        """Test execution with service and signal specified."""
        result = command.execute(mock_client, ["service1", "SIGTERM"])

        assert result == 0
        mock_client.send_signal.assert_called_once_with("SIGTERM", ["service1"])

    def test_execute_exception(self, command, mock_client):
        """Test execution with client exception."""
        mock_client.send_signal.side_effect = Exception("Signal failed")

        result = command.execute(mock_client, ["service1", "SIGTERM"])

        assert result == 1
