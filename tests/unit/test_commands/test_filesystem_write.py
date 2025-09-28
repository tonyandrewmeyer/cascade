"""Tests for file operation commands."""

from datetime import datetime
from unittest.mock import MagicMock, Mock, patch

import ops.pebble
import pytest
from ops.pebble import FileInfo, FileType

from pebble_shell.commands.filesystem_write import (
    CopyCommand,
    MakeDirCommand,
    MoveCommand,
    RemoveCommand,
    RemoveDirCommand,
    TouchCommand,
)


class TestCopyCommand:
    """Test cases for CopyCommand."""

    @pytest.fixture
    def command(self):
        """Create CopyCommand instance."""
        mock_shell = Mock()
        mock_shell.console = Mock()
        mock_shell.current_directory = "/"
        mock_shell.home_dir = "/home/user"
        return CopyCommand(mock_shell)

    @pytest.fixture
    def mock_client(self):
        """Create mock Pebble client."""
        client = MagicMock()

        # Mock the pull method to return a context manager
        mock_file = MagicMock()
        mock_file.read.return_value = b"file content"
        client.pull.return_value.__enter__.return_value = mock_file
        client.pull.return_value.__exit__.return_value = None

        # Mock push method
        client.push = MagicMock()

        # Mock list_files to return file info
        client.list_files.return_value = [
            FileInfo(
                path="/src/file.txt",
                name="file.txt",
                type=FileType.FILE,
                size=100,
                permissions=0o644,
                last_modified=datetime.now(),
                user_id=1000,
                user="user",
                group_id=1000,
                group="user",
            )
        ]

        return client

    @patch("pebble_shell.utils.resolve_path")
    @patch("pebble_shell.utils.expand_globs_in_tokens")
    def test_execute_simple_copy(
        self, mock_expand_globs, mock_resolve_path, command, mock_client
    ):
        """Test simple file copy."""
        # Mock the path resolution
        mock_resolve_path.side_effect = ["/src/file.txt", "/dest/file.txt"]
        mock_expand_globs.return_value = ["file.txt"]

        # Execute the command
        result = command.execute(mock_client, ["file.txt", "dest.txt"])

        # Check that it completed successfully (return code 0)
        assert result == 0

        # Check that console print was called (some output was generated)
        command.shell.console.print.assert_called()

    @patch("pebble_shell.utils.resolve_path")
    def test_execute_copy_to_directory(self, mock_resolve_path, command, mock_client):
        """Test copy file to directory."""
        mock_resolve_path.side_effect = ["/src/file.txt", "/dest"]

        # Mock destination as directory
        dir_info = FileInfo(
            path="/dest",
            name="dest",
            type=FileType.DIRECTORY,
            size=0,
            permissions=0o755,
            last_modified=datetime.now(),
            user_id=1000,
            user="user",
            group_id=1000,
            group="user",
        )
        mock_client.get_file_info.return_value = dir_info

        command.execute(mock_client, ["file.txt", "dest"])

        # Assert on console print calls
        command.shell.console.print.assert_called()

    def test_execute_insufficient_args(self, command, mock_client):
        """Test copy with insufficient arguments."""
        command.execute(mock_client, ["file.txt"])

        # Should print usage message
        command.shell.console.print.assert_called()

    @patch("pebble_shell.utils.resolve_path")
    def test_execute_recursive_copy(self, mock_resolve_path, command, mock_client):
        """Test recursive directory copy."""
        mock_resolve_path.side_effect = ["/src/dir", "/dest/dir"]

        command.execute(mock_client, ["-r", "dir", "dest"])

        # Assert on console print calls
        command.shell.console.print.assert_called()


class TestMoveCommand:
    """Test move command."""

    @pytest.fixture
    def command(self):
        """Create MoveCommand instance."""
        shell = MagicMock()
        shell.console.print = MagicMock()
        return MoveCommand(shell)

    @pytest.fixture
    def mock_client(self):
        """Create mock client."""
        client = Mock()
        client.push = Mock()
        client.remove_path = Mock()
        client.list_files.return_value = []
        return client

    @patch("pebble_shell.utils.resolve_path")
    def test_execute_recursive_copy(self, mock_resolve_path, command, mock_client):
        """Test recursive copy of directory."""
        mock_resolve_path.side_effect = ["/src/dir", "/dest"]

        command.execute(mock_client, ["-r", "dir", "dest"])

        # Assert on console print calls
        command.shell.console.print.assert_called()


class TestRemoveCommand:
    """Test cases for RemoveCommand."""

    @pytest.fixture
    def command(self):
        """Create RemoveCommand instance."""
        shell = MagicMock()
        shell.console.print = MagicMock()
        return RemoveCommand(shell)

    @pytest.fixture
    def mock_client(self):
        """Create mock client."""
        client = Mock()

        file_info = FileInfo(
            path="/path/test.txt",
            name="test.txt",
            type=FileType.FILE,
            size=100,
            permissions=0o644,
            last_modified=datetime.now(),
            user_id=1000,
            user="user",
            group_id=1000,
            group="user",
        )
        client.get_file_info.return_value = file_info
        client.remove_path = Mock()
        client.list_files.return_value = []

        return client

    @patch("pebble_shell.utils.resolve_path")
    def test_execute_remove_file(self, mock_resolve_path, command, mock_client):
        """Test remove file."""
        mock_resolve_path.return_value = "/path/file.txt"

        command.execute(mock_client, ["file.txt"])

        # Assert on console print calls
        command.shell.console.print.assert_called()

    @patch("pebble_shell.utils.resolve_path")
    def test_execute_remove_directory_without_recursive(
        self, mock_resolve_path, command, mock_client
    ):
        """Test remove directory without -r flag."""
        mock_resolve_path.return_value = "/path/dir"

        dir_info = FileInfo(
            path="/path/dir",
            name="dir",
            type=FileType.DIRECTORY,
            size=0,
            permissions=0o755,
            last_modified=datetime.now(),
            user_id=1000,
            user="user",
            group_id=1000,
            group="user",
        )
        mock_client.get_file_info.return_value = dir_info

        command.execute(mock_client, ["dir"])

        # Assert on console print calls
        command.shell.console.print.assert_called()

    @patch("pebble_shell.utils.resolve_path")
    def test_execute_remove_directory_recursive(
        self, mock_resolve_path, command, mock_client
    ):
        """Test remove directory with -r flag."""
        mock_resolve_path.return_value = "/path/dir"

        dir_info = FileInfo(
            path="/path/dir",
            name="dir",
            type=FileType.DIRECTORY,
            size=0,
            permissions=0o755,
            last_modified=datetime.now(),
            user_id=1000,
            user="user",
            group_id=1000,
            group="user",
        )
        mock_client.get_file_info.return_value = dir_info

        command.execute(mock_client, ["-r", "dir"])

        # Assert on console print calls
        command.shell.console.print.assert_called()

    def test_execute_no_args(self, command, mock_client):
        """Test remove with no arguments."""
        command.execute(mock_client, [])

        # Assert on console print calls
        command.shell.console.print.assert_called()

    @patch("pebble_shell.utils.resolve_path")
    def test_execute_force_option(self, mock_resolve_path, command, mock_client):
        """Test remove with force option."""
        mock_resolve_path.return_value = "/path/nonexistent"

        mock_client.get_file_info.side_effect = Exception("File not found")

        result = command.execute(mock_client, ["-f", "nonexistent"])

        # Force option should suppress errors and return success
        assert result == 0


class TestMakeDirCommand:
    """Test cases for MakeDirCommand."""

    @pytest.fixture
    def command(self):
        """Create MakeDirCommand instance."""
        shell = MagicMock()
        shell.console.print = MagicMock()
        return MakeDirCommand(shell)

    @pytest.fixture
    def mock_client(self):
        """Create mock client."""
        client = Mock()
        client.make_dir = Mock()
        return client

    @patch("pebble_shell.utils.resolve_path")
    def test_execute_create_directory(self, mock_resolve_path, command, mock_client):
        """Test create directory."""
        mock_resolve_path.return_value = "/path/newdir"

        command.execute(mock_client, ["newdir"])

        # Assert on console print calls
        command.shell.console.print.assert_called()

    @patch("pebble_shell.utils.resolve_path")
    def test_execute_create_with_parents(self, mock_resolve_path, command, mock_client):
        """Test create directory with -p flag."""
        mock_resolve_path.return_value = "/path/to/newdir"

        command.execute(mock_client, ["-p", "newdir"])

        # Assert on console print calls
        command.shell.console.print.assert_called()

    def test_execute_no_args(self, command, mock_client):
        """Test mkdir with no arguments."""
        command.execute(mock_client, [])

        # Assert on console print calls
        command.shell.console.print.assert_called()

    @patch("pebble_shell.commands.filesystem_write.resolve_path")
    def test_execute_error(self, mock_resolve_path, command, mock_client):
        """Test mkdir with error."""
        mock_resolve_path.return_value = "/path/newdir"
        mock_client.make_dir.side_effect = ops.pebble.PathError("base", "message")

        # The command should handle the exception and return error code
        result = command.execute(mock_client, ["newdir"])

        # Should return non-zero exit code for error
        assert result == 1

        # Assert on console print calls (error message should be printed)
        assert command.shell.console.print.called
        error_message = command.shell.console.print.call_args[0][0]
        assert "mkdir:" in error_message
        assert "No such file or directory" in error_message


class TestRemoveDirCommand:
    """Test cases for RemoveDirCommand."""

    @pytest.fixture
    def command(self):
        """Create RemoveDirCommand instance."""
        shell = MagicMock()
        shell.console.print = MagicMock()
        return RemoveDirCommand(shell)

    @pytest.fixture
    def mock_client(self):
        """Create mock client."""
        client = Mock()

        dir_info = FileInfo(
            path="/path/emptydir",
            name="emptydir",
            type=FileType.DIRECTORY,
            size=0,
            permissions=0o755,
            last_modified=datetime.now(),
            user_id=1000,
            user="user",
            group_id=1000,
            group="user",
        )
        client.get_file_info.return_value = dir_info
        client.list_files.return_value = [
            dir_info
        ]  # Return directory itself in list_files
        client.remove_path = Mock()

        return client

    @patch("pebble_shell.utils.resolve_path")
    def test_execute_remove_empty_directory(
        self, mock_resolve_path, command, mock_client
    ):
        """Test remove empty directory."""
        mock_resolve_path.return_value = "/path/emptydir"

        command.execute(mock_client, ["emptydir"])

        # Assert on console print calls
        command.shell.console.print.assert_called()

    @patch("pebble_shell.utils.resolve_path")
    def test_execute_remove_non_empty_directory(
        self, mock_resolve_path, command, mock_client
    ):
        """Test remove non-empty directory."""
        mock_resolve_path.return_value = "/path/nonemptydir"

        # Mock non-empty directory
        file_info = FileInfo(
            path="/path/file.txt",
            name="file.txt",
            type=FileType.FILE,
            size=100,
            permissions=0o644,
            last_modified=datetime.now(),
            user_id=1000,
            user="user",
            group_id=1000,
            group="user",
        )
        mock_client.list_files.return_value = [file_info]

        command.execute(mock_client, ["nonemptydir"])

        # Assert on console print calls
        command.shell.console.print.assert_called()

    @patch("pebble_shell.utils.resolve_path")
    def test_execute_remove_file_not_directory(
        self, mock_resolve_path, command, mock_client
    ):
        """Test rmdir on a file."""
        mock_resolve_path.return_value = "/path/file.txt"

        file_info = FileInfo(
            path="/path/file.txt",
            name="file.txt",
            type=FileType.FILE,
            size=100,
            permissions=0o644,
            last_modified=datetime.now(),
            user_id=1000,
            user="user",
            group_id=1000,
            group="user",
        )
        mock_client.get_file_info.return_value = file_info

        command.execute(mock_client, ["file.txt"])

        # Assert on console print calls
        command.shell.console.print.assert_called()

    def test_execute_no_args(self, command, mock_client):
        """Test rmdir with no arguments."""
        command.execute(mock_client, [])

        # Assert on console print calls
        command.shell.console.print.assert_called()


class TestTouchCommand:
    """Test cases for TouchCommand."""

    @pytest.fixture
    def command(self):
        """Create TouchCommand instance."""
        shell = MagicMock()
        shell.console.print = MagicMock()
        return TouchCommand(shell)

    @pytest.fixture
    def mock_client(self):
        """Create mock client."""
        client = Mock()
        client.push = Mock()
        client.list_files.return_value = []
        return client

    @patch("pebble_shell.commands.filesystem_write.resolve_path")
    def test_execute_create_new_file(self, mock_resolve_path, command, mock_client):
        """Test create new file with touch."""
        mock_resolve_path.return_value = "/path/newfile.txt"

        # File doesn't exist - list_files should raise PathError or APIError
        mock_client.list_files.side_effect = ops.pebble.PathError("path", "not found")

        result = command.execute(mock_client, ["newfile.txt"])

        assert result == 0
        mock_client.push.assert_called_with("/path/newfile.txt", b"", make_dirs=True)
        command.shell.console.print.assert_called_with("created '/path/newfile.txt'")

    @patch("pebble_shell.commands.filesystem_write.resolve_path")
    def test_execute_touch_existing_file(self, mock_resolve_path, command, mock_client):
        """Test touch existing file."""
        mock_resolve_path.return_value = "/path/existing.txt"

        # File exists
        file_info = FileInfo(
            path="/path/existing.txt",
            name="existing.txt",
            type=FileType.FILE,
            size=100,
            permissions=0o644,
            last_modified=datetime.now(),
            user_id=1000,
            user="user",
            group_id=1000,
            group="user",
        )
        mock_client.list_files.return_value = [file_info]
        mock_client.pull = MagicMock()
        mock_client.pull.return_value.__enter__.return_value.read.return_value = (
            b"content"
        )

        result = command.execute(mock_client, ["existing.txt"])

        assert result == 0
        mock_client.pull.assert_called_with("/path/existing.txt")
        mock_client.push.assert_called_with("/path/existing.txt", b"content")
        command.shell.console.print.assert_called_with(
            "touched '/path/existing.txt' (file existed)"
        )

    @patch("pebble_shell.commands.filesystem_write.resolve_path")
    def test_execute_touch_directory(self, mock_resolve_path, command, mock_client):
        """Test touch on directory."""
        mock_resolve_path.return_value = "/path/dir"

        # Target is directory
        dir_info = FileInfo(
            path="/path/dir",
            name="dir",
            type=FileType.DIRECTORY,
            size=0,
            permissions=0o755,
            last_modified=datetime.now(),
            user_id=1000,
            user="user",
            group_id=1000,
            group="user",
        )
        mock_client.list_files.return_value = [dir_info]

        result = command.execute(mock_client, ["dir"])

        assert result == 0
        command.shell.console.print.assert_called_with(
            "touch: /path/dir: Is a directory"
        )

    def test_execute_no_args(self, command, mock_client):
        """Test touch with no arguments."""
        command.execute(mock_client, [])

        # Assert on console print calls
        command.shell.console.print.assert_called()

    @patch("pebble_shell.commands.filesystem_write.resolve_path")
    def test_execute_multiple_files(self, mock_resolve_path, command, mock_client):
        """Test touch multiple files."""
        mock_resolve_path.side_effect = ["/path/file1.txt", "/path/file2.txt"]

        # Both files don't exist
        mock_client.list_files.side_effect = ops.pebble.PathError("path", "not found")

        result = command.execute(mock_client, ["file1.txt", "file2.txt"])

        assert result == 0
        assert mock_client.push.call_count == 2
        command.shell.console.print.assert_any_call("created '/path/file1.txt'")
        command.shell.console.print.assert_any_call("created '/path/file2.txt'")
