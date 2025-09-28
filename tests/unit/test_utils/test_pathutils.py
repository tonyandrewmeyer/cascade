"""Tests for path utilities."""

from __future__ import annotations

from pebble_shell.utils.pathutils import resolve_path


class TestResolvePath:
    """Test resolve_path function."""

    def test_home_directory_tilde(self) -> None:
        """Test resolving ~ to home directory."""
        result = resolve_path("/current", "~", "/home/user")
        assert result == "/home/user"

    def test_home_directory_with_path(self) -> None:
        """Test resolving ~/path to home directory + path."""
        result = resolve_path("/current", "~/documents", "/home/user")
        assert result == "/home/user/documents"

    def test_home_directory_with_nested_path(self) -> None:
        """Test resolving ~/path/subpath to home directory."""
        result = resolve_path("/current", "~/documents/files", "/home/user")
        assert result == "/home/user/documents/files"

    def test_home_directory_tilde_only_variant(self) -> None:
        """Test resolving ~ when not followed by slash."""
        result = resolve_path("/current", "~user", "/home/testuser")
        assert result == "/home/testuser"

    def test_absolute_path(self) -> None:
        """Test resolving absolute path (should return as-is)."""
        result = resolve_path("/current", "/absolute/path", "/home/user")
        assert result == "/absolute/path"

    def test_absolute_path_complex(self) -> None:
        """Test resolving complex absolute path."""
        result = resolve_path("/current", "/usr/bin/python", "/home/user")
        assert result == "/usr/bin/python"

    def test_relative_path_from_regular_directory(self) -> None:
        """Test resolving relative path from regular directory."""
        result = resolve_path("/current/dir", "subdir", "/home/user")
        assert result == "/current/dir/subdir"

    def test_relative_path_from_root(self) -> None:
        """Test resolving relative path from root directory."""
        result = resolve_path("/", "etc", "/home/user")
        assert result == "/etc"

    def test_relative_path_from_root_nested(self) -> None:
        """Test resolving nested relative path from root directory."""
        result = resolve_path("/", "etc/nginx", "/home/user")
        assert result == "/etc/nginx"

    def test_relative_path_nested(self) -> None:
        """Test resolving nested relative path."""
        result = resolve_path("/var/log", "nginx/access.log", "/home/user")
        assert result == "/var/log/nginx/access.log"

    def test_dot_relative_path(self) -> None:
        """Test resolving . as relative path."""
        result = resolve_path("/current", ".", "/home/user")
        assert result == "/current/."

    def test_dotdot_relative_path(self) -> None:
        """Test resolving .. as relative path."""
        result = resolve_path("/current", "..", "/home/user")
        assert result == "/current/.."

    def test_empty_path(self) -> None:
        """Test resolving empty path."""
        result = resolve_path("/current", "", "/home/user")
        assert result == "/current/"

    def test_home_directory_edge_cases(self) -> None:
        """Test edge cases with home directory paths."""
        # Home directory path variations
        result1 = resolve_path("/current", "~", "/")
        assert result1 == "/"

        result2 = resolve_path("/current", "~/", "/home/user")
        assert result2 == "/home/user/"

        result3 = resolve_path("/current", "~text", "/home/user")
        assert result3 == "/home/user"

    def test_different_current_directories(self) -> None:
        """Test with various current directory formats."""
        # Different current directory formats
        result1 = resolve_path("/", "file.txt", "/home/user")
        assert result1 == "/file.txt"

        result2 = resolve_path("/usr", "bin", "/home/user")
        assert result2 == "/usr/bin"

        result3 = resolve_path("/usr/local/bin", "../lib", "/home/user")
        assert result3 == "/usr/local/bin/../lib"

    def test_special_home_directories(self) -> None:
        """Test with special home directory values."""
        # Special home directories
        result1 = resolve_path("/current", "~", "")
        assert result1 == ""

        result2 = resolve_path("/current", "~/test", "")
        assert result2 == "/test"
