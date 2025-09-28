"""Tests for system commands."""

from datetime import datetime
from io import StringIO
from unittest.mock import MagicMock, Mock, patch

import ops.pebble
import pytest
from ops.pebble import FileInfo, FileType
from rich.console import Console

from pebble_shell.commands.system import (
    CpuinfoCommand,
    DashboardCommand,
    DiskUsageCommand,
    DmesgCommand,
    DuCommand,
    FdinfoCommand,
    FreeCommand,
    IostatCommand,
    LastCommand,
    LoadavgCommand,
    MeminfoCommand,
    MountCommand,
    PgrepCommand,
    ProcessCommand,
    PstreeCommand,
    SyslogCommand,
    UptimeCommand,
    VmstatCommand,
    WCommand,
    WhoCommand,
)


class TestDiskUsageCommand:
    """Test cases for DiskUsageCommand."""

    @pytest.fixture
    def command(self):
        """Create DiskUsageCommand instance."""
        mock_shell = Mock()
        string_io = StringIO()
        mock_shell.console = Console(file=string_io)
        command = DiskUsageCommand(mock_shell)
        command._test_output = string_io  # type: ignore[attr-defined]
        return command

    @pytest.fixture
    def mock_client(self):
        """Create mock client."""
        mock_client = Mock()

        def mock_pull_side_effect(path):
            """Mock pull method for different file paths."""
            mock_context = MagicMock()
            mock_file = Mock()

            if path == "/proc/mounts":
                mounts_content = """
/dev/sda1 / ext4 rw,relatime 0 0
/dev/sda2 /home ext4 rw,relatime 0 0
tmpfs /tmp tmpfs rw,nosuid,nodev 0 0
proc /proc proc rw,nosuid,nodev,noexec,relatime 0 0
                """.strip()
                mock_file.read.return_value = mounts_content
            else:
                mock_file.read.return_value = ""

            mock_context.__enter__.return_value = mock_file
            mock_context.__exit__.return_value = None
            return mock_context

        mock_client.pull.side_effect = mock_pull_side_effect
        return mock_client

    def test_execute_success(self, command, mock_client):
        """Test df command success."""
        result = command.execute(mock_client, [])

        assert result == 0
        output = command._test_output.getvalue()
        assert "Device" in output
        assert "Mount Point" in output
        assert "Type" in output
        assert "/dev/sda1" in output
        assert "ext4" in output
        assert "tmpfs" in output

    def test_execute_error(self, command, mock_client):
        """Test df command with error."""
        mock_client.pull.side_effect = Exception("Permission denied")

        try:
            command.execute(mock_client, [])
            pytest.fail("Expected exception")
        except Exception as e:
            assert "Permission denied" in str(e)

    def test_execute_empty_mounts(self, command, mock_client):
        """Test df command with empty mounts file."""

        def mock_pull_side_effect(path):
            """Mock pull method for different file paths."""
            mock_context = MagicMock()
            mock_file = Mock()

            if path == "/proc/mounts":
                mock_file.read.return_value = ""
            else:
                mock_file.read.return_value = ""

            mock_context.__enter__.return_value = mock_file
            mock_context.__exit__.return_value = None
            return mock_context

        mock_client.pull.side_effect = mock_pull_side_effect

        result = command.execute(mock_client, [])

        assert result == 0
        output = command._test_output.getvalue()
        assert "Device" in output
        assert "Mount Point" in output
        assert "Type" in output


class TestProcessCommand:
    """Test cases for ProcessCommand."""

    @pytest.fixture
    def command(self):
        """Create ProcessCommand instance."""
        mock_shell = Mock()
        string_io = StringIO()
        mock_shell.console = Console(file=string_io)
        command = ProcessCommand(mock_shell)
        command._test_output = string_io  # type: ignore[attr-defined]
        return command

    @pytest.fixture
    def mock_client(self):
        """Create mock client."""
        mock_client = Mock()

        # Mock /proc directory listing with proper FileInfo objects
        proc_files = [
            FileInfo(
                path="/proc/1",
                name="1",
                type=FileType.DIRECTORY,
                size=0,
                permissions=755,
                last_modified=datetime.now(),
                user_id=0,
                user="root",
                group_id=0,
                group="root",
            ),
            FileInfo(
                path="/proc/2",
                name="2",
                type=FileType.DIRECTORY,
                size=0,
                permissions=755,
                last_modified=datetime.now(),
                user_id=0,
                user="root",
                group_id=0,
                group="root",
            ),
            FileInfo(
                path="/proc/123",
                name="123",
                type=FileType.DIRECTORY,
                size=0,
                permissions=755,
                last_modified=datetime.now(),
                user_id=0,
                user="root",
                group_id=0,
                group="root",
            ),
            FileInfo(
                path="/proc/self",
                name="self",
                type=FileType.DIRECTORY,
                size=0,
                permissions=755,
                last_modified=datetime.now(),
                user_id=0,
                user="root",
                group_id=0,
                group="root",
            ),
            FileInfo(
                path="/proc/meminfo",
                name="meminfo",
                type=FileType.FILE,
                size=1024,
                permissions=644,
                last_modified=datetime.now(),
                user_id=0,
                user="root",
                group_id=0,
                group="root",
            ),
        ]

        mock_client.list_files.return_value = proc_files

        def mock_pull_side_effect(path):
            """Mock pull method for different file paths."""
            mock_context = MagicMock()
            mock_file = Mock()

            if path == "/proc/1/cmdline":
                mock_file.read.return_value = "/sbin/init\x00"
            elif path == "/proc/2/cmdline":
                mock_file.read.return_value = ""  # Empty cmdline triggers comm read
            elif path == "/proc/2/comm":
                mock_file.read.return_value = "kthreadd\n"
            elif path == "/proc/123/cmdline":
                mock_file.read.return_value = "python3\x00-c\x00print('hello')\x00"
            else:
                # For any unhandled paths, raise PathError to simulate file not found
                raise ops.pebble.PathError("kind", "File not found")

            mock_context.__enter__.return_value = mock_file
            mock_context.__exit__.return_value = None
            return mock_context

            mock_context.__enter__.return_value = mock_file
            mock_context.__exit__.return_value = None
            return mock_context

        mock_client.pull.side_effect = mock_pull_side_effect
        return mock_client

    def test_execute_success(self, command, mock_client):
        """Test ps command success."""
        result = command.execute(mock_client, [])

        assert result == 0
        output = command._test_output.getvalue()
        assert "PID" in output
        assert "CMD" in output
        assert "/sbin/init" in output
        assert "[kthreadd]" in output
        assert "python3 -c print('hello')" in output

    def test_execute_no_processes(self, command, mock_client):
        """Test ps command with no processes."""
        mock_client.list_files.return_value = []
        result = command.execute(mock_client, [])

        assert result == 1  # Should return error code when no processes found
        output = command._test_output.getvalue()
        assert "No process information found" in output

    def test_execute_error(self, command, mock_client):
        """Test ps command with error."""
        mock_client.list_files.side_effect = Exception("Permission denied")

        try:
            command.execute(mock_client, [])
            pytest.fail("Expected exception")
        except Exception as e:
            assert "Permission denied" in str(e)

    def test_execute_long_cmdline(self, command, mock_client):
        """Test ps command with long command line."""
        # Mock single process with very long cmdline
        proc_files = [
            FileInfo(
                path="/proc/999",
                name="999",
                type=FileType.DIRECTORY,
                size=0,
                permissions=755,
                last_modified=datetime.now(),
                user_id=0,
                user="root",
                group_id=0,
                group="root",
            )
        ]
        mock_client.list_files.return_value = proc_files

        def mock_pull_side_effect(path):
            """Mock pull method for different file paths."""
            mock_context = MagicMock()
            mock_file = Mock()
            if path == "/proc/999/cmdline":
                # Very long command line
                long_cmd = "very_long_command_name_that_exceeds_fifty_characters_and_should_be_truncated"
                mock_file.read.return_value = long_cmd
            else:
                mock_file.read.return_value = ""
            mock_context.__enter__.return_value = mock_file
            mock_context.__exit__.return_value = None
            return mock_context

        mock_client.pull.side_effect = mock_pull_side_effect
        result = command.execute(mock_client, [])

        assert result == 0
        output = command._test_output.getvalue()
        # Should be truncated with "..." (cmdline[:47] + "...")
        assert "very_long_command_name_that_exceeds_fifty_chara..." in output

    def test_execute_process_read_error(self, command, mock_client):
        """Test ps command with process read errors."""
        # Mock process that can't be read
        proc_files = [
            FileInfo(
                path="/proc/1",
                name="1",
                type=FileType.DIRECTORY,
                size=0,
                permissions=755,
                last_modified=datetime.now(),
                user_id=0,
                user="root",
                group_id=0,
                group="root",
            ),
            FileInfo(
                path="/proc/2",
                name="2",
                type=FileType.DIRECTORY,
                size=0,
                permissions=755,
                last_modified=datetime.now(),
                user_id=0,
                user="root",
                group_id=0,
                group="root",
            ),
        ]
        mock_client.list_files.return_value = proc_files

        def mock_pull_side_effect(path):
            """Mock pull method for different file paths."""
            if path == "/proc/1/cmdline":
                mock_context = MagicMock()
                mock_file = Mock()
                mock_file.read.return_value = "/sbin/init\x00"
                mock_context.__enter__.return_value = mock_file
                mock_context.__exit__.return_value = None
                return mock_context
            # Process 2 can't be read - raise PathError to skip it
            raise ops.pebble.PathError("kind", "Permission denied")

        mock_client.pull.side_effect = mock_pull_side_effect
        result = command.execute(mock_client, [])

        assert result == 0
        output = command._test_output.getvalue()
        # Should show process 1 but skip process 2
        assert "/sbin/init" in output
        # Process 2 should be skipped silently


class TestDuCommand:
    """Test cases for DuCommand."""

    @pytest.fixture
    def command(self):
        """Create a DuCommand for testing."""
        mock_shell = Mock()
        # Create a StringIO console for capturing output
        string_io = StringIO()
        mock_shell.console = Console(file=string_io)
        mock_shell.current_directory = "/test"
        mock_shell.home_dir = "/home/test"
        command = DuCommand(mock_shell)
        # Store the StringIO for output checking
        command._test_output = string_io  # type: ignore[attr-defined]
        return command

    @pytest.fixture
    def mock_client(self):
        """Create a mock client for testing."""
        return MagicMock()

    def test_execute_default_path(self, command, mock_client):
        """Test executing du command with default path."""
        # Mock the list_files response for the current directory and its parent
        mock_current_dir_info = Mock()
        mock_current_dir_info.name = "."
        mock_current_dir_info.type = ops.pebble.FileType.DIRECTORY
        mock_current_dir_info.size = None

        # Set up list_files to return the current directory file info
        def mock_list_files(path):
            if path == "/test":  # Parent directory of current directory
                return [mock_current_dir_info]
            if (
                path == "/test/."
            ):  # The current directory itself (when calculating size)
                return []  # Empty directory for simplicity
            return []

        mock_client.list_files.side_effect = mock_list_files

        # The command should run without errors
        result = command.execute(mock_client, [])

        # Verify basic functionality
        assert result == 0  # Should return success
        mock_client.list_files.assert_called()  # Should have called list_files

        # Check that something was printed to console
        output = command._test_output.getvalue()
        assert len(output) > 0  # Should have some output

    def test_execute_with_path(self, command, mock_client):
        """Test executing du command with specified path."""
        # Mock list_files for directory size calculation
        mock_client.list_files.return_value = []

        result = command.execute(mock_client, ["/var"])

        # Should call list_files to calculate size
        mock_client.list_files.assert_called()
        assert result == 0

        output = command._test_output.getvalue()
        assert len(output) > 0  # Should have some output

    def test_execute_error(self, command, mock_client):
        """Test handling execution errors."""
        mock_client.list_files.side_effect = Exception("Permission denied")

        # Since DuCommand doesn't handle list_files exceptions,
        # it will propagate the exception
        with pytest.raises(Exception, match="Permission denied"):
            command.execute(mock_client, ["/restricted"])


class TestUptimeCommand:
    """Test cases for UptimeCommand."""

    @pytest.fixture
    def command(self):
        """Create an UptimeCommand for testing."""
        mock_shell = Mock()
        string_io = StringIO()
        mock_shell.console = Console(file=string_io)
        command = UptimeCommand(mock_shell)
        command._test_output = string_io  # type: ignore[attr-defined]
        return command

    @pytest.fixture
    def mock_client(self):
        """Create a mock client for testing."""
        mock_client = Mock()

        def mock_pull_side_effect(path):
            """Mock pull method for different file paths."""
            mock_context = MagicMock()
            mock_file = Mock()

            if path == "/proc/driver/rtc":
                mock_file.read.return_value = "rtc_time\t: 12:34:56\n"
            elif path == "/proc/uptime":
                mock_file.read.return_value = "3600.50 7200.25\n"
            elif path == "/proc/loadavg":
                mock_file.read.return_value = "0.50 0.25 0.10 1/234 12345\n"
            else:
                mock_file.read.return_value = ""

            mock_context.__enter__.return_value = mock_file
            mock_context.__exit__.return_value = None
            return mock_context

        mock_client.pull.side_effect = mock_pull_side_effect
        return mock_client

    def test_execute_success(self, command, mock_client):
        """Test executing uptime command successfully."""
        result = command.execute(mock_client, [])

        assert result == 0
        output = command._test_output.getvalue()
        assert "12:34:56" in output
        assert "load average" in output
        assert "0.50" in output

    def test_execute_error(self, command, mock_client):
        """Test handling execution errors."""
        mock_client.pull.side_effect = Exception("File not found")

        # Command should fail when it can't read required files
        with pytest.raises(Exception, match="File not found"):
            command.execute(mock_client, [])


class TestWhoCommand:
    """Test cases for WhoCommand."""

    @pytest.fixture
    def command(self):
        """Create a WhoCommand for testing."""
        mock_shell = Mock()
        string_io = StringIO()
        mock_shell.console = Console(file=string_io)
        command = WhoCommand(mock_shell)
        command._test_output = string_io  # type: ignore[attr-defined]
        return command

    @pytest.fixture
    def mock_client(self):
        """Create a mock client for testing."""
        mock_client = Mock()

        # Mock /proc directory listing
        proc_files = [
            FileInfo(
                path="/proc/1",
                name="1",
                type=FileType.DIRECTORY,
                size=0,
                permissions=755,
                last_modified=datetime.now(),
                user_id=0,
                user="root",
                group_id=0,
                group="root",
            ),
            FileInfo(
                path="/proc/1234",
                name="1234",
                type=FileType.DIRECTORY,
                size=0,
                permissions=755,
                last_modified=datetime.now(),
                user_id=0,
                user="root",
                group_id=0,
                group="root",
            ),
        ]
        mock_client.list_files.return_value = proc_files

        def mock_pull_side_effect(path):
            """Mock pull method for different file paths."""
            mock_context = MagicMock()
            mock_file = Mock()

            if path == "/proc/1/cmdline":
                mock_file.read.return_value = "/sbin/init"
            elif path == "/proc/1/status":
                mock_file.read.return_value = "Name:\tinit\nUid:\t0\t0\t0\t0\n"
            elif path == "/proc/1234/cmdline":
                mock_file.read.return_value = "bash"
            elif path == "/proc/1234/status":
                mock_file.read.return_value = (
                    "Name:\tbash\nUid:\t1000\t1000\t1000\t1000\n"
                )
            elif path == "/etc/passwd":
                mock_file.read.return_value = "root:x:0:0:root:/root:/bin/bash\nuser:x:1000:1000:User:/home/user:/bin/bash\n"
            else:
                mock_file.read.return_value = ""

            mock_context.__enter__.return_value = mock_file
            mock_context.__exit__.return_value = None
            return mock_context

        mock_client.pull.side_effect = mock_pull_side_effect
        return mock_client

    def test_execute_success(self, command, mock_client):
        """Test executing who command successfully."""
        result = command.execute(mock_client, [])

        assert result == 0
        output = command._test_output.getvalue()
        assert "USER" in output  # Should show table headers

    def test_execute_error(self, command, mock_client):
        """Test handling execution errors."""
        mock_client.list_files.side_effect = Exception("Permission denied")

        with pytest.raises(Exception, match="Permission denied"):
            command.execute(mock_client, [])


class TestFreeCommand:
    """Test cases for FreeCommand."""

    @pytest.fixture
    def command(self):
        """Create a FreeCommand for testing."""
        mock_shell = Mock()
        string_io = StringIO()
        mock_shell.console = Console(file=string_io)
        command = FreeCommand(mock_shell)
        command._test_output = string_io  # type: ignore[attr-defined]
        return command

    @pytest.fixture
    def mock_client(self):
        """Create a mock client for testing."""
        mock_client = Mock()

        def mock_pull_side_effect(path):
            """Mock pull method for different file paths."""
            mock_context = MagicMock()
            mock_file = Mock()

            if path == "/proc/meminfo":
                mock_file.read.return_value = """MemTotal:        8000000 kB
MemFree:         4000000 kB
MemAvailable:    5800000 kB
Buffers:          200000 kB
Cached:          1800000 kB
SwapTotal:       2000000 kB
SwapFree:        1500000 kB
"""
            else:
                mock_file.read.return_value = ""

            mock_context.__enter__.return_value = mock_file
            mock_context.__exit__.return_value = None
            return mock_context

        mock_client.pull.side_effect = mock_pull_side_effect
        return mock_client

    def test_execute_success(self, command, mock_client):
        """Test executing free command successfully."""
        result = command.execute(mock_client, [])

        assert result == 0
        output = command._test_output.getvalue()
        assert len(output) > 0  # Should have some output

    def test_execute_error(self, command, mock_client):
        """Test handling execution errors."""
        mock_client.pull.side_effect = Exception("File not found")

        with pytest.raises(Exception, match="File not found"):
            command.execute(mock_client, [])


class TestLoadavgCommand:
    """Test cases for LoadavgCommand."""

    @pytest.fixture
    def command(self):
        """Create a LoadavgCommand for testing."""
        mock_shell = Mock()
        # Create a StringIO console for capturing output
        string_io = StringIO()
        mock_shell.console = Console(file=string_io)
        command = LoadavgCommand(mock_shell)
        command._test_output = string_io  # type: ignore[attr-defined]
        return command

    @pytest.fixture
    def mock_client(self):
        """Create a mock client for testing."""
        mock_client = Mock()

        def mock_pull_side_effect(path):
            """Mock pull method for different file paths."""
            mock_context = MagicMock()
            mock_file = Mock()

            if path == "/proc/loadavg":
                # Create a mock bytes object that returns a string when strip() is called
                mock_bytes = Mock()
                mock_bytes.strip.return_value = "0.50 0.25 0.10 1/234 12345"
                mock_file.read.return_value = mock_bytes
            elif path == "/proc/cpuinfo":
                # Mock cpuinfo content
                cpuinfo_content = (
                    "processor\t: 0\nprocessor\t: 1\nprocessor\t: 2\nprocessor\t: 3"
                )
                mock_file.read.return_value = cpuinfo_content
            else:
                mock_file.read.return_value = ""

            mock_context.__enter__.return_value = mock_file
            mock_context.__exit__.return_value = None
            return mock_context

        mock_client.pull.side_effect = mock_pull_side_effect
        return mock_client

    def test_execute_success(self, command, mock_client):
        """Test executing loadavg command successfully."""
        command.execute(mock_client, [])

        # Should call pull for both /proc/loadavg and /proc/cpuinfo
        assert mock_client.pull.call_count >= 1
        mock_client.pull.assert_any_call("/proc/loadavg")

        output = command._test_output.getvalue()
        assert "Load Average Information:" in output
        assert "Load Average (1 min)" in output
        assert "0.50" in output
        assert "0.25" in output
        assert "0.10" in output

    @patch("pebble_shell.commands.system.parse_proc_loadavg")
    def test_execute_file_not_found(self, mock_parse_loadavg, command, mock_client):
        """Test handling file not found error."""
        from pebble_shell.utils.proc_reader import ProcReadError

        mock_parse_loadavg.side_effect = ProcReadError(
            "/proc/loadavg", "File not found"
        )

        result = command.execute(mock_client, [])

        output = command._test_output.getvalue()
        assert "Error reading load average data" in output
        assert result == 1

    @patch("pebble_shell.commands.system.parse_proc_loadavg")
    def test_execute_invalid_format(self, mock_parse_loadavg, command, mock_client):
        """Test handling invalid file format."""
        from pebble_shell.utils.proc_reader import ProcReadError

        mock_parse_loadavg.side_effect = ProcReadError(
            "/proc/loadavg", "Invalid loadavg format"
        )

        result = command.execute(mock_client, [])

        output = command._test_output.getvalue()
        assert "Error reading load average data" in output
        assert result == 1


class TestDmesgCommand:
    """Test cases for DmesgCommand."""

    @pytest.fixture
    def command(self):
        """Create DmesgCommand instance."""
        mock_shell = Mock()
        string_io = StringIO()
        mock_shell.console = Console(file=string_io)
        command = DmesgCommand(mock_shell)
        command._test_output = string_io  # type: ignore[attr-defined]
        return command

    @pytest.fixture
    def mock_client(self):
        """Create mock client."""
        mock_client = Mock()
        return mock_client

    def test_execute_success_first_source(self, command, mock_client):
        """Test dmesg command success with first source available."""

        def mock_pull_side_effect(path):
            """Mock pull method for different file paths."""
            mock_context = MagicMock()
            mock_file = Mock()

            if path == "/proc/kmsg":
                mock_file.read.return_value = (
                    "[    0.000000] Linux version 5.4.0\n"
                    "[    0.000001] Command line: BOOT_IMAGE=/vmlinuz\n"
                    "[    0.000002] This is an error message\n"
                    "[    0.000003] This is a warning message\n"
                    "[    0.000004] This is an info message\n"
                    "[    0.000005] Normal kernel message\n"
                )
            else:
                raise ops.pebble.PathError("kind", "File not found")

            mock_context.__enter__.return_value = mock_file
            mock_context.__exit__.return_value = None
            return mock_context

        mock_client.pull.side_effect = mock_pull_side_effect
        result = command.execute(mock_client, [])

        assert result == 0
        output = command._test_output.getvalue()
        assert "Linux version 5.4.0" in output
        assert "Command line:" in output
        # Note: color coding is applied but we're checking content exists

    def test_execute_success_fallback_source(self, command, mock_client):
        """Test dmesg command success with fallback source."""

        def mock_pull_side_effect(path):
            """Mock pull method for different file paths."""
            mock_context = MagicMock()
            mock_file = Mock()

            if path in ["/proc/kmsg", "/var/log/dmesg"]:
                raise ops.pebble.PathError("kind", "File not found")
            if path == "/var/log/kern.log":
                mock_file.read.return_value = (
                    "Jul 22 10:30:01 hostname kernel: [12345.123] USB disconnect\n"
                    "Jul 22 10:30:02 hostname kernel: [12345.456] Network interface up\n"
                )
            else:
                raise ops.pebble.PathError("kind", "File not found")

            mock_context.__enter__.return_value = mock_file
            mock_context.__exit__.return_value = None
            return mock_context

        mock_client.pull.side_effect = mock_pull_side_effect
        result = command.execute(mock_client, [])

        assert result == 0
        output = command._test_output.getvalue()
        assert "USB disconnect" in output
        assert "Network interface up" in output

    def test_execute_no_sources_found(self, command, mock_client):
        """Test dmesg command when no sources are available."""

        def mock_pull_side_effect(path):
            """Mock pull method that always fails."""
            raise ops.pebble.PathError("kind", "File not found")

        mock_client.pull.side_effect = mock_pull_side_effect
        result = command.execute(mock_client, [])

        assert result == 1
        output = command._test_output.getvalue()
        assert "No kernel messages found" in output
        assert "/proc/kmsg" in output  # Should list tried sources

    def test_execute_empty_content(self, command, mock_client):
        """Test dmesg command with empty content."""

        def mock_pull_side_effect(path):
            """Mock pull method that returns empty content."""
            mock_context = MagicMock()
            mock_file = Mock()

            if path == "/proc/kmsg":
                mock_file.read.return_value = ""
            else:
                raise ops.pebble.PathError("kind", "File not found")

            mock_context.__enter__.return_value = mock_file
            mock_context.__exit__.return_value = None
            return mock_context

        mock_client.pull.side_effect = mock_pull_side_effect
        result = command.execute(mock_client, [])

        assert result == 1
        output = command._test_output.getvalue()
        assert "No kernel messages found" in output

    def test_execute_large_output_truncation(self, command, mock_client):
        """Test dmesg command with output that needs truncation."""

        def mock_pull_side_effect(path):
            """Mock pull method with large content."""
            mock_context = MagicMock()
            mock_file = Mock()

            if path == "/proc/kmsg":
                # Create content with more than 1000 lines
                lines = [f"[{i:10.6f}] Kernel message {i}" for i in range(1500)]
                mock_file.read.return_value = "\n".join(lines)
            else:
                raise ops.pebble.PathError("kind", "File not found")

            mock_context.__enter__.return_value = mock_file
            mock_context.__exit__.return_value = None
            return mock_context

        mock_client.pull.side_effect = mock_pull_side_effect
        result = command.execute(mock_client, [])

        assert result == 0
        output = command._test_output.getvalue()
        assert "Showing last 1000 lines..." in output
        assert "Kernel message 1499" in output  # Should show the last messages
        assert "Kernel message 0" not in output  # Should not show early messages


class TestMountCommand:
    """Test cases for MountCommand."""

    @pytest.fixture
    def command(self):
        """Create a MountCommand for testing."""
        mock_shell = Mock()
        # Create a StringIO console for capturing output
        string_io = StringIO()
        mock_shell.console = Console(file=string_io)
        command = MountCommand(mock_shell)
        command._test_output = string_io  # type: ignore[attr-defined]
        return command

    @pytest.fixture
    def mock_client(self):
        """Create a mock client for testing."""
        return Mock()

    def test_mount_success(self, command, mock_client):
        """Test mount with successful output."""
        test_output = """/dev/sda1 / ext4 rw,relatime 0 0
/dev/sda2 /home ext4 rw,relatime 0 0
tmpfs /tmp tmpfs rw,nosuid,nodev 0 0
proc /proc proc rw,nosuid,nodev,noexec,relatime 0 0"""

        # Mock successful /proc/mounts reading
        mock_context = MagicMock()
        mock_file = Mock()
        mock_file.read.return_value = test_output
        mock_context.__enter__.return_value = mock_file
        mock_context.__exit__.return_value = None
        mock_client.pull.return_value = mock_context

        result = command.execute(mock_client, [])

        assert result == 0
        mock_client.pull.assert_called_once_with("/proc/mounts")
        output = command._test_output.getvalue()
        assert "/dev/sda1" in output
        assert "ext4" in output
        assert "tmpfs" in output

    def test_mount_proc_mounts_fallback(self, command, mock_client):
        """Test mount with /proc/mounts fallback."""
        # This test is actually redundant since MountCommand only reads /proc/mounts
        # But keeping it for consistency with the original plan
        proc_mounts_content = """/dev/sda1 / ext4 rw,relatime 0 0
tmpfs /tmp tmpfs rw,nosuid,nodev 0 0"""

        mock_context = MagicMock()
        mock_file = Mock()
        mock_file.read.return_value = proc_mounts_content
        mock_context.__enter__.return_value = mock_file
        mock_context.__exit__.return_value = None
        mock_client.pull.return_value = mock_context

        result = command.execute(mock_client, [])

        assert result == 0
        output = command._test_output.getvalue()
        assert "/dev/sda1" in output
        assert "ext4" in output

    def test_mount_filesystem_coloring(self, command, mock_client):
        """Test mount output filesystem type coloring."""
        test_output = """/dev/sda1 / ext4 rw,relatime 0 0
/dev/sda2 /boot vfat rw,relatime 0 0
tmpfs /tmp tmpfs rw,nosuid,nodev 0 0
proc /proc proc rw,nosuid,nodev,noexec,relatime 0 0
devpts /dev/pts devpts rw,relatime 0 0"""

        mock_context = MagicMock()
        mock_file = Mock()
        mock_file.read.return_value = test_output
        mock_context.__enter__.return_value = mock_file
        mock_context.__exit__.return_value = None
        mock_client.pull.return_value = mock_context

        result = command.execute(mock_client, [])

        assert result == 0
        output = command._test_output.getvalue()
        # Check for filesystem types (colors will be stripped in output)
        assert "ext4" in output
        assert "tmpfs" in output
        assert "proc" in output
        assert "devpts" in output

    def test_mount_error_handling(self, command, mock_client):
        """Test mount command error handling."""
        mock_client.pull.side_effect = Exception("Cannot read /proc/mounts")

        result = command.execute(mock_client, [])

        assert result == 1

    def test_mount_empty_output(self, command, mock_client):
        """Test mount with empty output."""
        mock_context = MagicMock()
        mock_file = Mock()
        mock_file.read.return_value = ""
        mock_context.__enter__.return_value = mock_file
        mock_context.__exit__.return_value = None
        mock_client.pull.return_value = mock_context

        result = command.execute(mock_client, [])

        assert result == 0
        output = command._test_output.getvalue()
        # Should still show table headers
        assert "Device" in output
        assert "Mount Point" in output

    def test_mount_malformed_lines(self, command, mock_client):
        """Test mount with malformed lines that should be skipped."""
        test_output = """/dev/sda1 / ext4 rw,relatime 0 0
invalid line without enough fields
/dev/sda2 /home ext4 rw,relatime 0 0
another invalid line
tmpfs /tmp tmpfs rw,nosuid,nodev 0 0"""

        mock_context = MagicMock()
        mock_file = Mock()
        mock_file.read.return_value = test_output
        mock_context.__enter__.return_value = mock_file
        mock_context.__exit__.return_value = None
        mock_client.pull.return_value = mock_context

        result = command.execute(mock_client, [])

        assert result == 0
        output = command._test_output.getvalue()
        # Valid lines should be present
        assert "/dev/sda1" in output
        assert "/dev/sda2" in output
        assert "tmpfs" in output
        # Invalid lines should be skipped (not cause errors)


class TestPstreeCommand:
    """Test cases for PstreeCommand."""

    @pytest.fixture
    def command(self):
        """Create a PstreeCommand for testing."""
        mock_shell = Mock()
        command = PstreeCommand(mock_shell)
        # Create a mock console that records calls
        command.console = Mock()
        return command

    @pytest.fixture
    def mock_client(self):
        """Create a mock client for testing."""
        return Mock()

    def test_pstree_no_processes(self, command, mock_client):
        """Test pstree when no process directories found."""
        mock_entries = [Mock(name="self"), Mock(name="cmdline")]  # No numeric entries
        mock_client.list_files.return_value = mock_entries

        result = command.execute(mock_client, [])

        # Should succeed with empty process tree (pids = [])
        assert result == 0

    def test_pstree_process_read_error(self, command, mock_client):
        """Test pstree when process files can't be read."""
        mock_entries = [Mock(name="1"), Mock(name="100")]
        mock_client.list_files.return_value = mock_entries

        # Mock status files failing to read
        mock_client.pull.side_effect = ops.pebble.PathError("kind", "File not found")

        result = command.execute(mock_client, [])

        assert result == 0  # Should succeed even if some files can't be read

    def test_pstree_error_handling(self, command, mock_client):
        """Test pstree error handling."""
        mock_client.list_files.side_effect = Exception("Cannot access /proc")

        # Capture print output for error
        with patch("builtins.print") as mock_print:
            result = command.execute(mock_client, [])

            assert result == 1
            mock_print.assert_called_with(
                "Error building process tree: Cannot access /proc"
            )

    def test_pstree_success_basic(self, command, mock_client):
        """Test basic pstree functionality."""
        mock_entries = [Mock(name="1")]
        mock_client.list_files.return_value = mock_entries

        # Mock successful status and cmdline reads
        def mock_pull_side_effect(path):
            mock_context = MagicMock()
            mock_file = Mock()

            if path == "/proc/1/status":
                mock_file.read.return_value = """Name:	init
PPid:	0"""
            elif path == "/proc/1/cmdline":
                mock_file.read.return_value = "/sbin/init"
            else:
                mock_file.read.return_value = ""

            mock_context.__enter__.return_value = mock_file
            mock_context.__exit__.return_value = None
            return mock_context

        mock_client.pull.side_effect = mock_pull_side_effect

        result = command.execute(mock_client, [])

        # Should succeed and build process tree
        assert result == 0


class TestLastCommand:
    def test_execute_success(self):
        """Test successful execution with login entries found."""
        mock_shell = Mock()
        command = LastCommand(mock_shell)
        command.console = Mock()

        mock_client = Mock()

        # Mock file content with login entries
        auth_log_content = """Jan 15 10:30:15 hostname sshd[1234]: Accepted password for user1 from 192.168.1.10 port 22 ssh2
Jan 15 11:45:22 hostname login[5678]: session opened for user local on tty1
Jan 15 12:15:33 hostname sshd[9012]: Accepted publickey for user2 from 10.0.0.5 port 22 ssh2"""

        def mock_pull_side_effect(path: str):
            mock_context = MagicMock()
            mock_file = Mock()
            if path == "/var/log/auth.log":
                mock_file.read.return_value = auth_log_content
            else:
                # Simulate file not found for other log files
                raise ops.pebble.PathError("path", "not found")
            mock_context.__enter__.return_value = mock_file
            mock_context.__exit__.return_value = None
            return mock_context

        mock_client.pull.side_effect = mock_pull_side_effect

        result = command.execute(mock_client, [])

        # Verify table was printed
        command.console.print.assert_called_once()
        # Should succeed
        assert result == 0

    def test_execute_no_login_entries(self):
        """Test execution when no login entries are found."""
        mock_shell = Mock()
        command = LastCommand(mock_shell)
        command.console = Mock()

        mock_client = Mock()

        def mock_pull_side_effect(path: str):
            # All log files not found
            raise ops.pebble.PathError("path", "not found")

        mock_client.pull.side_effect = mock_pull_side_effect

        result = command.execute(mock_client, [])

        # Verify panel was printed
        command.console.print.assert_called_once()
        call_args = command.console.print.call_args[0][0]
        assert hasattr(call_args, "renderable")  # It's a Panel
        # Should return error
        assert result == 1

    def test_execute_empty_log_files(self):
        """Test execution when log files exist but contain no login entries."""
        mock_shell = Mock()
        command = LastCommand(mock_shell)
        command.console = Mock()

        mock_client = Mock()

        def mock_pull_side_effect(path: str):
            mock_context = MagicMock()
            mock_file = Mock()
            if path == "/var/log/auth.log":
                mock_file.read.return_value = (
                    "Some other entries\nWithout matching keywords"
                )
            else:
                raise ops.pebble.PathError("path", "not found")
            mock_context.__enter__.return_value = mock_file
            mock_context.__exit__.return_value = None
            return mock_context

        mock_client.pull.side_effect = mock_pull_side_effect

        result = command.execute(mock_client, [])

        # Should show no login information found
        command.console.print.assert_called_once()
        assert result == 1

    def test_execute_help(self):
        """Test help display."""
        mock_shell = Mock()
        command = LastCommand(mock_shell)
        command.show_help = Mock()  # type: ignore[method-assign]

        mock_client = Mock()
        result = command.execute(mock_client, ["-h"])

        command.show_help.assert_called_once()  # type: ignore[attr-defined]
        assert result == 0


class TestWCommand:
    def test_execute_success(self):
        """Test successful execution with active sessions."""
        mock_shell = Mock()
        command = WCommand(mock_shell)
        command.console = Mock()
        command._get_username_from_uid = Mock(return_value="testuser")  # type: ignore[method-assign]
        command._get_tty_for_process = Mock(return_value="pts/0")  # type: ignore[method-assign]
        command._get_process_start_time = Mock(return_value="10:30")  # type: ignore[method-assign]

        mock_client = Mock()

        # Mock directory listing for /proc
        proc_entry1 = Mock()
        proc_entry1.name = "1234"
        proc_entry2 = Mock()
        proc_entry2.name = "5678"
        proc_entry3 = Mock()
        proc_entry3.name = "not_a_pid"
        mock_client.list_files.return_value = [proc_entry1, proc_entry2, proc_entry3]

        status_content = """Name:	bash
Umask:	0022
State:	S (sleeping)
Tgid:	1234
Ngid:	0
Pid:	1234
PPid:	1
TracerPid:	0
Uid:	1000	1000	1000	1000
Gid:	1000	1000	1000	1000"""

        cmdline_content = "/bin/bash"

        def mock_pull_side_effect(path: str):
            mock_context = MagicMock()
            mock_file = Mock()
            if path.endswith("/status"):
                mock_file.read.return_value = status_content
            elif path.endswith("/cmdline"):
                mock_file.read.return_value = cmdline_content
            else:
                raise ops.pebble.PathError("path", "not found")
            mock_context.__enter__.return_value = mock_file
            mock_context.__exit__.return_value = None
            return mock_context

        mock_client.pull.side_effect = mock_pull_side_effect

        result = command.execute(mock_client, [])

        # Verify table was printed
        command.console.print.assert_called_once()
        # Should succeed
        assert result == 0

    def test_execute_no_sessions(self):
        """Test execution when no active sessions are found."""
        mock_shell = Mock()
        command = WCommand(mock_shell)
        command.console = Mock()

        mock_client = Mock()

        # Mock directory listing for /proc with no valid PIDs
        proc_entry1 = Mock()
        proc_entry1.name = "not_a_pid"
        mock_client.list_files.return_value = [proc_entry1]

        result = command.execute(mock_client, [])

        # Should show no sessions found
        command.console.print.assert_called_once()
        call_args = command.console.print.call_args[0][0]
        assert hasattr(call_args, "renderable")  # It's a Panel
        assert result == 1

    def test_execute_process_read_error(self):
        """Test execution when process files cannot be read."""
        mock_shell = Mock()
        command = WCommand(mock_shell)
        command.console = Mock()

        mock_client = Mock()

        # Mock directory listing for /proc
        proc_entry1 = Mock()
        proc_entry1.name = "1234"
        mock_client.list_files.return_value = [proc_entry1]

        def mock_pull_side_effect(path: str):
            # Simulate file read errors
            raise ops.pebble.PathError("path", "not found")

        mock_client.pull.side_effect = mock_pull_side_effect

        result = command.execute(mock_client, [])

        # Should show no sessions found (processes couldn't be read)
        command.console.print.assert_called_once()
        assert result == 1

    def test_execute_error_handling(self):
        """Test execution when an unexpected error occurs."""
        mock_shell = Mock()
        command = WCommand(mock_shell)
        command.console = Mock()

        mock_client = Mock()
        mock_client.list_files.side_effect = Exception("Unexpected error")

        result = command.execute(mock_client, [])

        # Should print error message
        command.console.print.assert_called_once()
        call_args = command.console.print.call_args[0][0]
        assert "Error getting session information" in str(call_args)
        assert result == 1

    def test_execute_help(self):
        """Test help display."""
        mock_shell = Mock()
        command = WCommand(mock_shell)
        command.show_help = Mock()  # type: ignore[method-assign]

        mock_client = Mock()
        result = command.execute(mock_client, ["-h"])

        command.show_help.assert_called_once()  # type: ignore[attr-defined]
        assert result == 0

    def test_get_tty_for_process(self):
        """Test TTY extraction from process stat."""
        mock_shell = Mock()
        command = WCommand(mock_shell)
        mock_client = Mock()

        stat_content = "1234 (bash) S 1 1234 1234 34816 1234 4194304 234 0 0 0 0 0 0 0 20 0 1 0 12345678 12345678 123 18446744073709551615"

        def mock_pull_side_effect(path: str):
            mock_context = MagicMock()
            mock_file = Mock()
            mock_file.read.return_value = stat_content
            mock_context.__enter__.return_value = mock_file
            mock_context.__exit__.return_value = None
            return mock_context

        mock_client.pull.side_effect = mock_pull_side_effect

        result = command._get_tty_for_process(mock_client, "1234")
        assert "pts/" in result or result == "?"


class TestPgrepCommand:
    def test_execute_success_pattern_match(self):
        """Test successful execution with pattern matching."""
        mock_shell = Mock()
        command = PgrepCommand(mock_shell)
        command.console = Mock()

        mock_client = Mock()

        # Mock directory listing for /proc
        proc_entry1 = Mock()
        proc_entry1.name = "1234"
        proc_entry2 = Mock()
        proc_entry2.name = "5678"
        mock_client.list_files.return_value = [proc_entry1, proc_entry2]

        def mock_pull_side_effect(path: str):
            mock_context = MagicMock()
            mock_file = Mock()

            if path.endswith("/1234/comm"):
                mock_file.read.return_value = "bash\n"
            elif path.endswith("/5678/comm"):
                mock_file.read.return_value = "python\n"
            elif path.endswith("/1234/status"):
                mock_file.read.return_value = (
                    "Name:\tbash\nUid:\t1000\t1000\t1000\t1000\n"
                )
            elif path.endswith("/5678/status"):
                mock_file.read.return_value = (
                    "Name:\tpython\nUid:\t1000\t1000\t1000\t1000\n"
                )
            elif path.endswith("/cmdline"):
                mock_file.read.return_value = "/bin/bash"
            elif path == "/etc/passwd":
                mock_file.read.return_value = "root:x:0:0::/root:/bin/bash\ntestuser:x:1000:1000::/home/testuser:/bin/bash\n"
            else:
                raise ops.pebble.PathError("path", "not found")

            mock_context.__enter__.return_value = mock_file
            mock_context.__exit__.return_value = None
            return mock_context

        mock_client.pull.side_effect = mock_pull_side_effect

        # Mock print function to capture output
        with patch("builtins.print") as mock_print:
            result = command.execute(mock_client, ["bash"])

        # Should succeed and print results
        assert result == 0
        command.console.print.assert_called()  # Table printed
        mock_print.assert_called()  # PIDs printed

    def test_execute_full_match_option(self):
        """Test -f option for full command line matching."""
        mock_shell = Mock()
        command = PgrepCommand(mock_shell)
        command.console = Mock()

        mock_client = Mock()

        proc_entry1 = Mock()
        proc_entry1.name = "1234"
        mock_client.list_files.return_value = [proc_entry1]

        def mock_pull_side_effect(path: str):
            mock_context = MagicMock()
            mock_file = Mock()

            if path.endswith("/comm"):
                mock_file.read.return_value = "python3\n"
            elif path.endswith("/cmdline"):
                mock_file.read.return_value = "python3\x00-m\x00pytest\x00"
            elif path.endswith("/status"):
                mock_file.read.return_value = (
                    "Name:\tpython3\nUid:\t1000\t1000\t1000\t1000\n"
                )
            elif path == "/etc/passwd":
                mock_file.read.return_value = (
                    "testuser:x:1000:1000::/home/testuser:/bin/bash\n"
                )
            else:
                raise ops.pebble.PathError("path", "not found")

            mock_context.__enter__.return_value = mock_file
            mock_context.__exit__.return_value = None
            return mock_context

        mock_client.pull.side_effect = mock_pull_side_effect

        with patch("builtins.print"):
            result = command.execute(mock_client, ["-f", "pytest"])

        assert result == 0

    def test_execute_user_filter(self):
        """Test -u option for user filtering."""
        mock_shell = Mock()
        command = PgrepCommand(mock_shell)
        command.console = Mock()

        mock_client = Mock()

        proc_entry1 = Mock()
        proc_entry1.name = "1234"
        mock_client.list_files.return_value = [proc_entry1]

        def mock_pull_side_effect(path: str):
            mock_context = MagicMock()
            mock_file = Mock()

            if path.endswith("/comm"):
                mock_file.read.return_value = "bash\n"
            elif path.endswith("/status"):
                mock_file.read.return_value = (
                    "Name:\tbash\nUid:\t1000\t1000\t1000\t1000\n"
                )
            elif path.endswith("/cmdline"):
                mock_file.read.return_value = "/bin/bash"
            elif path == "/etc/passwd":
                mock_file.read.return_value = (
                    "testuser:x:1000:1000::/home/testuser:/bin/bash\n"
                )
            else:
                raise ops.pebble.PathError("path", "not found")

            mock_context.__enter__.return_value = mock_file
            mock_context.__exit__.return_value = None
            return mock_context

        mock_client.pull.side_effect = mock_pull_side_effect

        with patch("builtins.print"):
            result = command.execute(mock_client, ["-u", "testuser", "bash"])

        assert result == 0

    def test_execute_no_matches(self):
        """Test when no processes match the pattern."""
        mock_shell = Mock()
        command = PgrepCommand(mock_shell)
        command.console = Mock()

        mock_client = Mock()

        proc_entry1 = Mock()
        proc_entry1.name = "1234"
        mock_client.list_files.return_value = [proc_entry1]

        def mock_pull_side_effect(path: str):
            mock_context = MagicMock()
            mock_file = Mock()

            if path.endswith("/comm"):
                mock_file.read.return_value = "bash\n"
            else:
                raise ops.pebble.PathError("path", "not found")

            mock_context.__enter__.return_value = mock_file
            mock_context.__exit__.return_value = None
            return mock_context

        mock_client.pull.side_effect = mock_pull_side_effect

        result = command.execute(mock_client, ["nonexistent"])

        assert result == 1
        command.console.print.assert_called_with(
            "No processes found matching 'nonexistent'"
        )

    def test_execute_no_args(self):
        """Test execution with no arguments."""
        mock_shell = Mock()
        command = PgrepCommand(mock_shell)
        command.console = Mock()

        mock_client = Mock()
        result = command.execute(mock_client, [])

        assert result == 1
        # Should print usage information (multiple lines)
        assert command.console.print.call_count == 3
        command.console.print.assert_any_call("Usage: pgrep [-f] [-u user] [pattern]")

    def test_execute_invalid_option(self):
        """Test execution with invalid option."""
        mock_shell = Mock()
        command = PgrepCommand(mock_shell)
        command.console = Mock()

        mock_client = Mock()
        result = command.execute(mock_client, ["-x", "bash"])

        assert result == 1
        command.console.print.assert_called_with("Error: Unknown option -x")

    def test_execute_user_option_missing_value(self):
        """Test -u option without username."""
        mock_shell = Mock()
        command = PgrepCommand(mock_shell)
        command.console = Mock()

        mock_client = Mock()
        result = command.execute(mock_client, ["-u"])

        assert result == 1
        command.console.print.assert_called_with("Error: -u requires a username")

    def test_execute_proc_read_error(self):
        """Test error when /proc cannot be read."""
        mock_shell = Mock()
        command = PgrepCommand(mock_shell)
        command.console = Mock()

        mock_client = Mock()
        mock_client.list_files.side_effect = ops.pebble.PathError("path", "not found")

        result = command.execute(mock_client, ["bash"])

        assert result == 1
        # Check that an error message was printed
        assert command.console.print.call_count > 0

    def test_execute_help(self):
        """Test help display."""
        mock_shell = Mock()
        command = PgrepCommand(mock_shell)
        command.show_help = Mock()  # type: ignore[method-assign]

        mock_client = Mock()
        result = command.execute(mock_client, ["-h"])

        command.show_help.assert_called_once()  # type: ignore[attr-defined]
        assert result == 0


class TestVmstatCommand:
    def test_execute_success_default(self):
        """Test successful execution with default parameters."""
        mock_shell = Mock()
        command = VmstatCommand(mock_shell)
        command.console = Mock()

        mock_client = Mock()

        # Mock the data files
        stat_content = """cpu  100000 1000 50000 800000 2000 0 1000
cpu0 25000 250 12500 200000 500 0 250
intr 1000000
ctxt 5000000
btime 1640995200
processes 10000
procs_running 2
procs_blocked 0"""

        meminfo_content = """MemTotal:        8192000 kB
MemFree:         2048000 kB
MemAvailable:    4096000 kB
Buffers:          512000 kB
Cached:          1024000 kB
SwapCached:            0 kB
SwapTotal:       2048000 kB
SwapFree:        2048000 kB"""

        vmstat_content = """nr_free_pages 512000
nr_alloc_batch 128
nr_inactive_anon 64000
nr_active_anon 128000
nr_inactive_file 256000
nr_active_file 384000
pgpgin 1000000
pgpgout 800000
pswpin 100
pswpout 50"""

        def mock_pull_side_effect(path: str):
            mock_context = MagicMock()
            mock_file = Mock()
            if path == "/proc/stat":
                mock_file.read.return_value = stat_content
            elif path == "/proc/meminfo":
                mock_file.read.return_value = meminfo_content
            elif path == "/proc/vmstat":
                mock_file.read.return_value = vmstat_content
            else:
                raise ops.pebble.PathError("path", "not found")
            mock_context.__enter__.return_value = mock_file
            mock_context.__exit__.return_value = None
            return mock_context

        mock_client.pull.side_effect = mock_pull_side_effect

        result = command.execute(mock_client, [])

        # Should succeed
        assert result == 0
        # Should print the vmstat output (2 print calls: table and traditional format)
        assert command.console.print.call_count >= 2

    def test_execute_with_interval_and_count(self):
        """Test execution with custom interval and count."""
        mock_shell = Mock()
        command = VmstatCommand(mock_shell)
        command.console = Mock()

        mock_client = Mock()

        # Mock basic stats
        stat_content = "cpu  100000 1000 50000 800000 2000 0 1000"
        meminfo_content = (
            "MemTotal: 8192000 kB\nMemFree: 2048000 kB\nMemAvailable: 4096000 kB"
        )

        def mock_pull_side_effect(path: str):
            mock_context = MagicMock()
            mock_file = Mock()
            if path == "/proc/stat":
                mock_file.read.return_value = stat_content
            elif path == "/proc/meminfo":
                mock_file.read.return_value = meminfo_content
            elif path == "/proc/vmstat":
                mock_file.read.return_value = "pgpgin 1000\npgpgout 800"
            else:
                raise ops.pebble.PathError("path", "not found")
            mock_context.__enter__.return_value = mock_file
            mock_context.__exit__.return_value = None
            return mock_context

        mock_client.pull.side_effect = mock_pull_side_effect

        # Mock time.sleep to avoid actual delays
        with patch("time.sleep"):
            result = command.execute(mock_client, ["0.1", "2"])

        assert result == 0

    def test_execute_invalid_interval(self):
        """Test execution with invalid interval."""
        mock_shell = Mock()
        command = VmstatCommand(mock_shell)
        command.console = Mock()

        mock_client = Mock()

        result = command.execute(mock_client, ["invalid"])

        assert result == 1
        command.console.print.assert_called_with("Error: interval must be a number")

    def test_execute_interval_too_small(self):
        """Test execution with interval too small."""
        mock_shell = Mock()
        command = VmstatCommand(mock_shell)
        command.console = Mock()

        mock_client = Mock()

        result = command.execute(mock_client, ["0.05"])

        assert result == 1
        command.console.print.assert_called_with(
            "Error: interval must be at least 0.1 seconds"
        )

    def test_execute_invalid_count(self):
        """Test execution with invalid count."""
        mock_shell = Mock()
        command = VmstatCommand(mock_shell)
        command.console = Mock()

        mock_client = Mock()

        result = command.execute(mock_client, ["1.0", "invalid"])

        assert result == 1
        command.console.print.assert_called_with("Error: count must be a number")

    def test_execute_count_too_small(self):
        """Test execution with count too small."""
        mock_shell = Mock()
        command = VmstatCommand(mock_shell)
        command.console = Mock()

        mock_client = Mock()

        result = command.execute(mock_client, ["1.0", "0"])

        assert result == 1
        command.console.print.assert_called_with("Error: count must be at least 1")

    @patch("pebble_shell.commands.system.parse_proc_stat")
    def test_execute_file_read_error(self, mock_parse_stat):
        """Test execution when file reading fails."""
        from pebble_shell.utils.proc_reader import ProcReadError

        mock_shell = Mock()
        command = VmstatCommand(mock_shell)
        command.console = Mock()

        mock_client = Mock()
        mock_parse_stat.side_effect = ProcReadError("/proc/stat", "not found")

        result = command.execute(mock_client, [])

        # Should return error code and print error message
        assert result == 1
        command.console.print.assert_called_with(
            "[red]Error reading vmstat data: Error reading /proc/stat: not found[/red]"
        )

    def test_execute_help(self):
        """Test help display."""
        mock_shell = Mock()
        command = VmstatCommand(mock_shell)
        command.show_help = Mock()  # type: ignore[method-assign]

        mock_client = Mock()
        result = command.execute(mock_client, ["-h"])

        command.show_help.assert_called_once()  # type: ignore[attr-defined]
        assert result == 0

    def test_get_vmstat_data_success(self):
        """Test _get_vmstat_data method."""
        mock_shell = Mock()
        command = VmstatCommand(mock_shell)

        mock_client = Mock()

        stat_content = "cpu  100000 1000 50000 800000 2000 500 1000"
        meminfo_content = "MemTotal: 8192000 kB\nMemFree: 2048000 kB"
        vmstat_content = "pgpgin 1000\npgpgout 800"

        def mock_pull_side_effect(path: str):
            mock_context = MagicMock()
            mock_file = Mock()
            if path == "/proc/stat":
                mock_file.read.return_value = stat_content
            elif path == "/proc/meminfo":
                mock_file.read.return_value = meminfo_content
            elif path == "/proc/vmstat":
                mock_file.read.return_value = vmstat_content
            else:
                raise ops.pebble.PathError("path", "not found")
            mock_context.__enter__.return_value = mock_file
            mock_context.__exit__.return_value = None
            return mock_context

        mock_client.pull.side_effect = mock_pull_side_effect

        result = command._get_vmstat_data(mock_client)

        assert result is not None
        assert "cpu" in result
        assert "memory" in result
        assert "vmstat" in result
        assert result["cpu"]["user"] == 100000
        assert result["memory"]["MemTotal"] == 8192000
        assert result["vmstat"]["pgpgin"] == 1000


class TestIostatCommand:
    """Test cases for IostatCommand."""

    def test_execute_success_default(self):
        """Test successful execution with default parameters."""
        mock_shell = Mock()
        command = IostatCommand(mock_shell)
        command.console = Mock()

        mock_client = Mock()

        # Mock realistic diskstats content based on real Ubuntu system
        diskstats_content = """   7       0 loop0 42 0 944 9 0 0 0 0 0 9 9 0 0 0 0 0 0
   8       0 sda 136678 23792 14480911 64412 645944 1150244 27677230 1056184 0 468791 1339495 68750 0 57463656 28345 279906 190553
   8       1 sda1 135734 23223 14367055 64078 645894 1150210 27676802 1056095 0 501314 1148518 68750 0 57463656 28345 0 0
   8      15 sda15 246 554 20415 69 2 0 2 1 0 41 70 0 0 0 0 0 0
 259       0 sda16 502 15 87001 230 36 26 322 60 0 186 290 0 0 0 0 0 0"""

        # Mock CPU stats for I/O wait
        stat_content = """cpu  608644 1501 535554 19329831 23410 0 25763 0 0 0
cpu0 321429 985 271385 9697822 11582 0 15947 0 0 0
cpu1 287215 515 264169 9632008 11828 0 9816 0 0 0"""

        def mock_pull_side_effect(path: str):
            mock_context = MagicMock()
            mock_file = Mock()
            if path == "/proc/diskstats":
                mock_file.read.return_value = diskstats_content
            elif path == "/proc/stat":
                mock_file.read.return_value = stat_content
            else:
                raise ops.pebble.PathError("path", "not found")
            mock_context.__enter__.return_value = mock_file
            mock_context.__exit__.return_value = None
            return mock_context

        mock_client.pull.side_effect = mock_pull_side_effect

        result = command.execute(mock_client, [])

        # Should succeed
        assert result == 0
        # Should print iostat output
        assert command.console.print.call_count >= 1

    def test_execute_with_interval_and_count(self):
        """Test execution with custom interval and count."""
        mock_shell = Mock()
        command = IostatCommand(mock_shell)
        command.console = Mock()

        mock_client = Mock()

        diskstats_content = (
            "   8       0 sda 1000 0 8000 100 2000 0 16000 200 0 300 300 0 0 0 0 0 0"
        )
        stat_content = "cpu  100000 1000 50000 800000 2000 0 1000"

        def mock_pull_side_effect(path: str):
            mock_context = MagicMock()
            mock_file = Mock()
            if path == "/proc/diskstats":
                mock_file.read.return_value = diskstats_content
            elif path == "/proc/stat":
                mock_file.read.return_value = stat_content
            else:
                raise ops.pebble.PathError("path", "not found")
            mock_context.__enter__.return_value = mock_file
            mock_context.__exit__.return_value = None
            return mock_context

        mock_client.pull.side_effect = mock_pull_side_effect

        # Mock time.sleep to avoid actual delays
        with patch("time.sleep"):
            result = command.execute(mock_client, ["2", "3"])

        assert result == 0
        # Should have printed multiple times (for each iteration)
        assert command.console.print.call_count >= 3

    def test_execute_invalid_interval(self):
        """Test execution with invalid interval."""
        mock_shell = Mock()
        command = IostatCommand(mock_shell)
        command.console = Mock()

        mock_client = Mock()

        result = command.execute(mock_client, ["invalid"])

        assert result == 1
        command.console.print.assert_called_with("Error: interval must be a number")

    def test_execute_interval_too_small(self):
        """Test execution with interval too small."""
        mock_shell = Mock()
        command = IostatCommand(mock_shell)
        command.console = Mock()

        mock_client = Mock()

        result = command.execute(mock_client, ["0.05"])

        assert result == 1
        command.console.print.assert_called_with(
            "Error: interval must be at least 0.1 seconds"
        )

    def test_execute_invalid_count(self):
        """Test execution with invalid count."""
        mock_shell = Mock()
        command = IostatCommand(mock_shell)
        command.console = Mock()

        mock_client = Mock()

        result = command.execute(mock_client, ["2.0", "invalid"])

        assert result == 1
        command.console.print.assert_called_with("Error: count must be a number")

    def test_execute_count_too_small(self):
        """Test execution with count too small."""
        mock_shell = Mock()
        command = IostatCommand(mock_shell)
        command.console = Mock()

        mock_client = Mock()

        result = command.execute(mock_client, ["2.0", "0"])

        assert result == 1
        command.console.print.assert_called_with("Error: count must be at least 1")

    @patch("pebble_shell.commands.system.parse_proc_diskstats")
    def test_execute_file_read_error(self, mock_parse_diskstats):
        """Test execution when file reading fails."""
        from pebble_shell.utils.proc_reader import ProcReadError

        mock_shell = Mock()
        command = IostatCommand(mock_shell)
        command.console = Mock()

        mock_client = Mock()
        mock_parse_diskstats.side_effect = ProcReadError("/proc/diskstats", "not found")

        result = command.execute(mock_client, [])

        # Should return error code and print error message
        assert result == 1
        command.console.print.assert_called_with(
            "[red]Error reading iostat data: Error reading /proc/diskstats: not found[/red]"
        )

    def test_execute_help(self):
        """Test help display."""
        mock_shell = Mock()
        command = IostatCommand(mock_shell)
        command.show_help = Mock()  # type: ignore[method-assign]

        mock_client = Mock()
        result = command.execute(mock_client, ["-h"])

        command.show_help.assert_called_once()  # type: ignore[attr-defined]
        assert result == 0

    def test_execute_empty_diskstats(self):
        """Test execution with empty diskstats file."""
        mock_shell = Mock()
        command = IostatCommand(mock_shell)
        command.console = Mock()

        mock_client = Mock()

        stat_content = "cpu  100000 1000 50000 800000 2000 0 1000"

        def mock_pull_side_effect(path: str):
            mock_context = MagicMock()
            mock_file = Mock()
            if path == "/proc/diskstats":
                mock_file.read.return_value = ""
            elif path == "/proc/stat":
                mock_file.read.return_value = stat_content
            else:
                raise ops.pebble.PathError("path", "not found")
            mock_context.__enter__.return_value = mock_file
            mock_context.__exit__.return_value = None
            return mock_context

        mock_client.pull.side_effect = mock_pull_side_effect

        result = command.execute(mock_client, [])

        # Should still succeed but show no devices
        assert result == 0
        assert command.console.print.call_count >= 1

    def test_execute_malformed_diskstats_lines(self):
        """Test execution with malformed diskstats lines."""
        mock_shell = Mock()
        command = IostatCommand(mock_shell)
        command.console = Mock()

        mock_client = Mock()

        # Mix of valid and invalid lines
        diskstats_content = """invalid line
   8       0 sda 1000 0 8000 100 2000 0 16000 200 0 300 300 0 0 0 0 0 0
short line
   8       1 sda1 2000 0 16000 200 4000 0 32000 400 0 600 600 0 0 0 0 0 0"""

        stat_content = "cpu  100000 1000 50000 800000 2000 0 1000"

        def mock_pull_side_effect(path: str):
            mock_context = MagicMock()
            mock_file = Mock()
            if path == "/proc/diskstats":
                mock_file.read.return_value = diskstats_content
            elif path == "/proc/stat":
                mock_file.read.return_value = stat_content
            else:
                raise ops.pebble.PathError("path", "not found")
            mock_context.__enter__.return_value = mock_file
            mock_context.__exit__.return_value = None
            return mock_context

        mock_client.pull.side_effect = mock_pull_side_effect

        result = command.execute(mock_client, [])

        # Should succeed and process valid lines while skipping invalid ones
        assert result == 0
        assert command.console.print.call_count >= 1


class TestDashboardCommand:
    """Test cases for DashboardCommand."""

    def test_execute_success(self):
        """Test successful dashboard launch."""
        mock_shell = Mock()
        command = DashboardCommand(mock_shell)
        command.console = Mock()

        mock_client = Mock()

        # Mock SystemDashboard to avoid actual dashboard launch
        with patch(
            "pebble_shell.commands.system.SystemDashboard"
        ) as mock_dashboard_class:
            mock_dashboard = Mock()
            mock_dashboard_class.return_value = mock_dashboard

            result = command.execute(mock_client, [])

        # Should succeed
        assert result == 0
        # Should have created and started dashboard
        mock_dashboard_class.assert_called_once_with(mock_shell)
        mock_dashboard.start.assert_called_once()
        # Should print startup messages
        assert command.console.print.call_count >= 4

    def test_execute_keyboard_interrupt(self):
        """Test dashboard with keyboard interrupt."""
        mock_shell = Mock()
        command = DashboardCommand(mock_shell)
        command.console = Mock()

        mock_client = Mock()

        # Mock SystemDashboard to raise KeyboardInterrupt
        with patch(
            "pebble_shell.commands.system.SystemDashboard"
        ) as mock_dashboard_class:
            mock_dashboard = Mock()
            mock_dashboard.start.side_effect = KeyboardInterrupt()
            mock_dashboard_class.return_value = mock_dashboard

            result = command.execute(mock_client, [])

        # Should succeed even with interrupt
        assert result == 0
        # Should print exit message
        command.console.print.assert_any_call("\n👋 Dashboard stopped.")

    def test_execute_exception(self):
        """Test dashboard with general exception."""
        mock_shell = Mock()
        command = DashboardCommand(mock_shell)
        command.console = Mock()

        mock_client = Mock()

        # Mock SystemDashboard to raise Exception
        with patch(
            "pebble_shell.commands.system.SystemDashboard"
        ) as mock_dashboard_class:
            mock_dashboard_class.side_effect = Exception("Dashboard error")

            result = command.execute(mock_client, [])

        # Should return error code
        assert result == 1
        # Should print error message
        command.console.print.assert_any_call(
            "Error starting dashboard: Dashboard error"
        )

    def test_execute_help(self):
        """Test help display."""
        mock_shell = Mock()
        command = DashboardCommand(mock_shell)
        command.show_help = Mock()  # type: ignore[method-assign]

        mock_client = Mock()
        result = command.execute(mock_client, ["-h"])

        command.show_help.assert_called_once()  # type: ignore[attr-defined]
        assert result == 0


class TestCpuinfoCommand:
    """Test cases for CpuinfoCommand."""

    def test_execute_success_default(self):
        """Test successful execution with default parameters."""
        mock_shell = Mock()
        command = CpuinfoCommand(mock_shell)
        command.console = Mock()

        mock_client = Mock()

        # Mock realistic cpuinfo content based on real Ubuntu system
        cpuinfo_content = """processor	: 0
BogoMIPS	: 48.00
Features	: fp asimd evtstrm aes pmull sha1 sha2 crc32 atomics fphp asimdhp cpuid asimdrdm
CPU implementer	: 0x61
CPU architecture: 8
CPU variant	: 0x0
CPU part	: 0x000
CPU revision	: 0
model name	: ARMv8 Processor
cpu cores	: 2
cache size	: 1024 KB

processor	: 1
BogoMIPS	: 48.00
Features	: fp asimd evtstrm aes pmull sha1 sha2 crc32 atomics fphp asimdhp cpuid asimdrdm
CPU implementer	: 0x61
CPU architecture: 8
CPU variant	: 0x0
CPU part	: 0x000
CPU revision	: 0
model name	: ARMv8 Processor
cpu cores	: 2
cache size	: 1024 KB"""

        def mock_pull_side_effect(path: str):
            mock_context = MagicMock()
            mock_file = Mock()
            if path == "/proc/cpuinfo":
                mock_file.read.return_value = cpuinfo_content
            else:
                raise ops.pebble.PathError("path", "not found")
            mock_context.__enter__.return_value = mock_file
            mock_context.__exit__.return_value = None
            return mock_context

        mock_client.pull.side_effect = mock_pull_side_effect

        result = command.execute(mock_client, [])

        # Should succeed
        assert result == 0
        # Should print CPU info (at least one print call)
        assert command.console.print.call_count >= 1

    def test_execute_compact_format(self):
        """Test execution with compact format."""
        mock_shell = Mock()
        command = CpuinfoCommand(mock_shell)
        command.console = Mock()

        mock_client = Mock()

        cpuinfo_content = """processor	: 0
model name	: ARMv8 Processor
cpu cores	: 2
cache size	: 1024 KB"""

        def mock_pull_side_effect(path: str):
            mock_context = MagicMock()
            mock_file = Mock()
            if path == "/proc/cpuinfo":
                mock_file.read.return_value = cpuinfo_content
            else:
                raise ops.pebble.PathError("path", "not found")
            mock_context.__enter__.return_value = mock_file
            mock_context.__exit__.return_value = None
            return mock_context

        mock_client.pull.side_effect = mock_pull_side_effect

        result = command.execute(mock_client, ["-c"])

        assert result == 0
        assert command.console.print.call_count >= 1

    def test_execute_topology_format(self):
        """Test execution with topology format."""
        mock_shell = Mock()
        command = CpuinfoCommand(mock_shell)
        command.console = Mock()

        mock_client = Mock()

        cpuinfo_content = """processor	: 0
physical id	: 0
core id	: 0
siblings	: 2
core siblings	: 2"""

        def mock_pull_side_effect(path: str):
            mock_context = MagicMock()
            mock_file = Mock()
            if path == "/proc/cpuinfo":
                mock_file.read.return_value = cpuinfo_content
            else:
                raise ops.pebble.PathError("path", "not found")
            mock_context.__enter__.return_value = mock_file
            mock_context.__exit__.return_value = None
            return mock_context

        mock_client.pull.side_effect = mock_pull_side_effect

        result = command.execute(mock_client, ["-t"])

        assert result == 0
        assert command.console.print.call_count >= 1

    def test_execute_all_cpus(self):
        """Test execution showing all CPUs."""
        mock_shell = Mock()
        command = CpuinfoCommand(mock_shell)
        command.console = Mock()

        mock_client = Mock()

        cpuinfo_content = "processor	: 0\nprocessor	: 1\n"

        def mock_pull_side_effect(path: str):
            mock_context = MagicMock()
            mock_file = Mock()
            if path == "/proc/cpuinfo":
                mock_file.read.return_value = cpuinfo_content
            else:
                raise ops.pebble.PathError("path", "not found")
            mock_context.__enter__.return_value = mock_file
            mock_context.__exit__.return_value = None
            return mock_context

        mock_client.pull.side_effect = mock_pull_side_effect

        result = command.execute(mock_client, ["-a"])

        assert result == 0
        assert command.console.print.call_count >= 1

    @patch("pebble_shell.commands.system.parse_proc_cpuinfo")
    def test_execute_file_read_error(self, mock_parse_cpuinfo):
        """Test execution when file reading fails."""
        from pebble_shell.utils.proc_reader import ProcReadError

        mock_shell = Mock()
        command = CpuinfoCommand(mock_shell)
        command.console = Mock()

        mock_client = Mock()
        mock_parse_cpuinfo.side_effect = ProcReadError("/proc/cpuinfo", "not found")

        result = command.execute(mock_client, [])

        # Should return error code and print error message
        assert result == 1
        command.console.print.assert_called_with(
            "Error reading CPU information: Error reading /proc/cpuinfo: not found"
        )

    def test_execute_help(self):
        """Test help display."""
        mock_shell = Mock()
        command = CpuinfoCommand(mock_shell)
        command.show_help = Mock()  # type: ignore[method-assign]

        mock_client = Mock()
        result = command.execute(mock_client, ["-h"])

        command.show_help.assert_called_once()  # type: ignore[attr-defined]
        assert result == 0


class TestMeminfoCommand:
    """Test cases for MeminfoCommand."""

    def test_execute_success_default(self):
        """Test successful execution with default parameters."""
        mock_shell = Mock()
        command = MeminfoCommand(mock_shell)
        command.console = Mock()

        mock_client = Mock()

        # Mock realistic meminfo content based on real Ubuntu system
        meminfo_content = """MemTotal:        3996072 kB
MemFree:          216540 kB
MemAvailable:    2605496 kB
Buffers:           98856 kB
Cached:          2369028 kB
SwapCached:            0 kB
Active:          1386728 kB
Inactive:        1860300 kB
SwapTotal:             0 kB
SwapFree:              0 kB
Dirty:               120 kB
Writeback:             0 kB
AnonPages:        805760 kB
Mapped:           449012 kB
Shmem:             35504 kB"""

        def mock_pull_side_effect(path: str):
            mock_context = MagicMock()
            mock_file = Mock()
            if path == "/proc/meminfo":
                mock_file.read.return_value = meminfo_content
            else:
                raise ops.pebble.PathError("path", "not found")
            mock_context.__enter__.return_value = mock_file
            mock_context.__exit__.return_value = None
            return mock_context

        mock_client.pull.side_effect = mock_pull_side_effect

        result = command.execute(mock_client, [])

        # Should succeed
        assert result == 0
        # Should print memory info
        assert command.console.print.call_count >= 1

    @patch("pebble_shell.commands.system.parse_proc_meminfo")
    def test_execute_file_read_error(self, mock_parse_meminfo):
        """Test execution when file reading fails."""
        from pebble_shell.utils.proc_reader import ProcReadError

        mock_shell = Mock()
        command = MeminfoCommand(mock_shell)
        command.console = Mock()

        mock_client = Mock()
        mock_parse_meminfo.side_effect = ProcReadError("/proc/meminfo", "not found")

        result = command.execute(mock_client, [])

        # Should return error code and print error message
        assert result == 1
        command.console.print.assert_called_with(
            "Error reading memory information: Error reading /proc/meminfo: not found"
        )

    def test_execute_help(self):
        """Test help display."""
        mock_shell = Mock()
        command = MeminfoCommand(mock_shell)
        command.show_help = Mock()  # type: ignore[method-assign]

        mock_client = Mock()
        result = command.execute(mock_client, ["-h"])

        command.show_help.assert_called_once()  # type: ignore[attr-defined]
        assert result == 0


class TestFdinfoCommand:
    """Test cases for FdinfoCommand."""

    def test_execute_success_default(self):
        """Test successful execution with default parameters."""
        mock_shell = Mock()
        command = FdinfoCommand(mock_shell)
        command.console = Mock()

        mock_client = Mock()

        # Mock /proc/self/fd directory listing
        fd_entry1 = Mock()
        fd_entry1.name = "0"
        fd_entry2 = Mock()
        fd_entry2.name = "1"
        fd_entry3 = Mock()
        fd_entry3.name = "2"
        mock_client.list_files.return_value = [fd_entry1, fd_entry2, fd_entry3]

        # Mock the context manager for fdinfo files
        mock_file = Mock()
        mock_file.read.return_value = "pos:\t0\nflags:\t0100000\nmnt_id:\t123"
        mock_context_manager = MagicMock()
        mock_context_manager.__enter__.return_value = mock_file
        mock_context_manager.__exit__.return_value = None
        mock_client.pull.return_value = mock_context_manager

        result = command.execute(mock_client, [])

        # Should succeed
        assert result == 0
        # Should print file descriptor info
        assert command.console.print.call_count >= 1

    def test_execute_with_pid(self):
        """Test execution with specific PID."""
        mock_shell = Mock()
        command = FdinfoCommand(mock_shell)
        command.console = Mock()

        mock_client = Mock()

        # Mock /proc/1234/fd directory listing
        fd_entry1 = Mock()
        fd_entry1.name = "0"
        fd_entry2 = Mock()
        fd_entry2.name = "1"
        mock_client.list_files.return_value = [fd_entry1, fd_entry2]

        # Mock the context manager for fdinfo files
        mock_file = Mock()
        mock_file.read.return_value = "pos:\t0\nflags:\t0100000\nmnt_id:\t123"
        mock_context_manager = MagicMock()
        mock_context_manager.__enter__.return_value = mock_file
        mock_context_manager.__exit__.return_value = None
        mock_client.pull.return_value = mock_context_manager

        result = command.execute(mock_client, ["1234"])

        # Should succeed
        assert result == 0
        # Should have called list_files with specific PID
        mock_client.list_files.assert_called_with("/proc/1234/fd")

    def test_execute_invalid_pid(self):
        """Test execution with invalid PID."""
        mock_shell = Mock()
        command = FdinfoCommand(mock_shell)
        command.console = Mock()

        mock_client = Mock()
        mock_client.list_files.side_effect = ops.pebble.PathError("path", "not found")

        result = command.execute(mock_client, ["invalid"])

        # Should succeed but print error message
        assert result == 0
        command.console.print.assert_called_with("No file descriptors found.")

    def test_execute_proc_read_error(self):
        """Test error when /proc cannot be read."""
        mock_shell = Mock()
        command = FdinfoCommand(mock_shell)
        command.console = Mock()

        mock_client = Mock()
        mock_client.list_files.side_effect = ops.pebble.PathError("path", "not found")

        result = command.execute(mock_client, [])

        # Should succeed but print error message
        assert result == 0
        # Should print error message
        command.console.print.assert_called_with("No file descriptors found.")

    def test_execute_help(self):
        """Test help display."""
        mock_shell = Mock()
        command = FdinfoCommand(mock_shell)
        command.show_help = Mock()  # type: ignore[method-assign]

        mock_client = Mock()
        result = command.execute(mock_client, ["-h"])

        command.show_help.assert_called_once()  # type: ignore[attr-defined]
        assert result == 0


class TestSyslogCommand:
    """Test cases for SyslogCommand."""

    def test_execute_success_default(self):
        """Test successful execution with default parameters."""
        mock_shell = Mock()
        command = SyslogCommand(mock_shell)
        command.console = Mock()

        mock_client = Mock()

        # Mock syslog content
        syslog_content = """Jan 15 10:30:15 hostname systemd[1]: Started System Logging Service.
Jan 15 10:30:16 hostname kernel: [    0.000000] Linux version 5.4.0
Jan 15 10:30:17 hostname sshd[1234]: Server listening on 0.0.0.0 port 22.
Jan 15 10:30:18 hostname NetworkManager[567]: <info> startup complete
Jan 15 10:30:19 hostname cron[890]: (CRON) INFO (pidfile fd = 3)"""

        def mock_pull_side_effect(path: str):
            mock_context = MagicMock()
            mock_file = Mock()
            if path == "/var/log/syslog":
                mock_file.read.return_value = syslog_content
            else:
                # Try other log files
                raise ops.pebble.PathError("path", "not found")
            mock_context.__enter__.return_value = mock_file
            mock_context.__exit__.return_value = None
            return mock_context

        mock_client.pull.side_effect = mock_pull_side_effect

        result = command.execute(mock_client, [])

        # Should succeed
        assert result == 0
        # Should print syslog entries
        assert command.console.print.call_count >= 1

    def test_execute_with_lines_limit(self):
        """Test execution with lines limit."""
        mock_shell = Mock()
        command = SyslogCommand(mock_shell)
        command.console = Mock()

        mock_client = Mock()

        # Mock syslog with many lines
        syslog_lines = [
            f"Jan 15 10:30:{i:02d} hostname test[123]: Log entry {i}"
            for i in range(100)
        ]
        syslog_content = "\n".join(syslog_lines)

        def mock_pull_side_effect(path: str):
            mock_context = MagicMock()
            mock_file = Mock()
            if path == "/var/log/syslog":
                mock_file.read.return_value = syslog_content
            else:
                raise ops.pebble.PathError("path", "not found")
            mock_context.__enter__.return_value = mock_file
            mock_context.__exit__.return_value = None
            return mock_context

        mock_client.pull.side_effect = mock_pull_side_effect

        result = command.execute(mock_client, ["10"])

        # Should succeed
        assert result == 0
        # Should print limited entries
        assert command.console.print.call_count >= 1

    def test_execute_follow_mode(self):
        """Test execution in follow mode."""
        mock_shell = Mock()
        command = SyslogCommand(mock_shell)
        command.console = Mock()

        mock_client = Mock()

        syslog_content = "Jan 15 10:30:15 hostname test[123]: Sample log entry"

        def mock_pull_side_effect(path: str):
            mock_context = MagicMock()
            mock_file = Mock()
            if path == "/var/log/syslog":
                mock_file.read.return_value = syslog_content
            else:
                raise ops.pebble.PathError("path", "not found")
            mock_context.__enter__.return_value = mock_file
            mock_context.__exit__.return_value = None
            return mock_context

        mock_client.pull.side_effect = mock_pull_side_effect

        # Mock KeyboardInterrupt to exit follow mode
        with patch("time.sleep", side_effect=KeyboardInterrupt):
            result = command.execute(mock_client, ["-f"])

        # Should succeed even with interrupt
        assert result == 0
        # Should print entries and exit message
        assert command.console.print.call_count >= 1

    def test_execute_no_log_files(self):
        """Test execution when no log files are found."""
        mock_shell = Mock()
        command = SyslogCommand(mock_shell)
        command.console = Mock()

        mock_client = Mock()

        def mock_pull_side_effect(path: str):
            # All log files not found
            raise ops.pebble.PathError("path", "not found")

        mock_client.pull.side_effect = mock_pull_side_effect

        result = command.execute(mock_client, [])

        # Should return error code
        assert result == 1
        # Should print no logs found message
        assert command.console.print.call_count >= 1

    def test_execute_invalid_lines_number(self):
        """Test execution with invalid lines number."""
        mock_shell = Mock()
        command = SyslogCommand(mock_shell)
        command.console = Mock()

        mock_client = Mock()

        # Mock the context manager for log files
        mock_file = Mock()
        mock_file.read.return_value = "Sample log content"
        mock_context_manager = MagicMock()
        mock_context_manager.__enter__.return_value = mock_file
        mock_context_manager.__exit__.return_value = None
        mock_client.pull.return_value = mock_context_manager

        result = command.execute(mock_client, ["-n", "invalid"])

        # Should return error code for invalid number
        assert result == 1
        command.console.print.assert_called_with("[red]Invalid number for -n[/red]")

    def test_execute_help(self):
        """Test help display."""
        mock_shell = Mock()
        command = SyslogCommand(mock_shell)
        command.show_help = Mock()  # type: ignore[method-assign]

        mock_client = Mock()
        result = command.execute(mock_client, ["-h"])

        command.show_help.assert_called_once()  # type: ignore[attr-defined]
        assert result == 0
