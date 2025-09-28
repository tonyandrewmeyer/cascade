"""Unit tests for error_handling utility module."""

from unittest.mock import MagicMock

import ops
from rich.console import Console

from pebble_shell.utils.error_handling import (
    handle_generic_pebble_error,
    handle_pebble_api_error,
    handle_pebble_path_error,
    safe_pebble_operation,
    show_file_not_found_error,
    show_permission_error,
    show_usage_error,
    validate_file_exists,
    with_error_context,
)


class TestHandlePebblePathError:
    """Tests for handle_pebble_path_error function."""

    def test_handle_pebble_path_error(self):
        """Test handling PathError with standardized formatting."""
        console = MagicMock(spec=Console)
        error = ops.pebble.PathError("kind", "Permission denied")

        handle_pebble_path_error(console, "read file", "/test/path", error)

        # Verify console.print was called with a Panel
        console.print.assert_called_once()
        panel_arg = console.print.call_args[0][0]
        assert hasattr(panel_arg, "renderable")  # It's a Panel


class TestHandlePebbleApiError:
    """Tests for handle_pebble_api_error function."""

    def test_handle_pebble_api_error(self):
        """Test handling APIError with standardized formatting."""
        console = MagicMock(spec=Console)
        error = ops.pebble.APIError({"error": "body"}, 500, "status", "message")

        handle_pebble_api_error(console, "list files", error)

        # Verify console.print was called with a Panel
        console.print.assert_called_once()
        panel_arg = console.print.call_args[0][0]
        assert hasattr(panel_arg, "renderable")  # It's a Panel


class TestHandleGenericPebbleError:
    """Tests for handle_generic_pebble_error function."""

    def test_handle_generic_pebble_error_with_context(self):
        """Test handling generic error with context."""
        console = MagicMock(spec=Console)
        error = ValueError("Test error")

        handle_generic_pebble_error(console, "test operation", error, "test context")

        # Verify console.print was called with a Panel
        console.print.assert_called_once()
        panel_arg = console.print.call_args[0][0]
        assert hasattr(panel_arg, "renderable")  # It's a Panel

    def test_handle_generic_pebble_error_without_context(self):
        """Test handling generic error without context."""
        console = MagicMock(spec=Console)
        error = RuntimeError("Test error")

        handle_generic_pebble_error(console, "test operation", error)

        # Verify console.print was called with a Panel
        console.print.assert_called_once()
        panel_arg = console.print.call_args[0][0]
        assert hasattr(panel_arg, "renderable")  # It's a Panel


class TestSafePebbleOperation:
    """Tests for safe_pebble_operation function."""

    def test_safe_pebble_operation_success(self):
        """Test safe operation execution when operation succeeds."""
        console = MagicMock(spec=Console)

        def test_operation():
            return "success"

        result = safe_pebble_operation(console, test_operation, "test operation")

        assert result == "success"
        console.print.assert_not_called()

    def test_safe_pebble_operation_path_error(self):
        """Test safe operation execution when PathError occurs."""
        console = MagicMock(spec=Console)

        def test_operation():
            raise ops.pebble.PathError("kind", "Not found")

        result = safe_pebble_operation(
            console, test_operation, "test operation", "/test/path"
        )

        assert result is None
        console.print.assert_called_once()

    def test_safe_pebble_operation_api_error(self):
        """Test safe operation execution when APIError occurs."""
        console = MagicMock(spec=Console)

        def test_operation():
            raise ops.pebble.APIError({"error": "body"}, 500, "status", "message")

        result = safe_pebble_operation(console, test_operation, "test operation")

        assert result is None
        console.print.assert_called_once()

    def test_safe_pebble_operation_generic_error(self):
        """Test safe operation execution when generic error occurs."""
        console = MagicMock(spec=Console)

        def test_operation():
            raise ValueError("Test error")

        result = safe_pebble_operation(console, test_operation, "test operation")

        assert result is None
        console.print.assert_called_once()


class TestShowFileNotFoundError:
    """Tests for show_file_not_found_error function."""

    def test_show_file_not_found_error_with_command(self):
        """Test showing file not found error with command context."""
        console = MagicMock(spec=Console)

        show_file_not_found_error(console, "/test/path", "ls")

        console.print.assert_called_once()
        call_args = console.print.call_args[0][0]
        assert "ls:" in call_args
        assert "/test/path" in call_args

    def test_show_file_not_found_error_without_command(self):
        """Test showing file not found error without command context."""
        console = MagicMock(spec=Console)

        show_file_not_found_error(console, "/test/path")

        console.print.assert_called_once()
        call_args = console.print.call_args[0][0]
        assert "/test/path" in call_args


class TestShowPermissionError:
    """Tests for show_permission_error function."""

    def test_show_permission_error_with_command(self):
        """Test showing permission error with command context."""
        console = MagicMock(spec=Console)

        show_permission_error(console, "/test/path", "read", "cat")

        console.print.assert_called_once()
        call_args = console.print.call_args[0][0]
        assert "cat:" in call_args
        assert "read" in call_args
        assert "/test/path" in call_args

    def test_show_permission_error_without_command(self):
        """Test showing permission error without command context."""
        console = MagicMock(spec=Console)

        show_permission_error(console, "/test/path", "write")

        console.print.assert_called_once()
        call_args = console.print.call_args[0][0]
        assert "write" in call_args
        assert "/test/path" in call_args


class TestValidateFileExists:
    """Tests for validate_file_exists function."""

    def test_validate_file_exists_success(self):
        """Test file existence validation when file exists."""
        console = MagicMock(spec=Console)
        client = MagicMock()
        client.list_files.return_value = [MagicMock()]  # File exists

        result = validate_file_exists(console, client, "/test/path", "ls")

        assert result is True
        client.list_files.assert_called_once_with("/test/path", itself=True)
        console.print.assert_not_called()

    def test_validate_file_exists_path_error(self):
        """Test file existence validation when file doesn't exist."""
        console = MagicMock(spec=Console)
        client = MagicMock()
        client.list_files.side_effect = ops.pebble.PathError("kind", "Not found")

        result = validate_file_exists(console, client, "/test/path", "ls")

        assert result is False
        console.print.assert_called_once()

    def test_validate_file_exists_api_error(self):
        """Test file existence validation when API error occurs."""
        console = MagicMock(spec=Console)
        client = MagicMock()
        client.list_files.side_effect = ops.pebble.APIError(
            {"error": "body"}, 500, "status", "message"
        )

        result = validate_file_exists(console, client, "/test/path")

        assert result is False
        console.print.assert_called_once()


class TestShowUsageError:
    """Tests for show_usage_error function."""

    def test_show_usage_error_with_message(self):
        """Test showing usage error with additional message."""
        console = MagicMock(spec=Console)

        result = show_usage_error(
            console, "ls", "ls [options] [file...]", "invalid option"
        )

        assert result == 1
        assert console.print.call_count == 2
        # First call should have the error message
        first_call = console.print.call_args_list[0][0][0]
        assert "ls:" in first_call
        assert "invalid option" in first_call
        # Second call should have the usage
        second_call = console.print.call_args_list[1][0][0]
        assert "Usage:" in second_call

    def test_show_usage_error_without_message(self):
        """Test showing usage error without additional message."""
        console = MagicMock(spec=Console)

        result = show_usage_error(console, "ls", "ls [options] [file...]")

        assert result == 1
        console.print.assert_called_once()
        call_args = console.print.call_args[0][0]
        assert "Usage:" in call_args


class TestWithErrorContext:
    """Tests for with_error_context decorator."""

    def test_with_error_context_success(self):
        """Test decorator when function succeeds."""

        class MockCommand:
            def __init__(self):
                self.console = MagicMock(spec=Console)

        @with_error_context("test operation", "test context")
        def test_method(self):
            return "success"

        command = MockCommand()
        result = test_method(command)

        assert result == "success"
        command.console.print.assert_not_called()

    def test_with_error_context_path_error(self):
        """Test decorator when PathError occurs."""

        class MockCommand:
            def __init__(self):
                self.console = MagicMock(spec=Console)

        @with_error_context("test operation", "test context")
        def test_method(self):
            raise ops.pebble.PathError("kind", "Not found")

        command = MockCommand()
        result = test_method(command)

        assert result is None
        command.console.print.assert_called_once()

    def test_with_error_context_api_error(self):
        """Test decorator when APIError occurs."""

        class MockCommand:
            def __init__(self):
                self.console = MagicMock(spec=Console)

        @with_error_context("test operation")
        def test_method(self):
            raise ops.pebble.APIError({"error": "body"}, 500, "status", "message")

        command = MockCommand()
        result = test_method(command)

        assert result is None
        command.console.print.assert_called_once()

    def test_with_error_context_generic_error(self):
        """Test decorator when generic error occurs."""

        class MockCommand:
            def __init__(self):
                self.console = MagicMock(spec=Console)

        @with_error_context("test operation", "test context")
        def test_method(self):
            raise ValueError("Test error")

        command = MockCommand()
        result = test_method(command)

        assert result is None
        command.console.print.assert_called_once()
