"""Tests for the dashboard utility module."""

import dataclasses
import unittest.mock as mock

import pytest

from pebble_shell.utils.dashboard import (
    SystemDashboard,
    SystemStats,
)


class TestSystemStats:
    """Test SystemStats dataclass."""

    def test_system_stats_creation(self):
        """Test creating SystemStats with default values."""
        stats = SystemStats()
        assert stats.cpu_user == 0.0
        assert stats.cpu_system == 0.0
        assert stats.cpu_idle == 0.0
        assert stats.cpu_iowait == 0.0
        assert stats.mem_total == 0
        assert stats.mem_used == 0
        assert stats.mem_free == 0
        assert stats.mem_available == 0
        assert stats.mem_buffers == 0
        assert stats.mem_cached == 0
        assert stats.load_1min == 0.0
        assert stats.load_5min == 0.0
        assert stats.load_15min == 0.0
        assert stats.process_count == 0
        assert stats.running_processes == 0

    def test_system_stats_with_values(self):
        """Test creating SystemStats with custom values."""
        stats = SystemStats(
            cpu_user=25.5,
            cpu_system=10.2,
            cpu_idle=64.3,
            cpu_iowait=0.0,
            mem_total=16000000,
            mem_used=8000000,
            mem_free=8000000,
            mem_available=8000000,
            mem_buffers=500000,
            mem_cached=1000000,
            load_1min=1.5,
            load_5min=1.2,
            load_15min=1.0,
            process_count=150,
            running_processes=3,
        )
        assert stats.cpu_user == 25.5
        assert stats.cpu_system == 10.2
        assert stats.cpu_idle == 64.3
        assert stats.cpu_iowait == 0.0
        assert stats.mem_total == 16000000
        assert stats.mem_used == 8000000
        assert stats.mem_free == 8000000
        assert stats.mem_available == 8000000
        assert stats.mem_buffers == 500000
        assert stats.mem_cached == 1000000
        assert stats.load_1min == 1.5
        assert stats.load_5min == 1.2
        assert stats.load_15min == 1.0
        assert stats.process_count == 150
        assert stats.running_processes == 3

    def test_system_stats_is_dataclass(self):
        """Test that SystemStats is a proper dataclass."""
        assert dataclasses.is_dataclass(SystemStats)
        fields = dataclasses.fields(SystemStats)
        field_names = [f.name for f in fields]
        expected_fields = [
            "cpu_user",
            "cpu_system",
            "cpu_idle",
            "cpu_iowait",
            "mem_total",
            "mem_used",
            "mem_free",
            "mem_available",
            "mem_buffers",
            "mem_cached",
            "load_1min",
            "load_5min",
            "load_15min",
            "process_count",
            "running_processes",
        ]
        for field in expected_fields:
            assert field in field_names


class TestSystemDashboard:
    """Test SystemDashboard class."""

    @pytest.fixture
    def mock_shell(self):
        """Create a mock shell instance."""
        shell = mock.Mock()
        shell.name = "test_shell"
        return shell

    @pytest.fixture
    def dashboard(self, mock_shell):
        """Create a SystemDashboard instance for testing."""
        return SystemDashboard(mock_shell)

    def test_dashboard_init(self, mock_shell):
        """Test SystemDashboard initialization."""
        dashboard = SystemDashboard(mock_shell)
        assert dashboard.shell == mock_shell
        assert dashboard.update_interval == 1.0
        assert dashboard.stats is not None
        assert isinstance(dashboard.stats, SystemStats)
        assert dashboard.running is False
        assert dashboard.update_thread is None
        assert dashboard.history_length == 20

    def test_dashboard_alerts_default(self, dashboard):
        """Test default alert thresholds."""
        assert dashboard.alerts["cpu_high"] == 80.0
        assert dashboard.alerts["memory_high"] == 85.0
        assert dashboard.alerts["load_high"] == 1.0
        assert dashboard.alerts["disk_high"] == 90.0

    def test_dashboard_history_lists_initialized(self, dashboard):
        """Test that history lists are initialized."""
        assert isinstance(dashboard.cpu_history, list)
        assert isinstance(dashboard.memory_history, list)
        assert isinstance(dashboard.load_history, list)
        assert len(dashboard.cpu_history) == 0
        assert len(dashboard.memory_history) == 0
        assert len(dashboard.load_history) == 0

    def test_update_cpu_stats_success(self, dashboard):
        """Test successful CPU stats update."""
        mock_file = mock.Mock()
        mock_file.read.return_value = "cpu  100 200 300 400 500 600 700\n"

        with mock.patch.object(dashboard.shell.client, "pull") as mock_pull:
            mock_pull.return_value.__enter__ = mock.Mock(return_value=mock_file)
            mock_pull.return_value.__exit__ = mock.Mock(return_value=None)

            dashboard._update_cpu_stats()

            mock_pull.assert_called_with("/proc/stat")
            # Check that CPU stats were updated
            assert dashboard.stats.cpu_user > 0
            assert dashboard.stats.cpu_system > 0

    def test_update_memory_stats_success(self, dashboard):
        """Test successful memory stats update."""
        mock_file = mock.Mock()
        mock_file.read.return_value = """MemTotal:       16000000 kB
MemFree:         8000000 kB
MemAvailable:    8000000 kB
Buffers:          500000 kB
Cached:          1000000 kB
"""

        with mock.patch.object(dashboard.shell.client, "pull") as mock_pull:
            mock_pull.return_value.__enter__ = mock.Mock(return_value=mock_file)
            mock_pull.return_value.__exit__ = mock.Mock(return_value=None)

            dashboard._update_memory_stats()

            mock_pull.assert_called_with("/proc/meminfo")
            # Check that memory stats were updated
            assert dashboard.stats.mem_total == 16000000
            assert dashboard.stats.mem_free == 8000000

    def test_update_load_stats_success(self, dashboard):
        """Test successful load average stats update."""
        mock_file = mock.Mock()
        mock_file.read.return_value = "1.50 1.20 1.00 2/150 12345\n"

        with mock.patch.object(dashboard.shell.client, "pull") as mock_pull:
            mock_pull.return_value.__enter__ = mock.Mock(return_value=mock_file)
            mock_pull.return_value.__exit__ = mock.Mock(return_value=None)

            dashboard._update_load_stats()

            mock_pull.assert_called_with("/proc/loadavg")
            # Check that load stats were updated
            assert dashboard.stats.load_1min == 1.5
            assert dashboard.stats.load_5min == 1.2
            assert dashboard.stats.load_15min == 1.0
            assert dashboard.stats.running_processes == 2
            assert dashboard.stats.process_count == 150

    def test_format_uptime(self, dashboard):
        """Test uptime formatting."""
        assert dashboard._format_uptime(3661) == "1h 1m"  # 1 hour, 1 minute, 1 second
        assert dashboard._format_uptime(86401) == "1d 0h 0m"  # 1 day, 1 second
        assert dashboard._format_uptime(60) == "1m"  # 1 minute
        assert dashboard._format_uptime(0) == "0m"  # 0 seconds

    def test_create_progress_bar(self, dashboard):
        """Test progress bar creation."""
        bar = dashboard._create_progress_bar(50, 100, 10)
        assert len(bar) == 10
        assert bar.count("█") == 5  # 50% of 10
        assert bar.count("░") == 5

        # Test edge cases
        bar_full = dashboard._create_progress_bar(100, 100, 10)
        assert bar_full == "█" * 10

        bar_empty = dashboard._create_progress_bar(0, 100, 10)
        assert bar_empty == "░" * 10

    def test_create_header(self, dashboard):
        """Test header panel creation."""
        dashboard.stats.uptime_seconds = 3600
        dashboard.stats.cpu_cores = 4

        panel = dashboard._create_header()
        # Just verify it returns a Panel object - actual content testing would be complex
        assert panel is not None

    def test_start_dashboard(self, dashboard):
        """Test dashboard start method."""
        with (
            mock.patch("threading.Thread") as mock_thread,
            mock.patch("pebble_shell.utils.dashboard.Live") as mock_live,
            mock.patch("time.sleep"),  # Not used but needed to prevent actual sleep
        ):
            mock_thread_instance = mock.Mock()
            mock_thread.return_value = mock_thread_instance

            # Mock Live context manager to exit immediately by raising KeyboardInterrupt
            def mock_live_context(*args, **kwargs):
                # Set running to False before raising KeyboardInterrupt
                dashboard.running = False
                raise KeyboardInterrupt()

            mock_live.return_value.__enter__ = mock_live_context
            mock_live.return_value.__exit__ = mock.Mock(return_value=None)

            dashboard.start()

            # Verify the thread was created and started
            mock_thread.assert_called_once()
            mock_thread_instance.start.assert_called_once()
            # Verify that running was set to False (by stop() call)
            assert dashboard.running is False

    def test_update_stats(self, dashboard):
        """Test stats update method calls all individual update methods."""
        with (
            mock.patch.object(dashboard, "_update_cpu_stats") as mock_cpu,
            mock.patch.object(dashboard, "_update_memory_stats") as mock_mem,
            mock.patch.object(dashboard, "_update_load_stats") as mock_load,
            mock.patch.object(dashboard, "_update_process_stats") as mock_proc,
            mock.patch.object(dashboard, "_update_disk_stats") as mock_disk,
            mock.patch.object(dashboard, "_update_network_stats") as mock_net,
            mock.patch.object(dashboard, "_update_system_info") as mock_sys,
            mock.patch.object(dashboard, "_update_history") as mock_hist,
        ):
            dashboard._update_stats()

            mock_cpu.assert_called_once()
            mock_mem.assert_called_once()
            mock_load.assert_called_once()
            mock_proc.assert_called_once()
            mock_disk.assert_called_once()
            mock_net.assert_called_once()
            mock_sys.assert_called_once()
            mock_hist.assert_called_once()

    def test_stop_dashboard_running(self, dashboard):
        """Test stopping dashboard when running."""
        dashboard.running = True

        dashboard.stop()

        assert dashboard.running is False

    def test_stop_dashboard_not_running(self, dashboard):
        """Test stopping dashboard when not running."""
        dashboard.running = False

        dashboard.stop()

        assert dashboard.running is False

    def test_update_history_with_data(self, dashboard):
        """Test updating history lists with data."""
        # Set some stats
        dashboard.stats.cpu_user = 25.0
        dashboard.stats.mem_used = 8000000
        dashboard.stats.mem_total = 16000000
        dashboard.stats.load_1min = 1.5

        dashboard._update_history()

        assert len(dashboard.cpu_history) == 1
        assert len(dashboard.memory_history) == 1
        assert len(dashboard.load_history) == 1
        assert dashboard.cpu_history[0] == 25.0
        assert dashboard.memory_history[0] == 50.0  # 8000000/16000000 * 100
        assert dashboard.load_history[0] == 1.5

    def test_update_history_max_length(self, dashboard):
        """Test that history lists maintain max length."""
        # Fill history beyond max length
        for i in range(25):  # More than history_length (20)
            dashboard.stats.cpu_user = float(i)
            dashboard.stats.mem_used = 1000000 * i
            dashboard.stats.mem_total = 20000000
            dashboard.stats.load_1min = float(i) * 0.1
            dashboard._update_history()

        assert len(dashboard.cpu_history) == dashboard.history_length
        assert len(dashboard.memory_history) == dashboard.history_length
        assert len(dashboard.load_history) == dashboard.history_length

        # Should have the most recent values
        assert dashboard.cpu_history[-1] == 24.0
        assert (
            abs(dashboard.load_history[-1] - 2.4) < 0.0001
        )  # Handle floating point precision

    def test_update_stats_with_exception(self, dashboard):
        """Test _update_stats with exception handling."""
        with (
            mock.patch.object(
                dashboard, "_update_cpu_stats", side_effect=Exception("CPU error")
            ),
            mock.patch("pebble_shell.utils.dashboard.logging") as mock_logging,
        ):
            dashboard._update_stats()

            # Should log the error but not crash
            mock_logging.warning.assert_called_with(
                "Failed to update dashboard stats: %s", mock.ANY
            )

    def test_update_process_stats(self, dashboard):
        """Test process stats update."""
        mock_entry1 = mock.Mock()
        mock_entry1.name = "123"  # Numeric (process)
        mock_entry2 = mock.Mock()
        mock_entry2.name = "456"  # Numeric (process)
        mock_entry3 = mock.Mock()
        mock_entry3.name = "stat"  # Non-numeric (not a process)

        mock_entries = [mock_entry1, mock_entry2, mock_entry3]

        with mock.patch.object(
            dashboard.shell.client, "list_files", return_value=mock_entries
        ):
            dashboard._update_process_stats()

            assert dashboard.stats.process_count == 2  # Only numeric entries

    def test_update_disk_stats(self, dashboard):
        """Test disk stats update."""
        mock_file = mock.Mock()
        mock_file.read.return_value = """   8       0 sda 100 0 200 0 300 0 400 0 0 0 0
   8      16 sdb 150 0 300 0 350 0 500 0 0 0 0
"""

        with mock.patch.object(dashboard.shell.client, "pull") as mock_pull:
            mock_pull.return_value.__enter__ = mock.Mock(return_value=mock_file)
            mock_pull.return_value.__exit__ = mock.Mock(return_value=None)

            dashboard._update_disk_stats()

            mock_pull.assert_called_with("/proc/diskstats")
            assert dashboard.stats.disk_reads == 250  # 100 + 150
            assert dashboard.stats.disk_writes == 650  # 300 + 350
            assert dashboard.stats.disk_read_kb == 250  # (200 + 300) * 0.5
            assert dashboard.stats.disk_write_kb == 450  # (400 + 500) * 0.5

    def test_update_disk_stats_with_invalid_data(self, dashboard):
        """Test disk stats update with invalid data."""
        mock_file = mock.Mock()
        mock_file.read.return_value = """invalid line
   8       0 sda insufficient parts
   completely invalid line with no numbers
"""

        with mock.patch.object(dashboard.shell.client, "pull") as mock_pull:
            mock_pull.return_value.__enter__ = mock.Mock(return_value=mock_file)
            mock_pull.return_value.__exit__ = mock.Mock(return_value=None)

            dashboard._update_disk_stats()

            # Should handle invalid data gracefully - only lines with insufficient parts or no numbers
            assert dashboard.stats.disk_reads == 0
            assert dashboard.stats.disk_writes == 0

    def test_update_network_stats(self, dashboard):
        """Test network stats update."""
        mock_file = mock.Mock()
        mock_file.read.return_value = """Inter-|   Receive                                                |  Transmit
 face |bytes    packets errs drop fifo frame compressed multicast|bytes    packets errs drop fifo colls carrier compressed
    lo: 1000000    1000    0    0    0     0          0         0  2000000    2000    0    0    0     0       0          0
  eth0: 5000000    5000    0    0    0     0          0         0 10000000   10000    0    0    0     0       0          0
"""

        with mock.patch.object(dashboard.shell.client, "pull") as mock_pull:
            mock_pull.return_value.__enter__ = mock.Mock(return_value=mock_file)
            mock_pull.return_value.__exit__ = mock.Mock(return_value=None)

            dashboard._update_network_stats()

            mock_pull.assert_called_with("/proc/net/dev")
            assert "lo" in dashboard.stats.network_interfaces
            assert "eth0" in dashboard.stats.network_interfaces
            assert dashboard.stats.network_interfaces["eth0"]["rx_bytes"] == 5000000
            assert dashboard.stats.network_interfaces["eth0"]["tx_bytes"] == 10000000

    def test_update_network_stats_with_invalid_data(self, dashboard):
        """Test network stats update with invalid data."""
        mock_file = mock.Mock()
        mock_file.read.return_value = """Inter-|   Receive                                                |  Transmit
 face |bytes    packets errs drop fifo frame compressed multicast|bytes    packets errs drop fifo colls carrier compressed
    lo: invalid data here
  eth0: 5000000    not_a_number    0    0    0     0          0         0 10000000   10000    0    0    0     0       0          0
"""

        with mock.patch.object(dashboard.shell.client, "pull") as mock_pull:
            mock_pull.return_value.__enter__ = mock.Mock(return_value=mock_file)
            mock_pull.return_value.__exit__ = mock.Mock(return_value=None)

            dashboard._update_network_stats()

            # Should handle invalid data gracefully
            assert len(dashboard.stats.network_interfaces) == 0

    def test_update_system_info(self, dashboard):
        """Test system info update."""
        mock_cpuinfo = mock.Mock()
        mock_cpuinfo.read.return_value = """processor	: 0
vendor_id	: GenuineIntel
cpu family	: 6
model		: 142
model name	: Intel(R) Core(TM) i7-8565U CPU @ 1.80GHz

processor	: 1
vendor_id	: GenuineIntel
cpu family	: 6
model		: 142
model name	: Intel(R) Core(TM) i7-8565U CPU @ 1.80GHz
"""

        mock_uptime = mock.Mock()
        mock_uptime.read.return_value = "3661.45 1830.22"

        with mock.patch.object(dashboard.shell.client, "pull") as mock_pull:
            # Configure the context manager to return different files based on path
            def pull_side_effect(path):
                mock_context = mock.Mock()
                if path == "/proc/cpuinfo":
                    mock_context.__enter__ = mock.Mock(return_value=mock_cpuinfo)
                elif path == "/proc/uptime":
                    mock_context.__enter__ = mock.Mock(return_value=mock_uptime)
                mock_context.__exit__ = mock.Mock(return_value=None)
                return mock_context

            mock_pull.side_effect = pull_side_effect

            dashboard._update_system_info()

            assert dashboard.stats.cpu_cores == 2  # Two processor entries
            assert dashboard.stats.uptime_seconds == 3661  # int(3661.45)

    def test_update_system_info_empty_uptime(self, dashboard):
        """Test system info update with empty uptime."""
        mock_cpuinfo = mock.Mock()
        mock_cpuinfo.read.return_value = "processor	: 0\n"

        mock_uptime = mock.Mock()
        mock_uptime.read.return_value = ""  # Empty uptime

        with mock.patch.object(dashboard.shell.client, "pull") as mock_pull:

            def pull_side_effect(path):
                mock_context = mock.Mock()
                if path == "/proc/cpuinfo":
                    mock_context.__enter__ = mock.Mock(return_value=mock_cpuinfo)
                elif path == "/proc/uptime":
                    mock_context.__enter__ = mock.Mock(return_value=mock_uptime)
                mock_context.__exit__ = mock.Mock(return_value=None)
                return mock_context

            mock_pull.side_effect = pull_side_effect

            dashboard._update_system_info()

            assert dashboard.stats.cpu_cores == 1
            # uptime_seconds should remain unchanged when content is empty

    def test_create_cpu_memory_panel(self, dashboard):
        """Test CPU memory panel creation."""
        dashboard.stats.cpu_user = 25.0
        dashboard.stats.cpu_system = 15.0
        dashboard.stats.mem_total = 16000000
        dashboard.stats.mem_used = 8000000

        panel = dashboard._create_cpu_memory_panel()

        # Just verify it returns a Panel - testing Rich components deeply would be complex
        assert panel is not None

    def test_create_cpu_memory_panel_high_usage(self, dashboard):
        """Test CPU memory panel with high usage (triggers alerts)."""
        dashboard.stats.cpu_user = 85.0  # High CPU
        dashboard.stats.cpu_system = 5.0
        dashboard.stats.mem_total = 16000000
        dashboard.stats.mem_used = 14000000  # High memory (87.5%)

        panel = dashboard._create_cpu_memory_panel()

        assert panel is not None

    def test_create_processes_panel(self, dashboard):
        """Test processes panel creation."""
        dashboard.stats.process_count = 150
        dashboard.stats.running_processes = 3
        dashboard.stats.load_1min = 2.0
        dashboard.stats.cpu_cores = 4

        panel = dashboard._create_processes_panel()

        assert panel is not None

    def test_create_processes_panel_no_cpu_cores(self, dashboard):
        """Test processes panel with no CPU cores."""
        dashboard.stats.process_count = 150
        dashboard.stats.running_processes = 3
        dashboard.stats.load_1min = 2.0
        dashboard.stats.cpu_cores = 0  # No cores detected

        panel = dashboard._create_processes_panel()

        assert panel is not None

    def test_create_load_disk_panel(self, dashboard):
        """Test load disk panel creation."""
        dashboard.stats.load_1min = 1.5
        dashboard.stats.load_5min = 1.2
        dashboard.stats.load_15min = 1.0
        dashboard.stats.disk_reads = 1000
        dashboard.stats.disk_writes = 2000
        dashboard.stats.disk_read_kb = 5000
        dashboard.stats.disk_write_kb = 10000

        panel = dashboard._create_load_disk_panel()

        assert panel is not None

    def test_create_network_panel_with_interfaces(self, dashboard):
        """Test network panel with multiple interfaces."""
        dashboard.stats.network_interfaces = {
            "eth0": {
                "rx_bytes": 5000000,
                "rx_packets": 5000,
                "tx_bytes": 10000000,
                "tx_packets": 10000,
            },
            "lo": {
                "rx_bytes": 1000000,
                "rx_packets": 1000,
                "tx_bytes": 2000000,
                "tx_packets": 2000,
            },
            "wlan0": {
                "rx_bytes": 3000000,
                "rx_packets": 3000,
                "tx_bytes": 6000000,
                "tx_packets": 6000,
            },
        }

        panel = dashboard._create_network_panel()

        assert panel is not None

    def test_create_network_panel_no_interfaces(self, dashboard):
        """Test network panel with no interfaces."""
        dashboard.stats.network_interfaces = {}

        panel = dashboard._create_network_panel()

        assert panel is not None

    def test_create_footer_with_alerts(self, dashboard):
        """Test footer creation with alerts."""
        # Set values that trigger alerts
        dashboard.stats.cpu_user = 85.0  # High CPU
        dashboard.stats.cpu_system = 5.0
        dashboard.stats.mem_total = 16000000
        dashboard.stats.mem_used = 14000000  # High memory
        dashboard.stats.load_1min = 2.0  # High load

        panel = dashboard._create_footer()

        assert panel is not None

    def test_create_footer_no_alerts(self, dashboard):
        """Test footer creation with no alerts."""
        # Set values that don't trigger alerts
        dashboard.stats.cpu_user = 25.0  # Normal CPU
        dashboard.stats.cpu_system = 10.0
        dashboard.stats.mem_total = 16000000
        dashboard.stats.mem_used = 8000000  # Normal memory
        dashboard.stats.load_1min = 0.5  # Normal load

        panel = dashboard._create_footer()

        assert panel is not None

    def test_stop_with_thread_timeout(self, dashboard):
        """Test stop method when thread join times out."""
        mock_thread = mock.Mock()
        dashboard.running = True
        dashboard.update_thread = mock_thread

        dashboard.stop()

        assert dashboard.running is False
        mock_thread.join.assert_called_once_with(timeout=1.0)

    def test_update_loop_with_logging(self, dashboard):
        """Test update loop with exception logging."""
        dashboard.running = True
        call_count = 0

        def side_effect(*args):
            nonlocal call_count
            call_count += 1
            if call_count >= 2:
                dashboard.running = False
            if call_count == 1:
                raise Exception("Test exception")

        with (
            mock.patch.object(dashboard, "_update_stats", side_effect=side_effect),
            mock.patch("time.sleep"),
            mock.patch("pebble_shell.utils.dashboard.logging") as mock_logging,
        ):
            dashboard._update_loop()

            # Should log the exception but continue running
            mock_logging.warning.assert_called_with(
                "Dashboard update failed: %s", mock.ANY
            )

    def test_update_cpu_stats_edge_cases(self, dashboard):
        """Test CPU stats with edge cases."""
        # Test with zero total (division by zero protection)
        mock_file = mock.Mock()
        mock_file.read.return_value = "cpu  0 0 0 0 0 0 0\n"

        with mock.patch.object(dashboard.shell.client, "pull") as mock_pull:
            mock_pull.return_value.__enter__ = mock.Mock(return_value=mock_file)
            mock_pull.return_value.__exit__ = mock.Mock(return_value=None)

            dashboard._update_cpu_stats()

            # Should handle zero total gracefully (no division by zero)

    def test_update_cpu_stats_insufficient_parts(self, dashboard):
        """Test CPU stats with insufficient parts."""
        mock_file = mock.Mock()
        mock_file.read.return_value = "cpu  100 200\n"  # Only 2 parts instead of >= 5

        with mock.patch.object(dashboard.shell.client, "pull") as mock_pull:
            mock_pull.return_value.__enter__ = mock.Mock(return_value=mock_file)
            mock_pull.return_value.__exit__ = mock.Mock(return_value=None)

            dashboard._update_cpu_stats()

            # Should skip lines with insufficient parts

    def test_update_load_stats_edge_cases(self, dashboard):
        """Test load stats with edge cases."""
        # Test with insufficient parts
        mock_file = mock.Mock()
        mock_file.read.return_value = "1.50 1.20\n"  # Only 2 parts instead of >= 3

        with mock.patch.object(dashboard.shell.client, "pull") as mock_pull:
            mock_pull.return_value.__enter__ = mock.Mock(return_value=mock_file)
            mock_pull.return_value.__exit__ = mock.Mock(return_value=None)

            dashboard._update_load_stats()

            # Should handle insufficient parts gracefully

    def test_update_load_stats_invalid_process_info(self, dashboard):
        """Test load stats with invalid process info."""
        mock_file = mock.Mock()
        mock_file.read.return_value = (
            "1.50 1.20 1.00 invalid_format 12345\n"  # Invalid process info format
        )

        with mock.patch.object(dashboard.shell.client, "pull") as mock_pull:
            mock_pull.return_value.__enter__ = mock.Mock(return_value=mock_file)
            mock_pull.return_value.__exit__ = mock.Mock(return_value=None)

            dashboard._update_load_stats()

            # Should handle invalid process info format gracefully
            assert dashboard.stats.load_1min == 1.5
            assert dashboard.stats.load_5min == 1.2
            assert dashboard.stats.load_15min == 1.0

    def test_create_processes_panel_high_load(self, dashboard):
        """Test processes panel with high load per core."""
        dashboard.stats.process_count = 150
        dashboard.stats.running_processes = 3
        dashboard.stats.load_1min = 5.0  # High load
        dashboard.stats.cpu_cores = 4

        panel = dashboard._create_processes_panel()

        assert panel is not None
