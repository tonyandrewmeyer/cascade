"""Unit tests for command helper utilities."""

from unittest.mock import MagicMock, Mock, patch

import ops
from rich.table import Table

from pebble_shell.utils.command_helpers import (
    add_standard_columns,
    check_file_exists,
    create_file_progress,
    create_standard_table,
    create_system_table,
    find_files_by_pattern,
    format_file_header,
    handle_help_flag,
    parse_flags,
    parse_lines_argument,
    process_file_arguments,
    safe_read_file,
    safe_read_file_lines,
    validate_min_args,
)


class TestHandleHelpFlag:
    """Test help flag handling."""

    def test_handle_help_short_flag(self):
        """Test handling -h flag."""
        command = Mock()
        result = handle_help_flag(command, ["-h"])
        assert result is True
        command.show_help.assert_called_once()

    def test_handle_help_long_flag(self):
        """Test handling --help flag."""
        command = Mock()
        result = handle_help_flag(command, ["--help"])
        assert result is True
        command.show_help.assert_called_once()

    def test_no_help_flag(self):
        """Test when no help flag is present."""
        command = Mock()
        result = handle_help_flag(command, ["file.txt"])
        assert result is False
        command.show_help.assert_not_called()

    def test_help_flag_with_other_args(self):
        """Test help flag mixed with other arguments."""
        command = Mock()
        result = handle_help_flag(command, ["file.txt", "-h", "other"])
        assert result is True
        command.show_help.assert_called_once()


class TestValidateMinArgs:
    """Test argument validation."""

    def test_validate_sufficient_args(self):
        """Test validation with sufficient arguments."""
        shell = Mock()
        result = validate_min_args(shell, ["arg1", "arg2"], 2)
        assert result is True
        shell.console.print.assert_not_called()

    def test_validate_insufficient_args(self):
        """Test validation with insufficient arguments."""
        shell = Mock()
        result = validate_min_args(shell, ["arg1"], 2)
        assert result is False
        shell.console.print.assert_called_once()

    def test_validate_with_usage_message(self):
        """Test validation with custom usage message."""
        shell = Mock()
        result = validate_min_args(shell, ["arg1"], 2, "cmd <file1> <file2>")
        assert result is False
        shell.console.print.assert_called_once_with("Usage: cmd <file1> <file2>")


class TestParseFlags:
    """Test flag parsing functionality."""

    def test_parse_bool_flags(self):
        """Test parsing boolean flags."""
        result = parse_flags(["-l", "-a", "file.txt"], {"l": bool, "a": bool})
        assert result is not None
        flags, remaining = result
        assert flags == {"l": True, "a": True}
        assert remaining == ["file.txt"]

    def test_parse_combined_bool_flags(self):
        """Test parsing combined boolean flags like -la."""
        result = parse_flags(["-la", "file.txt"], {"l": bool, "a": bool})
        assert result is not None
        flags, remaining = result
        assert flags == {"l": True, "a": True}
        assert remaining == ["file.txt"]

    def test_parse_string_flag(self):
        """Test parsing string flag with argument."""
        result = parse_flags(["-f", "value", "file.txt"], {"f": str})
        assert result is not None
        flags, remaining = result
        assert flags == {"f": "value"}
        assert remaining == ["file.txt"]

    def test_parse_int_flag(self):
        """Test parsing integer flag with argument."""
        result = parse_flags(["-n", "10", "file.txt"], {"n": int})
        assert result is not None
        flags, remaining = result
        assert flags == {"n": 10}
        assert remaining == ["file.txt"]

    def test_invalid_flag(self):
        """Test handling invalid flag."""
        shell = Mock()
        result = parse_flags(["-x"], {"l": bool}, shell)
        assert result is None
        shell.console.print.assert_called_once_with("Error: Invalid option -x")

    def test_missing_string_flag_argument(self):
        """Test handling string flag without argument."""
        shell = Mock()
        result = parse_flags(["-f"], {"f": str}, shell)
        assert result is None
        shell.console.print.assert_called_once_with(
            "Error: Flag -f requires an argument"
        )

    def test_invalid_int_flag_argument(self):
        """Test handling invalid integer argument."""
        shell = Mock()
        result = parse_flags(["-n", "abc"], {"n": int}, shell)
        assert result is None
        shell.console.print.assert_called_once_with(
            "Error: Flag -n requires an integer argument"
        )

        def test_mixed_flag_types(self):
            """Test parsing mixed flag types."""
            result = parse_flags(["-l", "-n", "5", "file.txt"], {"l": bool, "n": int})
            assert result is not None
            flags, remaining = result
            assert flags == {"l": True, "n": 5}
            assert remaining == ["file.txt"]


class TestProcessFileArguments:
    """Test file argument processing."""

    @patch("pebble_shell.utils.command_helpers.expand_globs_in_tokens")
    @patch("pebble_shell.utils.command_helpers.resolve_path")
    def test_process_with_globs(self, mock_resolve, mock_expand):
        """Test processing file arguments with glob expansion."""
        shell = Mock()
        shell.current_directory = "/current"
        shell.home_dir = "/home/user"
        client = Mock()

        mock_expand.return_value = ["file1.txt", "file2.txt"]
        mock_resolve.side_effect = lambda cur_dir, f, home: f"/resolved/{f}"

        result = process_file_arguments(shell, client, ["*.txt"])

        assert result == ["/resolved/file1.txt", "/resolved/file2.txt"]
        mock_expand.assert_called_once_with(client, ["*.txt"], "/current")

    @patch("pebble_shell.utils.command_helpers.resolve_path")
    def test_process_without_globs(self, mock_resolve):
        """Test processing file arguments without glob expansion."""
        shell = Mock()
        shell.current_directory = "/current"
        shell.home_dir = "/home/user"

        mock_resolve.side_effect = lambda cur_dir, f, home: f"/resolved/{f}"

        result = process_file_arguments(
            shell, Mock(), ["file1.txt", "file2.txt"], allow_globs=False
        )

        assert result == ["/resolved/file1.txt", "/resolved/file2.txt"]

    @patch("pebble_shell.utils.command_helpers.expand_globs_in_tokens")
    def test_process_no_glob_matches(self, mock_expand):
        """Test when glob expansion returns no matches."""
        shell = Mock()
        client = Mock()

        mock_expand.return_value = []

        result = process_file_arguments(shell, client, ["*.nonexistent"])

        assert result is None
        shell.console.print.assert_called_once_with("Error: No files match the pattern")

    def test_process_insufficient_files(self):
        """Test when insufficient files provided."""
        shell = Mock()

        result = process_file_arguments(
            shell, Mock(), ["file1.txt"], allow_globs=False, min_files=2
        )

        assert result is None
        shell.console.print.assert_called_once_with(
            "Error: At least 2 file(s) required"
        )

    def test_process_too_many_files(self):
        """Test when too many files provided."""
        shell = Mock()

        result = process_file_arguments(
            shell,
            Mock(),
            ["file1.txt", "file2.txt", "file3.txt"],
            allow_globs=False,
            max_files=2,
        )

        assert result is None
        shell.console.print.assert_called_once_with("Error: At most 2 file(s) allowed")


class TestSafeReadFile:
    """Test safe file reading functionality."""

    def test_successful_read(self):
        """Test successful file reading."""
        client = Mock()
        file_mock = Mock()
        file_mock.read.return_value = "file content"

        # Set up the context manager properly
        context_manager = MagicMock()
        context_manager.__enter__.return_value = file_mock
        context_manager.__exit__.return_value = False
        client.pull.return_value = context_manager

        result = safe_read_file(client, "/path/to/file")

        assert result == "file content"
        client.pull.assert_called_once_with("/path/to/file")

    def test_file_not_found(self):
        """Test handling file not found error."""
        client = Mock()
        client.pull.side_effect = ops.pebble.PathError("not found", "Path not found")
        shell = Mock()

        result = safe_read_file(client, "/nonexistent", shell)

        assert result is None
        shell.console.print.assert_called_once_with(
            "Error reading file /nonexistent: not found - Path not found"
        )

    def test_binary_mode(self):
        """Test reading text content that looks like binary."""
        client = Mock()
        file_mock = Mock()
        file_mock.read.return_value = "text content"

        # Set up the context manager properly
        context_manager = MagicMock()
        context_manager.__enter__.return_value = file_mock
        context_manager.__exit__.return_value = False
        client.pull.return_value = context_manager

        result = safe_read_file(client, "/path/to/file")

        assert result == "text content"
        client.pull.assert_called_once_with("/path/to/file")


class TestSafeReadFileLines:
    """Test safe file line reading."""

    def test_successful_read_lines(self):
        """Test successful reading of file lines."""
        client = Mock()
        file_mock = Mock()
        file_mock.read.return_value = "line1\nline2\nline3"

        # Set up the context manager properly
        context_manager = MagicMock()
        context_manager.__enter__.return_value = file_mock
        context_manager.__exit__.return_value = False
        client.pull.return_value = context_manager

        result = safe_read_file_lines(client, "/path/to/file")

        assert result == ["line1", "line2", "line3"]

    def test_read_lines_with_binary_content(self):
        """Test reading lines from binary content."""
        client = Mock()
        file_mock = Mock()
        file_mock.read.return_value = b"line1\nline2"

        # Set up the context manager properly
        context_manager = MagicMock()
        context_manager.__enter__.return_value = file_mock
        context_manager.__exit__.return_value = False
        client.pull.return_value = context_manager

        result = safe_read_file_lines(client, "/path/to/file")

        assert result == ["line1", "line2"]

    def test_read_lines_file_error(self):
        """Test handling file read error."""
        client = Mock()
        client.pull.side_effect = ops.pebble.PathError("not found", "Path not found")
        shell = Mock()

        result = safe_read_file_lines(client, "/nonexistent", shell)

        assert result is None


class TestTableCreation:
    """Test Rich table creation utilities."""

    def test_create_standard_table(self):
        """Test creating standard table."""
        table = create_standard_table()

        assert isinstance(table, Table)
        assert table.show_header is True
        assert table.header_style == "bold magenta"

    def test_create_system_table(self):
        """Test creating system table."""
        table = create_system_table()

        assert isinstance(table, Table)
        assert table.show_header is True
        assert table.header_style == "bold magenta"
        assert table.border_style == "bright_blue"

    def test_add_standard_columns(self):
        """Test adding standard columns to table."""
        table = create_standard_table()
        add_standard_columns(table, ["pid", "user", "command"])

        # Check that columns were added
        assert len(table.columns) == 3

    def test_add_unknown_column(self):
        """Test adding unknown column type."""
        table = create_standard_table()
        add_standard_columns(table, ["unknown_column"])

        # Should still add the column with fallback styling
        assert len(table.columns) == 1


class TestFileOperations:
    """Test file operation utilities."""

    def test_check_file_exists_true(self):
        """Test checking existing file."""
        client = Mock()
        file_info = Mock()
        file_info.name = "test.txt"
        client.list_files.return_value = [file_info]

        result = check_file_exists(client, "/path/test.txt")

        assert result is True
        client.list_files.assert_called_once_with("/path")

    def test_check_file_exists_false(self):
        """Test checking non-existing file."""
        client = Mock()
        client.list_files.return_value = []

        result = check_file_exists(client, "/path/nonexistent.txt")

        assert result is False

    def test_check_file_exists_error(self):
        """Test handling error when checking file."""
        client = Mock()
        client.list_files.side_effect = ops.pebble.PathError(
            "permission denied", "Permission denied"
        )
        shell = Mock()

        result = check_file_exists(client, "/path/test.txt", shell)

        assert result is False
        shell.console.print.assert_called_once_with(
            "Error checking file /path/test.txt: permission denied - Permission denied"
        )

    @patch("fnmatch.fnmatch")
    def test_find_files_by_pattern(self, mock_fnmatch):
        """Test finding files by pattern."""
        client = Mock()
        file1 = Mock()
        file1.name = "test1.txt"
        file2 = Mock()
        file2.name = "test2.log"
        client.list_files.return_value = [file1, file2]

        mock_fnmatch.side_effect = lambda name, pattern: name.endswith(".txt")

        result = find_files_by_pattern(client, "/path", "*.txt")

        assert result == ["/path/test1.txt"]


class TestHelperFunctions:
    """Test miscellaneous helper functions."""

    def test_parse_lines_argument(self):
        """Test parsing lines argument."""
        lines, remaining = parse_lines_argument(["10", "file.txt", "20"])

        # Should take the last numeric argument found
        assert lines == 20
        assert remaining == ["file.txt"]

    def test_parse_lines_argument_default(self):
        """Test parsing lines with default value."""
        lines, remaining = parse_lines_argument(["file.txt"])

        assert lines == 10  # Default value
        assert remaining == ["file.txt"]

    def test_format_file_header_multiple_files(self):
        """Test formatting header for multiple files."""
        header = format_file_header("/path/file.txt", 3)

        assert header == "==> /path/file.txt <=="

    def test_format_file_header_single_file(self):
        """Test formatting header for single file."""
        header = format_file_header("/path/file.txt", 1)

        assert header is None

    def test_create_file_progress(self):
        """Test creating file progress bar."""
        progress = create_file_progress()

        # Should return a Progress instance
        assert progress is not None
