# tests/unit/test_proc_reader.py
"""Tests for ProcReader class."""

from unittest.mock import MagicMock, Mock, mock_open, patch

import pytest

from pebble_shell.commands.pebble_top import PebbleTopViewer, ProcessInfo, ProcReader


class TestProcReader:
    """Test cases for ProcReader class."""

    @pytest.fixture
    def mock_client(self):
        """Create mock Pebble client."""
        client = Mock()
        mock_file = MagicMock()
        mock_file.read.return_value = "btime 1640995200\n"
        client.pull.return_value.__enter__.return_value = mock_file
        client.pull.return_value.__exit__.return_value = None
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

    @patch("builtins.open", mock_open(read_data="btime 1640995200\n"))
    def test_get_boot_time(self, proc_reader):
        """Test getting boot time."""
        boot_time = proc_reader._get_boot_time()
        assert boot_time == 1640995200

    @patch("builtins.open", mock_open(read_data="btime invalid\n"))
    def test_get_boot_time_invalid(self, proc_reader):
        """Test getting boot time with invalid data."""
        boot_time = proc_reader._get_boot_time()
        assert boot_time == 0

    @patch("builtins.open", mock_open(read_data="cpu  100 200 300 400 500\n"))
    def test_get_system_cpu_stats(self, proc_reader):
        """Test getting system CPU stats."""
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
        total, available = proc_reader._get_memory_info()
        assert total == 16777216
        assert available == 8388608

    @patch("builtins.open", mock_open(read_data="invalid data\n"))
    def test_get_memory_info_invalid(self, proc_reader):
        """Test getting memory info with invalid data."""
        total, available = proc_reader._get_memory_info()
        assert total == 0
        assert available == 0

    @patch("pathlib.Path.exists", return_value=False)
    def test_get_process_info_not_exists(self, mock_exists, proc_reader):
        """Test getting process info for non-existent process."""
        result = proc_reader._get_process_info(99999)
        assert result is None

    @patch("pathlib.Path.exists", return_value=True)
    @patch(
        "builtins.open",
        mock_open(
            read_data="1 (init) S 0 1 1 0 -1 4194560 0 0 0 0 0 0 0 0 20 0 1 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0"
        ),
    )
    def test_get_process_info_invalid_stat(
        self, mock_open_func, mock_exists, proc_reader
    ):
        """Test getting process info with invalid stat data."""
        result = proc_reader._get_process_info(1)
        assert result is None

    @patch("pathlib.Path.exists", return_value=True)
    @patch("builtins.open")
    @patch("pathlib.Path.stat")
    @patch("pwd.getpwuid")
    def test_get_process_info_valid(
        self, mock_getpwuid, mock_stat, mock_open_func, mock_exists, proc_reader
    ):
        """Test getting process info with valid data."""
        # Mock file contents
        stat_data = "1 (systemd) S 0 1 1 0 -1 4194560 0 0 0 0 10 5 0 0 20 0 1 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0"
        status_data = "VmRSS:\t1024 kB\n"
        cmdline_data = "/sbin/init\x00"

        # Configure mocks
        mock_files = {
            "/proc/1/stat": stat_data,
            "/proc/1/status": status_data,
            "/proc/1/cmdline": cmdline_data,
        }

        def mock_open_side_effect(filename, mode="r"):
            if str(filename) in mock_files:
                return mock_open(read_data=mock_files[str(filename)])()
            raise FileNotFoundError()

        mock_open_func.side_effect = mock_open_side_effect

        # Mock user lookup
        mock_user = type("User", (), {"pw_name": "root"})()
        mock_getpwuid.return_value = mock_user

        # Mock file stats
        mock_stat_result = type("Stat", (), {"st_uid": 0})()
        mock_stat.return_value = mock_stat_result

        result = proc_reader._get_process_info(1)

        assert result is not None
        assert result.pid == 1
        assert result.name == "systemd"
        assert result.state == "S"
        assert result.ppid == 0
        assert result.user == "root"
        assert result.memory_kb == 1024
        assert result.cmdline == "/sbin/init"

    @patch("pathlib.Path.iterdir")
    @patch.object(ProcReader, "_get_process_info")
    def test_get_all_processes(self, mock_get_process_info, mock_iterdir, proc_reader):
        """Test getting all processes."""
        # Mock /proc directory contents
        mock_dirs = [
            type("Path", (), {"is_dir": lambda: True, "name": "1"})(),
            type("Path", (), {"is_dir": lambda: True, "name": "2"})(),
            type("Path", (), {"is_dir": lambda: True, "name": "invalid"})(),
            type("Path", (), {"is_dir": lambda: False, "name": "3"})(),
        ]
        mock_iterdir.return_value = mock_dirs

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

        mock_get_process_info.side_effect = [proc1, proc2]

        processes = proc_reader.get_all_processes()

        assert len(processes) == 2
        assert processes[0].pid == 1
        assert processes[1].pid == 2

        # Should have called _get_process_info for valid PIDs only
        mock_get_process_info.assert_any_call(1)
        mock_get_process_info.assert_any_call(2)
        assert mock_get_process_info.call_count == 2


class TestPebbleTop:
    """Test cases for PebbleTop class."""

    @pytest.fixture
    def mock_client(self):
        """Create a mock Pebble client."""
        return Mock()

    @pytest.fixture
    def pebble_top(self, mock_client):
        """Create PebbleTop instance."""
        return PebbleTopViewer(mock_client)

    def test_init(self, pebble_top):
        """Test PebbleTop initialization."""
        assert pebble_top.sort_column == "cpu_percent"
        assert pebble_top.sort_reverse is True
        assert pebble_top.show_threads is False
        assert pebble_top.running is True

    def test_format_memory(self, pebble_top):
        """Test memory formatting."""
        assert pebble_top.format_memory(512) == "512K"
        assert pebble_top.format_memory(1536) == "1.5M"
        assert pebble_top.format_memory(1048576) == "1.0G"
        assert pebble_top.format_memory(2097152) == "2.0G"

    def test_format_time(self, pebble_top):
        """Test time formatting."""
        assert pebble_top.format_time(0) == "00:00:00"
        assert pebble_top.format_time(65) == "00:01:05"
        assert pebble_top.format_time(3661) == "01:01:01"
        assert pebble_top.format_time(90061) == "25:01:01"

    def test_draw_header(self, pebble_top, monkeypatch):
        """Test drawing header."""
        # Mock curses screen
        mock_stdscr = MagicMock()
        mock_stdscr.getmaxyx.return_value = (24, 80)

        # Mock /proc files
        uptime_data = "12345.67 54321.89\n"
        loadavg_data = "0.15 0.25 0.35 1/234 5678\n"

        with patch("builtins.open") as mock_open:
            mock_files = {
                "/proc/uptime": uptime_data,
                "/proc/loadavg": loadavg_data,
            }

            def mock_open_side_effect(filename, mode="r"):
                from unittest.mock import mock_open as mock_open_func

                if filename in mock_files:
                    return mock_open_func(read_data=mock_files[filename])()
                raise FileNotFoundError()

            mock_open.side_effect = mock_open_side_effect

            # Mock memory info
            monkeypatch.setattr(
                pebble_top.proc_reader, "_get_memory_info", lambda: (16777216, 8388608)
            )

            processes = []
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
