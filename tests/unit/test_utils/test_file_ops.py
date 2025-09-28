"""Tests for file operation utilities."""

from unittest.mock import Mock, patch

import ops
from src.pebble_shell.utils.file_ops import (
    copy_directory_recursive,
    copy_file_with_progress,
    count_files_recursive,
    ensure_parent_directory,
    file_exists,
    get_directory_size,
    get_file_info,
    list_directory_safe,
    move_file_with_progress,
    remove_file_recursive,
    safe_pull_file,
    safe_push_file,
)


class TestBasicFileOperations:
    """Test basic file operation utilities."""

    def test_safe_pull_file_success(self):
        """Test successful file pull."""
        mock_client = Mock()
        mock_file = Mock()
        mock_file.read.return_value = "file content"

        # Properly mock the context manager
        mock_context = Mock()
        mock_context.__enter__ = Mock(return_value=mock_file)
        mock_context.__exit__ = Mock(return_value=None)
        mock_client.pull.return_value = mock_context

        result = safe_pull_file(mock_client, "/test/file.txt")

        assert result == "file content"
        mock_client.pull.assert_called_once_with("/test/file.txt")

    def test_safe_pull_file_error(self):
        """Test file pull with error."""
        mock_client = Mock()
        mock_client.pull.side_effect = ops.pebble.PathError("file", "not found")

        result = safe_pull_file(mock_client, "/test/missing.txt")

        assert result is None

    def test_safe_push_file_success(self):
        """Test successful file push."""
        mock_client = Mock()

        result = safe_push_file(mock_client, "/test/file.txt", "content")

        assert result is True
        mock_client.push.assert_called_once_with(
            "/test/file.txt", "content", make_dirs=True
        )

    def test_safe_push_file_no_make_dirs(self):
        """Test file push without making directories."""
        mock_client = Mock()

        result = safe_push_file(
            mock_client, "/test/file.txt", "content", make_dirs=False
        )

        assert result is True
        mock_client.push.assert_called_once_with(
            "/test/file.txt", "content", make_dirs=False
        )

    def test_safe_push_file_error(self):
        """Test file push with error."""
        mock_client = Mock()
        mock_client.push.side_effect = ops.pebble.PathError("file", "permission denied")

        result = safe_push_file(mock_client, "/test/file.txt", "content")

        assert result is False

    def test_list_directory_safe_success(self):
        """Test successful directory listing."""
        mock_client = Mock()
        mock_files = [Mock(name="file1"), Mock(name="file2")]
        mock_client.list_files.return_value = mock_files

        result = list_directory_safe(mock_client, "/test/dir")

        assert result == mock_files
        mock_client.list_files.assert_called_once_with("/test/dir")

    def test_list_directory_safe_error(self):
        """Test directory listing with error."""
        mock_client = Mock()
        mock_client.list_files.side_effect = ops.pebble.PathError("dir", "not found")

        result = list_directory_safe(mock_client, "/test/missing")

        assert result is None


class TestFileExistence:
    """Test file existence checking utilities."""

    def test_file_exists_true(self):
        """Test file exists returns True when file is found."""
        mock_client = Mock()
        mock_file = Mock()
        mock_file.name = "test.txt"
        mock_client.list_files.return_value = [mock_file]

        result = file_exists(mock_client, "/path/test.txt")

        assert result is True
        mock_client.list_files.assert_called_once_with("/path")

    def test_file_exists_false(self):
        """Test file exists returns False when file is not found."""
        mock_client = Mock()
        mock_file = Mock()
        mock_file.name = "other.txt"
        mock_client.list_files.return_value = [mock_file]

        result = file_exists(mock_client, "/path/test.txt")

        assert result is False

    def test_file_exists_error(self):
        """Test file exists returns False on error."""
        mock_client = Mock()
        mock_client.list_files.side_effect = ops.pebble.PathError("dir", "not found")

        result = file_exists(mock_client, "/path/test.txt")

        assert result is False

    def test_file_exists_root_path(self):
        """Test file exists with root path."""
        mock_client = Mock()
        mock_file = Mock()
        mock_file.name = "test.txt"
        mock_client.list_files.return_value = [mock_file]

        result = file_exists(mock_client, "test.txt")

        assert result is True
        mock_client.list_files.assert_called_once_with(".")

    def test_get_file_info_found(self):
        """Test getting file info when file exists."""
        mock_client = Mock()
        mock_file = Mock()
        mock_file.name = "test.txt"
        mock_client.list_files.return_value = [mock_file]

        result = get_file_info(mock_client, "/path/test.txt")

        assert result == mock_file

    def test_get_file_info_not_found(self):
        """Test getting file info when file doesn't exist."""
        mock_client = Mock()
        mock_file = Mock()
        mock_file.name = "other.txt"
        mock_client.list_files.return_value = [mock_file]

        result = get_file_info(mock_client, "/path/test.txt")

        assert result is None

    def test_get_file_info_error(self):
        """Test getting file info with error."""
        mock_client = Mock()
        mock_client.list_files.side_effect = ops.pebble.PathError("dir", "not found")

        result = get_file_info(mock_client, "/path/test.txt")

        assert result is None


class TestCopyOperations:
    """Test file and directory copying utilities."""

    def test_copy_file_with_progress_success(self):
        """Test successful file copy with progress."""
        mock_client = Mock()
        mock_console = Mock()
        mock_progress = Mock()

        # Mock successful pull and push
        with (
            patch("src.pebble_shell.utils.file_ops.safe_pull_file") as mock_pull,
            patch("src.pebble_shell.utils.file_ops.safe_push_file") as mock_push,
        ):
            mock_pull.return_value = "file content"
            mock_push.return_value = True

            result = copy_file_with_progress(
                mock_client,
                mock_console,
                "/src/file.txt",
                "/dst/file.txt",
                mock_progress,
                1,
            )

        assert result is True
        mock_pull.assert_called_once_with(mock_client, "/src/file.txt")
        mock_push.assert_called_once_with(
            mock_client, "/dst/file.txt", "file content", make_dirs=True
        )
        mock_console.print.assert_called_with("'/src/file.txt' -> '/dst/file.txt'")
        mock_progress.advance.assert_called_once_with(1)

    def test_copy_file_with_progress_no_progress(self):
        """Test file copy without progress tracking."""
        mock_client = Mock()
        mock_console = Mock()

        with (
            patch("src.pebble_shell.utils.file_ops.safe_pull_file") as mock_pull,
            patch("src.pebble_shell.utils.file_ops.safe_push_file") as mock_push,
        ):
            mock_pull.return_value = "file content"
            mock_push.return_value = True

            result = copy_file_with_progress(
                mock_client, mock_console, "/src/file.txt", "/dst/file.txt"
            )

        assert result is True

    def test_copy_file_with_progress_pull_failure(self):
        """Test file copy with pull failure."""
        mock_client = Mock()
        mock_console = Mock()

        with patch("src.pebble_shell.utils.file_ops.safe_pull_file") as mock_pull:
            mock_pull.return_value = None

            result = copy_file_with_progress(
                mock_client, mock_console, "/src/file.txt", "/dst/file.txt"
            )

        assert result is False
        mock_console.print.assert_called_with("cannot read source file: /src/file.txt")

    def test_copy_file_with_progress_push_failure(self):
        """Test file copy with push failure."""
        mock_client = Mock()
        mock_console = Mock()

        with (
            patch("src.pebble_shell.utils.file_ops.safe_pull_file") as mock_pull,
            patch("src.pebble_shell.utils.file_ops.safe_push_file") as mock_push,
        ):
            mock_pull.return_value = "content"
            mock_push.return_value = False

            result = copy_file_with_progress(
                mock_client, mock_console, "/src/file.txt", "/dst/file.txt"
            )

        assert result is False
        mock_console.print.assert_called_with(
            "cannot write destination file: /dst/file.txt"
        )

    def test_copy_directory_recursive_success(self):
        """Test successful recursive directory copy."""
        mock_client = Mock()
        mock_console = Mock()

        # Mock directory listing
        mock_file = Mock()
        mock_file.name = "file.txt"
        mock_file.type = ops.pebble.FileType.FILE

        mock_subdir = Mock()
        mock_subdir.name = "subdir"
        mock_subdir.type = ops.pebble.FileType.DIRECTORY

        with (
            patch("src.pebble_shell.utils.file_ops.list_directory_safe") as mock_list,
            patch(
                "src.pebble_shell.utils.file_ops.copy_file_with_progress"
            ) as mock_copy_file,
            patch(
                "src.pebble_shell.utils.file_ops.copy_directory_recursive"
            ) as mock_copy_dir,
        ):
            mock_list.return_value = [mock_file, mock_subdir]
            mock_copy_file.return_value = True
            mock_copy_dir.return_value = True

            result = copy_directory_recursive(
                mock_client, mock_console, "/src/dir", "/dst/dir"
            )

        assert result is True
        mock_client.make_dir.assert_called_once_with("/dst/dir", make_parents=True)
        mock_console.print.assert_called_with("'/src/dir' -> '/dst/dir' (directory)")
        mock_copy_file.assert_called_once()
        mock_copy_dir.assert_called_once()

    def test_copy_directory_recursive_list_failure(self):
        """Test directory copy with listing failure."""
        mock_client = Mock()
        mock_console = Mock()

        with patch("src.pebble_shell.utils.file_ops.list_directory_safe") as mock_list:
            mock_list.return_value = None

            result = copy_directory_recursive(
                mock_client, mock_console, "/src/dir", "/dst/dir"
            )

        assert result is False
        mock_console.print.assert_any_call("cannot list directory: /src/dir")


class TestRemoveOperations:
    """Test file and directory removal utilities."""

    def test_remove_file_recursive_file_success(self):
        """Test successful file removal."""
        mock_client = Mock()
        mock_console = Mock()
        mock_progress = Mock()

        mock_file_info = Mock()
        mock_file_info.type = ops.pebble.FileType.FILE

        with patch("src.pebble_shell.utils.file_ops.get_file_info") as mock_get_info:
            mock_get_info.return_value = mock_file_info

            result = remove_file_recursive(
                mock_client,
                mock_console,
                "/test/file.txt",
                progress=mock_progress,
                task_id=1,
            )

        assert result is True
        mock_client.remove_path.assert_called_once_with("/test/file.txt")
        mock_console.print.assert_called_with("removed '/test/file.txt'")
        mock_progress.advance.assert_called_once_with(1)

    def test_remove_file_recursive_file_not_found_force(self):
        """Test file removal when file not found with force=True."""
        mock_client = Mock()
        mock_console = Mock()

        with patch("src.pebble_shell.utils.file_ops.get_file_info") as mock_get_info:
            mock_get_info.return_value = None

            result = remove_file_recursive(
                mock_client, mock_console, "/test/file.txt", force=True
            )

        assert result is True

    def test_remove_file_recursive_file_not_found_no_force(self):
        """Test file removal when file not found with force=False."""
        mock_client = Mock()
        mock_console = Mock()

        with patch("src.pebble_shell.utils.file_ops.get_file_info") as mock_get_info:
            mock_get_info.return_value = None

            result = remove_file_recursive(
                mock_client, mock_console, "/test/file.txt", force=False
            )

        assert result is False
        mock_console.print.assert_called_with(
            "cannot remove '/test/file.txt': file not found"
        )

    def test_remove_file_recursive_directory(self):
        """Test recursive directory removal."""
        mock_client = Mock()
        mock_console = Mock()

        mock_dir_info = Mock()
        mock_dir_info.type = ops.pebble.FileType.DIRECTORY

        mock_sub_file = Mock()
        mock_sub_file.name = "file.txt"

        with (
            patch("src.pebble_shell.utils.file_ops.get_file_info") as mock_get_info,
            patch("src.pebble_shell.utils.file_ops.list_directory_safe") as mock_list,
            patch(
                "src.pebble_shell.utils.file_ops.remove_file_recursive"
            ) as mock_remove,
        ):
            mock_get_info.return_value = mock_dir_info
            mock_list.return_value = [mock_sub_file]
            mock_remove.return_value = True

            result = remove_file_recursive(mock_client, mock_console, "/test/dir")

        assert result is True
        mock_remove.assert_called_once()


class TestMoveOperations:
    """Test file and directory move utilities."""

    def test_move_file_with_progress_file(self):
        """Test moving a file."""
        mock_client = Mock()
        mock_console = Mock()

        mock_file_info = Mock()
        mock_file_info.type = ops.pebble.FileType.FILE

        with (
            patch("src.pebble_shell.utils.file_ops.get_file_info") as mock_get_info,
            patch(
                "src.pebble_shell.utils.file_ops.copy_file_with_progress"
            ) as mock_copy,
            patch(
                "src.pebble_shell.utils.file_ops.remove_file_recursive"
            ) as mock_remove,
        ):
            mock_get_info.return_value = mock_file_info
            mock_copy.return_value = True
            mock_remove.return_value = True

            result = move_file_with_progress(
                mock_client, mock_console, "/src/file.txt", "/dst/file.txt"
            )

        assert result is True
        mock_copy.assert_called_once()
        mock_remove.assert_called_once()

    def test_move_file_with_progress_directory(self):
        """Test moving a directory."""
        mock_client = Mock()
        mock_console = Mock()

        mock_dir_info = Mock()
        mock_dir_info.type = ops.pebble.FileType.DIRECTORY

        with (
            patch("src.pebble_shell.utils.file_ops.get_file_info") as mock_get_info,
            patch(
                "src.pebble_shell.utils.file_ops.copy_directory_recursive"
            ) as mock_copy,
            patch(
                "src.pebble_shell.utils.file_ops.remove_file_recursive"
            ) as mock_remove,
        ):
            mock_get_info.return_value = mock_dir_info
            mock_copy.return_value = True
            mock_remove.return_value = True

            result = move_file_with_progress(
                mock_client, mock_console, "/src/dir", "/dst/dir"
            )

        assert result is True

    def test_move_file_with_progress_not_found(self):
        """Test moving a non-existent file."""
        mock_client = Mock()
        mock_console = Mock()

        with patch("src.pebble_shell.utils.file_ops.get_file_info") as mock_get_info:
            mock_get_info.return_value = None

            result = move_file_with_progress(
                mock_client, mock_console, "/src/file.txt", "/dst/file.txt"
            )

        assert result is False
        mock_console.print.assert_called_with(
            "cannot stat '/src/file.txt': file not found"
        )


class TestUtilityFunctions:
    """Test utility functions."""

    def test_ensure_parent_directory_success(self):
        """Test ensuring parent directory exists."""
        mock_client = Mock()

        result = ensure_parent_directory(mock_client, "/path/to/file.txt")

        assert result is True
        mock_client.make_dir.assert_called_once_with("/path/to", make_parents=True)

    def test_ensure_parent_directory_no_parent(self):
        """Test ensuring parent directory when no parent needed."""
        mock_client = Mock()

        result = ensure_parent_directory(mock_client, "file.txt")

        assert result is True
        mock_client.make_dir.assert_not_called()

    def test_ensure_parent_directory_error(self):
        """Test ensuring parent directory with error."""
        mock_client = Mock()
        mock_client.make_dir.side_effect = ops.pebble.PathError(
            "dir", "permission denied"
        )

        result = ensure_parent_directory(mock_client, "/path/to/file.txt")

        assert result is False

    def test_get_directory_size(self):
        """Test getting directory size."""
        mock_client = Mock()

        mock_file1 = Mock()
        mock_file1.name = "file1.txt"
        mock_file1.type = ops.pebble.FileType.FILE
        mock_file1.size = 100

        mock_file2 = Mock()
        mock_file2.name = "file2.txt"
        mock_file2.type = ops.pebble.FileType.FILE
        mock_file2.size = 200

        mock_subdir = Mock()
        mock_subdir.name = "subdir"
        mock_subdir.type = ops.pebble.FileType.DIRECTORY

        with patch("src.pebble_shell.utils.file_ops.list_directory_safe") as mock_list:
            # Set up different return values for different paths
            def list_side_effect(client, path):
                if path == "/test/dir":
                    return [mock_file1, mock_file2, mock_subdir]
                elif path == "/test/dir/subdir":
                    # Return one file in subdirectory with size 50
                    sub_file = Mock()
                    sub_file.name = "sub.txt"
                    sub_file.type = ops.pebble.FileType.FILE
                    sub_file.size = 50
                    return [sub_file]
                return []

            mock_list.side_effect = list_side_effect

            result = get_directory_size(mock_client, "/test/dir")

        assert result == 350  # 100 + 200 + 50 = 350

    def test_get_directory_size_error(self):
        """Test getting directory size with error."""
        mock_client = Mock()

        with patch("src.pebble_shell.utils.file_ops.list_directory_safe") as mock_list:
            mock_list.return_value = None

            result = get_directory_size(mock_client, "/test/dir")

        assert result == 0

    def test_count_files_recursive(self):
        """Test counting files recursively."""
        mock_client = Mock()

        mock_file1 = Mock()
        mock_file1.name = "file1.txt"
        mock_file1.type = ops.pebble.FileType.FILE

        mock_file2 = Mock()
        mock_file2.name = "file2.txt"
        mock_file2.type = ops.pebble.FileType.FILE

        mock_subdir = Mock()
        mock_subdir.name = "subdir"
        mock_subdir.type = ops.pebble.FileType.DIRECTORY

        with patch("src.pebble_shell.utils.file_ops.list_directory_safe") as mock_list:
            # Set up different return values for different paths
            def list_side_effect(client, path):
                if path == "/test/dir":
                    return [mock_file1, mock_file2, mock_subdir]
                elif path == "/test/dir/subdir":
                    # Return 3 files in subdirectory
                    sub_file1 = Mock()
                    sub_file1.name = "sub1.txt"
                    sub_file1.type = ops.pebble.FileType.FILE
                    sub_file2 = Mock()
                    sub_file2.name = "sub2.txt"
                    sub_file2.type = ops.pebble.FileType.FILE
                    sub_file3 = Mock()
                    sub_file3.name = "sub3.txt"
                    sub_file3.type = ops.pebble.FileType.FILE
                    return [sub_file1, sub_file2, sub_file3]
                return []

            mock_list.side_effect = list_side_effect

            result = count_files_recursive(mock_client, "/test/dir")

        assert result == 5  # 2 files in root + 3 files in subdir = 5 total

    def test_count_files_recursive_error(self):
        """Test counting files with error."""
        mock_client = Mock()

        with patch("src.pebble_shell.utils.file_ops.list_directory_safe") as mock_list:
            mock_list.return_value = None

            result = count_files_recursive(mock_client, "/test/dir")

        assert result == 0


class TestAdditionalCoverage:
    """Additional tests to improve coverage."""

    def test_safe_pull_file_api_error(self):
        """Test file pull with API error."""
        mock_client = Mock()
        mock_client.pull.side_effect = ops.pebble.APIError(
            {"error": "body"}, 400, "Bad Request", "Test error message"
        )

        result = safe_pull_file(mock_client, "/test/file.txt")

        assert result is None

    def test_safe_push_file_api_error(self):
        """Test file push with API error."""
        mock_client = Mock()
        mock_client.push.side_effect = ops.pebble.APIError(
            {"error": "body"}, 400, "Bad Request", "Test error message"
        )

        result = safe_push_file(mock_client, "/test/file.txt", "content")

        assert result is False

    def test_list_directory_safe_api_error(self):
        """Test directory listing with API error."""
        mock_client = Mock()
        mock_client.list_files.side_effect = ops.pebble.APIError(
            {"error": "body"}, 400, "Bad Request", "Test error message"
        )

        result = list_directory_safe(mock_client, "/test/dir")

        assert result is None

    def test_file_exists_special_case(self):
        """Test file_exists with special path case."""
        mock_client = Mock()

        # Test when path equals its parent (root case)
        mock_files = [Mock(name="test")]
        mock_client.list_files.return_value = mock_files

        result = file_exists(mock_client, "/")

        assert result is False  # Root itself won't have a name match

    def test_copy_file_with_progress_generic_exception(self):
        """Test copy file with generic exception."""
        from unittest.mock import Mock

        mock_client = Mock()
        mock_console = Mock()
        mock_client.pull.side_effect = Exception("Generic error")

        result = copy_file_with_progress(mock_client, mock_console, "/src", "/dst")

        assert result is False
        mock_console.print.assert_called_with("cannot copy file: Generic error")

    def test_copy_directory_recursive_generic_exception(self):
        """Test copy directory with generic exception."""
        mock_client = Mock()
        mock_console = Mock()
        mock_client.make_dir.side_effect = Exception("Generic error")

        result = copy_directory_recursive(mock_client, mock_console, "/src", "/dst")

        assert result is False
        mock_console.print.assert_called_with("cannot copy directory: Generic error")

    def test_remove_file_recursive_generic_exception(self):
        """Test remove file with generic exception."""
        mock_client = Mock()
        mock_console = Mock()

        with patch("src.pebble_shell.utils.file_ops.get_file_info") as mock_get_info:
            mock_get_info.side_effect = Exception("Generic error")

            result = remove_file_recursive(mock_client, mock_console, "/test")

            assert result is False
            mock_console.print.assert_called_with(
                "cannot remove '/test': Generic error"
            )

    def test_remove_file_recursive_force_mode(self):
        """Test remove file with force mode ignoring errors."""
        mock_client = Mock()
        mock_console = Mock()

        with patch("src.pebble_shell.utils.file_ops.get_file_info") as mock_get_info:
            mock_get_info.side_effect = Exception("Generic error")

            result = remove_file_recursive(
                mock_client, mock_console, "/test", force=True
            )

            assert result is True

    def test_move_file_with_progress_generic_exception(self):
        """Test move file with generic exception."""
        mock_client = Mock()
        mock_console = Mock()

        with patch("src.pebble_shell.utils.file_ops.get_file_info") as mock_get_info:
            mock_get_info.side_effect = Exception("Generic error")

            # The function doesn't catch generic exceptions, so it will raise
            try:
                move_file_with_progress(mock_client, mock_console, "/src", "/dst")
                raise AssertionError("Should have raised an exception")
            except Exception as e:
                assert str(e) == "Generic error"

    def test_ensure_parent_directory_root_edge_case(self):
        """Test ensure_parent_directory with root path edge case."""
        mock_client = Mock()

        # Test with path that has no parent
        result = ensure_parent_directory(mock_client, "/")

        assert result is True  # Should succeed for root path

    def test_get_directory_size_calculation_error(self):
        """Test get_directory_size with calculation error."""
        mock_client = Mock()

        with patch("src.pebble_shell.utils.file_ops.list_directory_safe") as mock_list:
            # Return files but cause an error during size calculation
            mock_file = Mock()
            mock_file.name = "test.txt"
            mock_file.type = ops.pebble.FileType.FILE
            mock_file.size = None  # This could cause issues
            mock_list.return_value = [mock_file]

            result = get_directory_size(mock_client, "/test")

            # Should handle None size gracefully
            assert result == 0
