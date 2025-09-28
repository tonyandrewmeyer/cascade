"""Tests for ProcReader class."""

from unittest.mock import MagicMock, Mock, mock_open, patch

import pytest

from pebble_shell.commands.pebble_top import PebbleTopViewer, ProcessInfo, ProcReader
from pebble_shell.utils.formatting import format_bytes, format_time


class TestProcReader:
    """Test cases for ProcReader class."""

    @pytest.fixture
    def mock_client(self):
        """Create mock Pebble client."""
        client = Mock()
        mock_file = MagicMock()
        mock_file.read.return_value = "btime 1640995200\n"

        # Create a proper context manager mock
        context_manager = MagicMock()
        context_manager.__enter__.return_value = mock_file
        context_manager.__exit__.return_value = None
        client.pull.return_value = context_manager
        return client

    @pytest.fixture
    def proc_reader(self, mock_client):
        """Create ProcReader instance."""
        return ProcReader(mock_client)

    def test_init(self, proc_reader):
        """Test ProcReader initialization."""
        assert proc_reader.last_cpu_stats == {}
        assert proc_reader.last_system_stats is None
        assert proc_reader.boot_time >= 0
        assert proc_reader.clock_ticks > 0

    def test_get_boot_time(self, proc_reader):
        """Test getting boot time."""
        # Mock the client to return stat data
        mock_file = MagicMock()
        mock_file.read.return_value = "cpu 12345 0 5678 90123\nbtime 1640995200\n"
        context_manager = MagicMock()
        context_manager.__enter__.return_value = mock_file
        context_manager.__exit__.return_value = None
        proc_reader._client.pull.return_value = context_manager

        boot_time = proc_reader._get_boot_time()
        assert boot_time == 1640995200

    @patch("builtins.open", mock_open(read_data="btime invalid\n"))
    def test_get_boot_time_invalid(self, proc_reader):
        """Test getting boot time with invalid data."""
        # Mock the client.pull to return the invalid data
        mock_file = MagicMock()
        mock_file.read.return_value = "btime invalid\n"
        context_manager = MagicMock()
        context_manager.__enter__.return_value = mock_file
        context_manager.__exit__.return_value = None
        proc_reader._client.pull.return_value = context_manager

        boot_time = proc_reader._get_boot_time()
        assert boot_time == 0

    @patch("builtins.open", mock_open(read_data="cpu  100 200 300 400 500\n"))
    def test_get_system_cpu_stats(self, proc_reader):
        """Test getting system CPU stats."""
        # Mock the client.pull to return the CPU data
        mock_file = MagicMock()
        mock_file.read.return_value = "cpu  100 200 300 400 500\n"
        context_manager = MagicMock()
        context_manager.__enter__.return_value = mock_file
        context_manager.__exit__.return_value = None
        proc_reader._client.pull.return_value = context_manager

        total, idle = proc_reader._get_system_cpu_stats()
        assert total == 1000  # 100 + 200 + 300 + 400
        assert idle == 400

    @patch("builtins.open", mock_open(read_data="invalid line\n"))
    def test_get_system_cpu_stats_invalid(self, proc_reader):
        """Test getting system CPU stats with invalid data."""
        total, idle = proc_reader._get_system_cpu_stats()
        assert total == 0
        assert idle == 0

    @patch(
        "builtins.open",
        mock_open(read_data="MemTotal: 16777216 kB\nMemAvailable: 8388608 kB\n"),
    )
    def test_get_memory_info(self, proc_reader):
        """Test getting memory information."""
        # Mock the client.pull to return the memory data
        mock_file = MagicMock()
        mock_file.read.return_value = (
            "MemTotal: 16777216 kB\nMemAvailable: 8388608 kB\n"
        )
        context_manager = MagicMock()
        context_manager.__enter__.return_value = mock_file
        context_manager.__exit__.return_value = None
        proc_reader._client.pull.return_value = context_manager

        total, available = proc_reader.get_memory_info()
        assert total == 16777216
        assert available == 8388608

    @patch("builtins.open", mock_open(read_data="invalid data\n"))
    def test_get_memory_info_invalid(self, proc_reader):
        """Test getting memory info with invalid data."""
        # Mock the client.pull to return invalid data
        mock_file = MagicMock()
        mock_file.read.return_value = "invalid data\n"
        context_manager = MagicMock()
        context_manager.__enter__.return_value = mock_file
        context_manager.__exit__.return_value = None
        proc_reader._client.pull.return_value = context_manager

        total, available = proc_reader.get_memory_info()
        assert total == 0
        assert available == 0

    @patch("pathlib.Path.exists", return_value=False)
    def test_get_process_info_not_exists(self, _mock_exists, proc_reader):
        """Test getting process info for non-existent process."""
        result = proc_reader._get_process_info(99999)
        assert result is None

    def test_get_process_info_invalid_stat(self, proc_reader):
        """Test getting process info with invalid stat data."""
        # Mock the client.pull to return invalid stat data (not enough fields - only 10 instead of 44+ required)
        mock_file = MagicMock()
        mock_file.read.return_value = "1 (init) S 0 1 1 0 -1 4194560 0"
        context_manager = MagicMock()
        context_manager.__enter__.return_value = mock_file
        context_manager.__exit__.return_value = None
        proc_reader._client.pull.return_value = context_manager

        result = proc_reader._get_process_info(1)
        assert result is None

    def test_get_process_info_valid(self, proc_reader):
        """Test getting process info with valid data."""
        # Mock file contents
        stat_data = "1 (systemd) S 0 1 1 0 -1 4194560 0 0 0 0 10 5 0 0 20 0 1 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0"
        status_data = "VmRSS:\t1024 kB\n"
        cmdline_data = "/sbin/init\x00"

        # Configure mocks for multiple file reads
        def mock_pull_side_effect(path):
            mock_file = MagicMock()
            context_manager = MagicMock()
            context_manager.__enter__.return_value = mock_file
            context_manager.__exit__.return_value = None

            if path == "/proc/1/stat":
                mock_file.read.return_value = stat_data
            elif path == "/proc/1/status":
                mock_file.read.return_value = status_data
            elif path == "/proc/1/cmdline":
                mock_file.read.return_value = cmdline_data
            elif path == "/proc/meminfo":
                mock_file.read.return_value = (
                    "MemTotal: 16777216 kB\nMemAvailable: 8388608 kB\n"
                )
            else:
                # For any other path, simulate file not found
                raise Exception("File not found")

            return context_manager

        proc_reader._client.pull.side_effect = mock_pull_side_effect

        result = proc_reader._get_process_info(1)

        assert result is not None
        assert result.pid == 1
        assert result.name == "systemd"
        assert result.state == "S"
        assert result.ppid == 0
        assert result.user == "root"
        assert result.memory_kb == 1024
        assert result.cmdline == "/sbin/init"

    @patch.object(ProcReader, "_get_process_info")
    def test_get_all_processes(self, mock_get_process_info, proc_reader):
        """Test getting all processes."""
        # Mock the client.list_files to return directory entries
        mock_entry_1 = MagicMock()
        mock_entry_1.name = "1"
        mock_entry_2 = MagicMock()
        mock_entry_2.name = "2"
        mock_entry_invalid = MagicMock()
        mock_entry_invalid.name = "invalid"

        proc_reader._client.list_files.return_value = [
            mock_entry_1,
            mock_entry_2,
            mock_entry_invalid,
        ]

        # Mock process info
        proc1 = ProcessInfo(
            pid=1,
            ppid=0,
            name="init",
            state="S",
            cpu_percent=0.1,
            memory_percent=0.5,
            memory_kb=1024,
            user="root",
            priority=20,
            nice=0,
            threads=1,
            start_time=0,
            cpu_time=100,
            cmdline="/sbin/init",
        )
        proc2 = ProcessInfo(
            pid=2,
            ppid=0,
            name="kthreadd",
            state="S",
            cpu_percent=0.0,
            memory_percent=0.0,
            memory_kb=0,
            user="root",
            priority=20,
            nice=0,
            threads=1,
            start_time=0,
            cpu_time=50,
            cmdline="[kthreadd]",
        )

        # Set up side effect - return process info for valid PIDs, None for invalid
        def get_process_side_effect(pid):
            if pid == 1:
                return proc1
            if pid == 2:
                return proc2
            return None

        mock_get_process_info.side_effect = get_process_side_effect

        processes = proc_reader.get_all_processes()

        assert len(processes) == 2
        assert processes[0].pid == 1
        assert processes[1].pid == 2

        # Should have called _get_process_info for valid PIDs only
        mock_get_process_info.assert_any_call(1)
        mock_get_process_info.assert_any_call(2)
        assert mock_get_process_info.call_count == 2


class TestTopViewer:
    """Test cases for PebbleTop class."""

    @pytest.fixture
    def pebble_top(self):
        """Create PebbleTop instance."""
        mock_client = Mock()
        mock_file = MagicMock()
        mock_file.read.return_value = "cpu  0 0 0 0 0 0 0 0 0 0\nbtime 1234567890\n"
        mock_client.pull.return_value = MagicMock()
        mock_client.pull.return_value.__enter__.return_value = mock_file
        mock_client.pull.return_value.__exit__.return_value = None
        return PebbleTopViewer(mock_client)

    def test_init(self, pebble_top):
        """Test PebbleTop initialization."""
        assert pebble_top.sort_column == "cpu_percent"
        assert pebble_top.sort_reverse is True
        assert pebble_top.show_threads is False
        assert pebble_top.running is True

    def test_format_memory(self):
        """Test memory formatting."""
        assert format_bytes(512) == "512.0B"
        assert format_bytes(1536) == "1536.0KB"
        assert format_bytes(1048576) == "1048576.0MB"
        assert format_bytes(2097152) == "2097152.0MB"

    def test_format_time(self):
        """Test time formatting."""
        assert format_time(0) == "00:00:00"
        assert format_time(65) == "00:01:05"
        assert format_time(3661) == "01:01:01"
        assert format_time(90061) == "25:01:01"

    def test_draw_header(self, pebble_top, monkeypatch):
        """Test drawing header."""
        # Mock curses screen
        mock_stdscr = MagicMock()
        mock_stdscr.getmaxyx.return_value = (24, 80)

        # Mock file reads through client.pull
        def mock_pull_side_effect(path):
            mock_file = MagicMock()
            if path == "/proc/uptime":
                mock_file.read.return_value = "12345.67 54321.89\n"
            elif path == "/proc/loadavg":
                mock_file.read.return_value = "0.15 0.25 0.35 1/234 5678\n"
            else:
                raise FileNotFoundError()

            context_manager = MagicMock()
            context_manager.__enter__.return_value = mock_file
            context_manager.__exit__.return_value = None
            return context_manager

        pebble_top._client.pull.side_effect = mock_pull_side_effect

        # Mock memory info
        monkeypatch.setattr(
            pebble_top.proc_reader, "get_memory_info", lambda: (16777216, 8388608)
        )

        processes = []

        # Mock curses functions to avoid actual curses calls
        with patch("curses.color_pair"), patch("curses.A_BOLD"):
            pebble_top.draw_header(mock_stdscr, processes)

        # Verify addstr was called for header lines
        assert mock_stdscr.addstr.call_count >= 4

    def test_draw_processes_cpu_sort(self, pebble_top):
        """Test drawing processes sorted by CPU."""
        # Mock curses screen
        mock_stdscr = MagicMock()
        mock_stdscr.getmaxyx.return_value = (24, 80)

        # Create test processes
        processes = [
            ProcessInfo(
                pid=1,
                ppid=0,
                name="init",
                state="S",
                cpu_percent=0.1,
                memory_percent=0.5,
                memory_kb=1024,
                user="root",
                priority=20,
                nice=0,
                threads=1,
                start_time=0,
                cpu_time=100,
                cmdline="/sbin/init",
            ),
            ProcessInfo(
                pid=2,
                ppid=0,
                name="cpu_hog",
                state="R",
                cpu_percent=50.0,
                memory_percent=10.0,
                memory_kb=102400,
                user="root",
                priority=20,
                nice=0,
                threads=1,
                start_time=0,
                cpu_time=5000,
                cmdline="cpu_intensive_app",
            ),
        ]

        pebble_top.sort_column = "cpu_percent"
        pebble_top.sort_reverse = True

        # Mock curses functions to avoid actual curses calls
        with patch("curses.color_pair") as mock_color_pair:
            mock_color_pair.return_value = 1
            pebble_top.draw_processes(mock_stdscr, processes)

        # Should have drawn at least the processes
        assert mock_stdscr.addstr.call_count >= 2

    def test_draw_processes_memory_sort(self, pebble_top):
        """Test drawing processes sorted by memory."""
        mock_stdscr = MagicMock()
        mock_stdscr.getmaxyx.return_value = (24, 80)

        processes = [
            ProcessInfo(
                pid=1,
                ppid=0,
                name="init",
                state="S",
                cpu_percent=0.1,
                memory_percent=0.5,
                memory_kb=1024,
                user="root",
                priority=20,
                nice=0,
                threads=1,
                start_time=0,
                cpu_time=100,
                cmdline="/sbin/init",
            ),
            ProcessInfo(
                pid=2,
                ppid=0,
                name="mem_hog",
                state="S",
                cpu_percent=1.0,
                memory_percent=50.0,
                memory_kb=1048576,
                user="user",
                priority=20,
                nice=0,
                threads=1,
                start_time=0,
                cpu_time=1000,
                cmdline="memory_intensive_app",
            ),
        ]

        pebble_top.sort_column = "memory_percent"
        pebble_top.sort_reverse = True

        # Mock curses functions to avoid actual curses calls
        with patch("curses.color_pair") as mock_color_pair:
            mock_color_pair.return_value = 1
            pebble_top.draw_processes(mock_stdscr, processes)

        assert mock_stdscr.addstr.call_count >= 2

    def test_draw_help(self, pebble_top):
        """Test drawing help screen."""
        mock_stdscr = MagicMock()
        mock_stdscr.getmaxyx.return_value = (24, 80)
        mock_stdscr.getch.return_value = ord("q")

        pebble_top.draw_help(mock_stdscr)

        # Should clear screen, draw help text, and wait for input
        mock_stdscr.clear.assert_called_once()
        mock_stdscr.refresh.assert_called_once()
        mock_stdscr.getch.assert_called_once()
        assert mock_stdscr.addstr.call_count > 10  # Many help lines
