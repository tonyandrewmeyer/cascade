"""Tests for formatting utilities."""

from __future__ import annotations

import datetime
from unittest.mock import Mock

import ops

from pebble_shell.utils.formatting import (
    _octal_permissions,
    format_bytes,
    format_error,
    format_file_info,
    format_relative_time,
    format_stat_info,
    format_time,
)


class TestOctalPermissions:
    """Test _octal_permissions function."""

    def test_full_permissions(self) -> None:
        """Test full permissions (777)."""
        result = _octal_permissions(0o777)
        assert result == "rwxrwxrwx"

    def test_no_permissions(self) -> None:
        """Test no permissions (000)."""
        result = _octal_permissions(0o000)
        assert result == "---------"

    def test_owner_only_permissions(self) -> None:
        """Test owner-only permissions (700)."""
        result = _octal_permissions(0o700)
        assert result == "rwx------"

    def test_read_only_permissions(self) -> None:
        """Test read-only permissions (444)."""
        result = _octal_permissions(0o444)
        assert result == "r--r--r--"

    def test_typical_file_permissions(self) -> None:
        """Test typical file permissions (644)."""
        result = _octal_permissions(0o644)
        assert result == "rw-r--r--"

    def test_typical_executable_permissions(self) -> None:
        """Test typical executable permissions (755)."""
        result = _octal_permissions(0o755)
        assert result == "rwxr-xr-x"


class TestFormatFileInfo:
    """Test format_file_info function."""

    def test_format_file(self) -> None:
        """Test formatting regular file info."""
        file_info = Mock(spec=ops.pebble.FileInfo)
        file_info.type = ops.pebble.FileType.FILE
        file_info.permissions = 0o644
        file_info.size = 1024
        file_info.last_modified = datetime.datetime(2023, 6, 15, 10, 30, 45)
        file_info.user_id = 1000
        file_info.group_id = 1000
        file_info.name = "test.txt"

        result = format_file_info(file_info)
        expected = "-rw-r--r-- 1000     1000         1024 Jun 15 10:30 test.txt"
        assert result == expected

    def test_format_directory(self) -> None:
        """Test formatting directory info."""
        file_info = Mock(spec=ops.pebble.FileInfo)
        file_info.type = ops.pebble.FileType.DIRECTORY
        file_info.permissions = 0o755
        file_info.size = 4096
        file_info.last_modified = datetime.datetime(2023, 6, 15, 10, 30, 45)
        file_info.user_id = 0
        file_info.group_id = 0
        file_info.name = "testdir"

        result = format_file_info(file_info)
        expected = "drwxr-xr-x 0        0            4096 Jun 15 10:30 testdir"
        assert result == expected

    def test_format_file_none_values(self) -> None:
        """Test formatting file info with None values."""
        file_info = Mock(spec=ops.pebble.FileInfo)
        file_info.type = ops.pebble.FileType.FILE
        file_info.permissions = 0o644
        file_info.size = None
        file_info.last_modified = None
        file_info.user_id = None
        file_info.group_id = None
        file_info.name = "test.txt"

        result = format_file_info(file_info)
        expected = "-rw-r--r-- 0        0               0 unknown test.txt"
        assert result == expected


class TestFormatStatInfo:
    """Test format_stat_info function."""

    def test_format_stat_complete(self) -> None:
        """Test formatting complete stat info."""
        file_info = Mock(spec=ops.pebble.FileInfo)
        file_info.type = ops.pebble.FileType.FILE
        file_info.size = 1024
        file_info.user_id = 1000
        file_info.group_id = 1000
        file_info.last_modified = datetime.datetime(2023, 6, 15, 10, 30, 45)

        result = format_stat_info(file_info, "/path/to/file.txt")
        expected_lines = [
            "File: /path/to/file.txt",
            "Type: FileType.FILE",
            "Size: 1024 bytes",
            "Owner: 1000",
            "Group: 1000",
            "Last Modified: 2023-06-15 10:30:45",
        ]
        assert result == "\n".join(expected_lines)

    def test_format_stat_minimal(self) -> None:
        """Test formatting stat info with minimal data."""
        file_info = Mock(spec=ops.pebble.FileInfo)
        file_info.type = ops.pebble.FileType.FILE
        file_info.size = None
        file_info.user_id = None
        file_info.group_id = None
        file_info.last_modified = None

        result = format_stat_info(file_info, "/path/to/file.txt")
        expected_lines = [
            "File: /path/to/file.txt",
            "Type: FileType.FILE",
            "Size: unknown",
        ]
        assert result == "\n".join(expected_lines)


class TestFormatError:
    """Test format_error function."""

    def test_format_error(self) -> None:
        """Test formatting error message."""
        result = format_error("Something went wrong")
        assert result == "Error: Something went wrong"

    def test_format_empty_error(self) -> None:
        """Test formatting empty error message."""
        result = format_error("")
        assert result == "Error: "


class TestFormatBytes:
    """Test format_bytes function."""

    def test_bytes(self) -> None:
        """Test formatting bytes."""
        assert format_bytes(512) == "512.0B"
        assert format_bytes(1023) == "1023.0B"

    def test_kilobytes(self) -> None:
        """Test formatting kilobytes."""
        assert format_bytes(1024) == "1024.0KB"
        assert format_bytes(2048) == "2048.0KB"

    def test_megabytes(self) -> None:
        """Test formatting megabytes."""
        assert format_bytes(1024 * 1024) == "1048576.0MB"
        assert format_bytes(2 * 1024 * 1024) == "2097152.0MB"

    def test_gigabytes(self) -> None:
        """Test formatting gigabytes."""
        assert format_bytes(1024 * 1024 * 1024) == "1073741824.0GB"

    def test_terabytes(self) -> None:
        """Test formatting terabytes."""
        assert format_bytes(1024 * 1024 * 1024 * 1024) == "1099511627776.0TB"

    def test_petabytes(self) -> None:
        """Test formatting petabytes."""
        assert format_bytes(1024 * 1024 * 1024 * 1024 * 1024) == "1.0PB"

    def test_zero_bytes(self) -> None:
        """Test formatting zero bytes."""
        assert format_bytes(0) == "0.0B"


class TestFormatTime:
    """Test format_time function."""

    def test_seconds_only(self) -> None:
        """Test formatting seconds only."""
        assert format_time(30) == "00:00:30"

    def test_minutes_and_seconds(self) -> None:
        """Test formatting minutes and seconds."""
        assert format_time(90) == "00:01:30"

    def test_hours_minutes_seconds(self) -> None:
        """Test formatting hours, minutes, and seconds."""
        assert format_time(3661) == "01:01:01"

    def test_zero_time(self) -> None:
        """Test formatting zero time."""
        assert format_time(0) == "00:00:00"

    def test_large_time(self) -> None:
        """Test formatting large time values."""
        assert format_time(86400) == "24:00:00"  # 24 hours


class TestFormatRelativeTime:
    """Test format_relative_time function."""

    def test_none_datetime(self) -> None:
        """Test formatting None datetime."""
        assert format_relative_time(None) == "unknown"  # type: ignore

    def test_seconds_ago(self) -> None:
        """Test formatting seconds ago."""
        now = datetime.datetime.now(datetime.timezone.utc)
        past = now - datetime.timedelta(seconds=30)
        result = format_relative_time(past)
        assert "second" in result and "ago" in result

    def test_one_second_ago(self) -> None:
        """Test formatting one second ago (no plural)."""
        now = datetime.datetime.now(datetime.timezone.utc)
        past = now - datetime.timedelta(seconds=1)
        result = format_relative_time(past)
        assert result == "1 second ago"

    def test_multiple_seconds_ago(self) -> None:
        """Test formatting multiple seconds ago (plural)."""
        now = datetime.datetime.now(datetime.timezone.utc)
        past = now - datetime.timedelta(seconds=30)
        result = format_relative_time(past)
        assert result == "30 seconds ago"

    def test_minutes_ago(self) -> None:
        """Test formatting minutes ago."""
        now = datetime.datetime.now(datetime.timezone.utc)
        past = now - datetime.timedelta(minutes=5)
        result = format_relative_time(past)
        assert result == "5 minutes ago"

    def test_one_minute_ago(self) -> None:
        """Test formatting one minute ago (no plural)."""
        now = datetime.datetime.now(datetime.timezone.utc)
        past = now - datetime.timedelta(minutes=1)
        result = format_relative_time(past)
        assert result == "1 minute ago"

    def test_hours_ago(self) -> None:
        """Test formatting hours ago."""
        now = datetime.datetime.now(datetime.timezone.utc)
        past = now - datetime.timedelta(hours=3)
        result = format_relative_time(past)
        assert result == "3 hours ago"

    def test_one_hour_ago(self) -> None:
        """Test formatting one hour ago (no plural)."""
        now = datetime.datetime.now(datetime.timezone.utc)
        past = now - datetime.timedelta(hours=1)
        result = format_relative_time(past)
        assert result == "1 hour ago"

    def test_days_ago(self) -> None:
        """Test formatting days ago."""
        now = datetime.datetime.now(datetime.timezone.utc)
        past = now - datetime.timedelta(days=5)
        result = format_relative_time(past)
        assert result == "5 days ago"

    def test_one_day_ago(self) -> None:
        """Test formatting one day ago (no plural)."""
        now = datetime.datetime.now(datetime.timezone.utc)
        past = now - datetime.timedelta(days=1)
        result = format_relative_time(past)
        assert result == "1 day ago"

    def test_months_ago(self) -> None:
        """Test formatting months ago."""
        now = datetime.datetime.now(datetime.timezone.utc)
        past = now - datetime.timedelta(days=60)  # ~2 months
        result = format_relative_time(past)
        assert result == "2 months ago"

    def test_one_month_ago(self) -> None:
        """Test formatting one month ago (no plural)."""
        now = datetime.datetime.now(datetime.timezone.utc)
        past = now - datetime.timedelta(days=35)  # ~1 month
        result = format_relative_time(past)
        assert result == "1 month ago"

    def test_years_ago(self) -> None:
        """Test formatting years ago."""
        now = datetime.datetime.now(datetime.timezone.utc)
        past = now - datetime.timedelta(days=400)  # ~1+ years
        result = format_relative_time(past)
        assert result == "1 year ago"

    def test_multiple_years_ago(self) -> None:
        """Test formatting multiple years ago."""
        now = datetime.datetime.now(datetime.timezone.utc)
        past = now - datetime.timedelta(days=800)  # ~2+ years
        result = format_relative_time(past)
        assert result == "2 years ago"
