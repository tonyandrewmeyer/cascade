"""Tests for glob utilities."""

from __future__ import annotations

from unittest.mock import Mock

import ops

from pebble_shell.utils.glob_utils import (
    expand_globs_in_tokens,
    expand_remote_globs,
    expand_remote_globs_recursive,
)


class TestExpandRemoteGlobs:
    """Test expand_remote_globs function."""

    def test_empty_pattern(self) -> None:
        """Test with empty pattern."""
        client = Mock()
        result = expand_remote_globs(client, "", "/")
        assert result == [""]

    def test_dot_pattern(self) -> None:
        """Test with dot pattern."""
        client = Mock()
        result = expand_remote_globs(client, ".", "/")
        assert result == ["."]

    def test_dotdot_pattern(self) -> None:
        """Test with dotdot pattern."""
        client = Mock()
        result = expand_remote_globs(client, "..", "/")
        assert result == [".."]

    def test_absolute_path_pattern(self) -> None:
        """Test with absolute path pattern."""
        client = Mock()
        file1 = Mock(spec=ops.pebble.FileInfo)
        file1.name = "test.txt"
        file2 = Mock(spec=ops.pebble.FileInfo)
        file2.name = "another.txt"
        client.list_files.return_value = [file1, file2]

        result = expand_remote_globs(client, "/usr/*.txt", "/")
        client.list_files.assert_called_once_with("/usr")
        assert result == ["/usr/another.txt", "/usr/test.txt"]

    def test_simple_wildcard_pattern(self) -> None:
        """Test with simple wildcard pattern."""
        client = Mock()
        file1 = Mock(spec=ops.pebble.FileInfo)
        file1.name = "test.txt"
        file2 = Mock(spec=ops.pebble.FileInfo)
        file2.name = "test.log"
        file3 = Mock(spec=ops.pebble.FileInfo)
        file3.name = "other.txt"
        client.list_files.return_value = [file1, file2, file3]

        result = expand_remote_globs(client, "*.txt", "/home")
        client.list_files.assert_called_once_with("/home")
        assert result == ["/home/other.txt", "/home/test.txt"]

    def test_question_mark_pattern(self) -> None:
        """Test with question mark pattern."""
        client = Mock()
        file1 = Mock(spec=ops.pebble.FileInfo)
        file1.name = "test1.txt"
        file2 = Mock(spec=ops.pebble.FileInfo)
        file2.name = "test2.txt"
        file3 = Mock(spec=ops.pebble.FileInfo)
        file3.name = "test10.txt"
        client.list_files.return_value = [file1, file2, file3]

        result = expand_remote_globs(client, "test?.txt", "/home")
        client.list_files.assert_called_once_with("/home")
        assert result == ["/home/test1.txt", "/home/test2.txt"]

    def test_subdirectory_pattern(self) -> None:
        """Test with subdirectory pattern."""
        client = Mock()
        file1 = Mock(spec=ops.pebble.FileInfo)
        file1.name = "file1.txt"
        file2 = Mock(spec=ops.pebble.FileInfo)
        file2.name = "file2.log"
        client.list_files.return_value = [file1, file2]

        result = expand_remote_globs(client, "subdir/*.txt", "/home")
        client.list_files.assert_called_once_with("/home/subdir")
        assert result == ["/home/subdir/file1.txt"]

    def test_path_error_handling(self) -> None:
        """Test handling of PathError."""
        client = Mock()
        client.list_files.side_effect = ops.pebble.PathError("path", "error")

        result = expand_remote_globs(client, "*.txt", "/nonexistent")
        assert result == ["*.txt"]

    def test_filters_dot_files(self) -> None:
        """Test that dot and dotdot files are filtered out."""
        client = Mock()
        file1 = Mock(spec=ops.pebble.FileInfo)
        file1.name = "."
        file2 = Mock(spec=ops.pebble.FileInfo)
        file2.name = ".."
        file3 = Mock(spec=ops.pebble.FileInfo)
        file3.name = "regular.txt"
        client.list_files.return_value = [file1, file2, file3]

        result = expand_remote_globs(client, "*", "/home")
        assert result == ["/home/regular.txt"]

    def test_root_base_path(self) -> None:
        """Test with root as base path."""
        client = Mock()
        file1 = Mock(spec=ops.pebble.FileInfo)
        file1.name = "test.txt"
        client.list_files.return_value = [file1]

        result = expand_remote_globs(client, "*.txt", "/")
        client.list_files.assert_called_once_with("/")
        assert result == ["/test.txt"]

    def test_bracket_pattern(self) -> None:
        """Test with bracket pattern."""
        client = Mock()
        file1 = Mock(spec=ops.pebble.FileInfo)
        file1.name = "file1.txt"
        file2 = Mock(spec=ops.pebble.FileInfo)
        file2.name = "file2.txt"
        file3 = Mock(spec=ops.pebble.FileInfo)
        file3.name = "file3.log"
        client.list_files.return_value = [file1, file2, file3]

        result = expand_remote_globs(client, "file[12].txt", "/home")
        assert result == ["/home/file1.txt", "/home/file2.txt"]


class TestExpandRemoteGlobsRecursive:
    """Test expand_remote_globs_recursive function."""

    def test_no_recursive_pattern(self) -> None:
        """Test without recursive pattern (should use regular expand)."""
        client = Mock()
        file1 = Mock(spec=ops.pebble.FileInfo)
        file1.name = "test.txt"
        client.list_files.return_value = [file1]

        result = expand_remote_globs_recursive(client, "*.txt", "/home")
        client.list_files.assert_called_once_with("/home")
        assert result == ["/home/test.txt"]

    def test_invalid_recursive_pattern(self) -> None:
        """Test with invalid recursive pattern (multiple **)."""
        client = Mock()
        result = expand_remote_globs_recursive(client, "**/**/**.txt", "/home")
        assert result == ["**/**/**.txt"]

    def test_recursive_file_search(self) -> None:
        """Test recursive file search."""
        client = Mock()

        # Mock directory structure:
        # /home/
        #   file1.txt
        #   subdir/ (directory)
        #     file2.txt
        #     nested/ (directory)
        #       file3.txt

        def mock_list_files(path: str):
            if path == "/home":
                file1 = Mock(spec=ops.pebble.FileInfo)
                file1.name = "file1.txt"
                file1.type = ops.pebble.FileType.FILE

                subdir = Mock(spec=ops.pebble.FileInfo)
                subdir.name = "subdir"
                subdir.type = ops.pebble.FileType.DIRECTORY

                return [file1, subdir]
            elif path == "/home/subdir":
                file2 = Mock(spec=ops.pebble.FileInfo)
                file2.name = "file2.txt"
                file2.type = ops.pebble.FileType.FILE

                nested = Mock(spec=ops.pebble.FileInfo)
                nested.name = "nested"
                nested.type = ops.pebble.FileType.DIRECTORY

                return [file2, nested]
            elif path == "/home/subdir/nested":
                file3 = Mock(spec=ops.pebble.FileInfo)
                file3.name = "file3.txt"
                file3.type = ops.pebble.FileType.FILE

                return [file3]
            else:
                raise ops.pebble.PathError(path, "not found")

        client.list_files.side_effect = mock_list_files

        result = expand_remote_globs_recursive(client, "**/*.txt", "/home")
        expected = [
            "/home/file1.txt",
            "/home/subdir/file2.txt",
            "/home/subdir/nested/file3.txt",
        ]
        assert result == expected

    def test_recursive_directory_search(self) -> None:
        """Test recursive directory search without file pattern."""
        client = Mock()

        def mock_list_files(path: str):
            if path == "/home":
                subdir1 = Mock(spec=ops.pebble.FileInfo)
                subdir1.name = "subdir1"
                subdir1.type = ops.pebble.FileType.DIRECTORY

                subdir2 = Mock(spec=ops.pebble.FileInfo)
                subdir2.name = "subdir2"
                subdir2.type = ops.pebble.FileType.DIRECTORY

                return [subdir1, subdir2]
            elif path == "/home/subdir1":
                nested = Mock(spec=ops.pebble.FileInfo)
                nested.name = "nested"
                nested.type = ops.pebble.FileType.DIRECTORY

                return [nested]
            elif path == "/home/subdir1/nested" or path == "/home/subdir2":
                return []
            else:
                raise ops.pebble.PathError(path, "not found")

        client.list_files.side_effect = mock_list_files

        result = expand_remote_globs_recursive(client, "**", "/home")
        expected = ["/home/subdir1", "/home/subdir1/nested", "/home/subdir2"]
        assert result == expected

    def test_recursive_path_error(self) -> None:
        """Test handling of PathError in recursive search."""
        client = Mock()
        client.list_files.side_effect = ops.pebble.PathError("/path", "error")

        result = expand_remote_globs_recursive(client, "**/*.txt", "/home")
        assert result == []

    def test_recursive_filters_dot_files(self) -> None:
        """Test that recursive search filters dot and dotdot."""
        client = Mock()

        def mock_list_files(path: str):
            if path == "/home":
                dot = Mock(spec=ops.pebble.FileInfo)
                dot.name = "."
                dot.type = ops.pebble.FileType.DIRECTORY

                dotdot = Mock(spec=ops.pebble.FileInfo)
                dotdot.name = ".."
                dotdot.type = ops.pebble.FileType.DIRECTORY

                file1 = Mock(spec=ops.pebble.FileInfo)
                file1.name = "file.txt"
                file1.type = ops.pebble.FileType.FILE

                return [dot, dotdot, file1]
            else:
                raise ops.pebble.PathError(path, "not found")

        client.list_files.side_effect = mock_list_files

        result = expand_remote_globs_recursive(client, "**/*.txt", "/home")
        assert result == ["/home/file.txt"]


class TestExpandGlobsInTokens:
    """Test expand_globs_in_tokens function."""

    def test_no_glob_patterns(self) -> None:
        """Test with tokens containing no glob patterns."""
        client = Mock()
        tokens = ["ls", "-l", "file.txt"]
        result = expand_globs_in_tokens(client, tokens, "/home")
        assert result == ["ls", "-l", "file.txt"]

    def test_glob_pattern_with_matches(self) -> None:
        """Test with glob pattern that has matches."""
        client = Mock()
        file1 = Mock(spec=ops.pebble.FileInfo)
        file1.name = "file1.txt"
        file2 = Mock(spec=ops.pebble.FileInfo)
        file2.name = "file2.txt"
        client.list_files.return_value = [file1, file2]

        tokens = ["cat", "*.txt"]
        result = expand_globs_in_tokens(client, tokens, "/home")
        assert result == ["cat", "/home/file1.txt", "/home/file2.txt"]

    def test_glob_pattern_no_matches(self) -> None:
        """Test with glob pattern that has no matches."""
        client = Mock()
        client.list_files.return_value = []

        tokens = ["cat", "*.xyz"]
        result = expand_globs_in_tokens(client, tokens, "/home")
        assert result == ["cat", "*.xyz"]  # Keep original token

    def test_mixed_tokens(self) -> None:
        """Test with mix of glob and non-glob tokens."""
        client = Mock()
        file1 = Mock(spec=ops.pebble.FileInfo)
        file1.name = "data.log"
        client.list_files.return_value = [file1]

        tokens = ["grep", "error", "*.log", "-n"]
        result = expand_globs_in_tokens(client, tokens, "/var/log")
        assert result == ["grep", "error", "/var/log/data.log", "-n"]

    def test_option_flags_not_expanded(self) -> None:
        """Test that option flags starting with - are not expanded."""
        client = Mock()
        file1 = Mock(spec=ops.pebble.FileInfo)
        file1.name = "all"
        client.list_files.return_value = [file1]

        tokens = ["ls", "-*", "*.txt"]  # -* should not be expanded
        result = expand_globs_in_tokens(client, tokens, "/home")
        # Only *.txt should be attempted for expansion
        assert result == ["ls", "-*", "*.txt"]  # No matches for *.txt

    def test_question_mark_expansion(self) -> None:
        """Test expansion with question mark patterns."""
        client = Mock()
        file1 = Mock(spec=ops.pebble.FileInfo)
        file1.name = "file1.txt"
        file2 = Mock(spec=ops.pebble.FileInfo)
        file2.name = "file2.txt"
        file3 = Mock(spec=ops.pebble.FileInfo)
        file3.name = "file10.txt"
        client.list_files.return_value = [file1, file2, file3]

        tokens = ["file?.txt"]
        result = expand_globs_in_tokens(client, tokens, "/")
        assert result == ["/file1.txt", "/file2.txt"]

    def test_bracket_expansion(self) -> None:
        """Test expansion with bracket patterns."""
        client = Mock()
        file1 = Mock(spec=ops.pebble.FileInfo)
        file1.name = "data1.txt"
        file2 = Mock(spec=ops.pebble.FileInfo)
        file2.name = "data2.txt"
        file3 = Mock(spec=ops.pebble.FileInfo)
        file3.name = "data9.txt"
        client.list_files.return_value = [file1, file2, file3]

        tokens = ["data[12].txt"]
        result = expand_globs_in_tokens(client, tokens, "/")
        assert result == ["/data1.txt", "/data2.txt"]

    def test_multiple_glob_tokens(self) -> None:
        """Test with multiple glob patterns in token list."""
        client = Mock()

        def mock_list_files(path: str):
            if "*.txt" in path:  # This won't actually be called this way
                txt_file = Mock(spec=ops.pebble.FileInfo)
                txt_file.name = "doc.txt"
                return [txt_file]
            else:  # Called with the directory path
                txt_file = Mock(spec=ops.pebble.FileInfo)
                txt_file.name = "doc.txt"
                log_file = Mock(spec=ops.pebble.FileInfo)
                log_file.name = "app.log"
                return [txt_file, log_file]

        client.list_files.side_effect = mock_list_files

        tokens = ["cp", "*.txt", "*.log", "/backup"]
        result = expand_globs_in_tokens(client, tokens, "/data")
        # Both patterns should expand
        assert "cp" in result
        assert "/backup" in result
        assert "/data/doc.txt" in result
        assert "/data/app.log" in result
