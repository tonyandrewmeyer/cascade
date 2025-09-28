"""Real-time system monitoring dashboard for Cascade shell."""

from __future__ import annotations

import dataclasses
import datetime
import logging
import threading
import time
from typing import TYPE_CHECKING

from rich.align import Align
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

if TYPE_CHECKING:
    from pebble_shell.shell import PebbleShell


@dataclasses.dataclass
class SystemStats:
    """Container for system statistics."""

    # CPU stats
    cpu_user: float = 0.0
    cpu_system: float = 0.0
    cpu_idle: float = 0.0
    cpu_iowait: float = 0.0

    # Memory stats
    mem_total: int = 0
    mem_used: int = 0
    mem_free: int = 0
    mem_available: int = 0
    mem_buffers: int = 0
    mem_cached: int = 0

    # Load averages
    load_1min: float = 0.0
    load_5min: float = 0.0
    load_15min: float = 0.0

    # Process stats
    process_count: int = 0
    running_processes: int = 0

    # Disk stats
    disk_reads: int = 0
    disk_writes: int = 0
    disk_read_kb: int = 0
    disk_write_kb: int = 0

    # Network stats (basic)
    network_interfaces: dict[str, dict[str, int]] = dataclasses.field(
        default_factory=dict
    )

    # System info
    uptime_seconds: int = 0
    cpu_cores: int = 0


class SystemDashboard:
    """Real-time system monitoring dashboard."""

    def __init__(self, shell: PebbleShell):
        self.shell = shell
        self.stats = SystemStats()
        self.running = False
        self.update_thread = None
        self.update_interval = 1.0  # seconds

        # Historical data for trends
        self.cpu_history: list[float] = []
        self.memory_history: list[float] = []
        self.load_history: list[float] = []
        self.history_length = 20

        # Alert thresholds
        self.alerts = {
            "cpu_high": 80.0,
            "memory_high": 85.0,
            "load_high": 1.0,
            "disk_high": 90.0,
        }

    def start(self):
        """Start the real-time dashboard."""
        self.running = True
        self.update_thread = threading.Thread(target=self._update_loop, daemon=True)
        self.update_thread.start()

        try:
            with Live(
                self._create_dashboard(), refresh_per_second=2, screen=True
            ) as live:
                while self.running:
                    live.update(self._create_dashboard())
                    time.sleep(0.5)
        except KeyboardInterrupt:
            self.stop()

    def stop(self):
        """Stop the dashboard."""
        self.running = False
        if self.update_thread:
            self.update_thread.join(timeout=1.0)

    def _update_loop(self):
        """Background thread for updating system statistics."""
        while self.running:
            try:
                self._update_stats()
                time.sleep(self.update_interval)
            except Exception as e:  # noqa: PERF203
                # Log errors but keep dashboard running
                logging.warning("Dashboard update failed: %s", e)

    def _update_stats(self):
        """Update system statistics from remote system."""
        try:
            # Get CPU stats
            self._update_cpu_stats()

            # Get memory stats
            self._update_memory_stats()

            # Get load averages
            self._update_load_stats()

            # Get process stats
            self._update_process_stats()

            # Get disk stats
            self._update_disk_stats()

            # Get network stats
            self._update_network_stats()

            # Get system info
            self._update_system_info()

            # Update history
            self._update_history()

        except Exception as e:
            # Log errors but don't crash dashboard
            logging.warning("Failed to update dashboard stats: %s", e)

    def _update_cpu_stats(self):
        """Update CPU statistics."""
        with self.shell.client.pull("/proc/stat") as file:
            content = file.read()
        assert isinstance(content, str)
        for line in content.splitlines():
            if line.startswith("cpu "):
                parts = line.split()
                if len(parts) >= 5:
                    total = sum(int(parts[i]) for i in range(1, 5))
                    if total > 0:
                        self.stats.cpu_user = (int(parts[1]) / total) * 100
                        self.stats.cpu_system = (int(parts[3]) / total) * 100
                        self.stats.cpu_idle = (int(parts[4]) / total) * 100
                        self.stats.cpu_iowait = (
                            (int(parts[5]) / total) * 100 if len(parts) > 5 else 0
                        )
                break

    def _update_memory_stats(self):
        """Update memory statistics."""
        with self.shell.client.pull("/proc/meminfo") as file:
            content = file.read()
        assert isinstance(content, str)

        mem_stats: dict[str, int] = {}
        for line in content.splitlines():
            if ":" in line:
                key, value = line.split(":", 1)
                key = key.strip()
                value = value.strip().split()[0]
                try:
                    mem_stats[key] = int(value)
                except ValueError:
                    continue

        self.stats.mem_total = mem_stats.get("MemTotal", 0)
        self.stats.mem_free = mem_stats.get("MemFree", 0)
        self.stats.mem_available = mem_stats.get("MemAvailable", self.stats.mem_free)
        self.stats.mem_buffers = mem_stats.get("Buffers", 0)
        self.stats.mem_cached = mem_stats.get("Cached", 0)
        self.stats.mem_used = (
            self.stats.mem_total - self.stats.mem_available
            if self.stats.mem_total > 0
            else 0
        )

    def _update_load_stats(self):
        """Update load average statistics."""
        with self.shell.client.pull("/proc/loadavg") as file:
            content = file.read().strip()
        assert isinstance(content, str)

        parts = content.split()
        if len(parts) >= 3:
            self.stats.load_1min = float(parts[0])
            self.stats.load_5min = float(parts[1])
            self.stats.load_15min = float(parts[2])

            # Get process info
            if len(parts) >= 5:
                process_info = parts[3].split("/")
                if len(process_info) == 2:
                    self.stats.running_processes = int(process_info[0])
                    self.stats.process_count = int(process_info[1])

    def _update_process_stats(self):
        """Update process statistics."""
        proc_entries = self.shell.client.list_files("/proc")
        self.stats.process_count = sum(
            1 for entry in proc_entries if entry.name.isdigit()
        )

    def _update_disk_stats(self):
        """Update disk I/O statistics."""
        with self.shell.client.pull("/proc/diskstats") as file:
            content = file.read()

        total_reads = 0
        total_writes = 0
        total_read_sectors = 0
        total_write_sectors = 0

        for line in content.splitlines():
            if line.strip():
                parts = line.split()
                if len(parts) >= 14:
                    try:
                        total_reads += int(parts[3])
                        total_writes += int(parts[7])
                        total_read_sectors += int(parts[5])
                        total_write_sectors += int(parts[9])
                    except (ValueError, IndexError):
                        continue

        self.stats.disk_reads = total_reads
        self.stats.disk_writes = total_writes
        self.stats.disk_read_kb = int(total_read_sectors * 0.5)  # Convert sectors to KB
        self.stats.disk_write_kb = int(total_write_sectors * 0.5)

    def _update_network_stats(self):
        """Update network interface statistics."""
        with self.shell.client.pull("/proc/net/dev") as file:
            content = file.read()
        assert isinstance(content, str)

        self.stats.network_interfaces = {}
        for line in content.splitlines()[2:]:  # Skip header lines
            if ":" in line:
                parts = line.split(":")
                if len(parts) >= 2:
                    interface = parts[0].strip()
                    stats = parts[1].split()
                    if len(stats) >= 16:
                        try:
                            self.stats.network_interfaces[interface] = {
                                "rx_bytes": int(stats[0]),
                                "rx_packets": int(stats[1]),
                                "tx_bytes": int(stats[8]),
                                "tx_packets": int(stats[9]),
                            }
                        except (ValueError, IndexError):
                            continue

    def _update_system_info(self):
        """Update system information."""
        with self.shell.client.pull("/proc/cpuinfo") as file:
            content = file.read()
        assert isinstance(content, str)

        self.stats.cpu_cores = sum(
            1 for line in content.splitlines() if line.startswith("processor")
        )

        with self.shell.client.pull("/proc/uptime") as file:
            content = file.read().strip()

        if content:
            self.stats.uptime_seconds = int(float(content.split()[0]))

    def _update_history(self):
        """Update historical data for trends."""
        cpu_usage = self.stats.cpu_user + self.stats.cpu_system
        memory_usage = (
            (self.stats.mem_used / self.stats.mem_total * 100)
            if self.stats.mem_total > 0
            else 0
        )

        self.cpu_history.append(cpu_usage)
        self.memory_history.append(memory_usage)
        self.load_history.append(self.stats.load_1min)

        # Keep history length
        if len(self.cpu_history) > self.history_length:
            self.cpu_history.pop(0)
            self.memory_history.pop(0)
            self.load_history.pop(0)

    def _create_dashboard(self) -> Layout:
        """Create the dashboard layout."""
        layout = Layout()

        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="main"),
            Layout(name="footer", size=3),
        )

        layout["main"].split_row(
            Layout(name="left", ratio=1), Layout(name="right", ratio=1)
        )

        layout["left"].split_column(Layout(name="cpu_memory"), Layout(name="processes"))

        layout["right"].split_column(Layout(name="load_disk"), Layout(name="network"))

        layout["header"].update(self._create_header())
        layout["cpu_memory"].update(self._create_cpu_memory_panel())
        layout["processes"].update(self._create_processes_panel())
        layout["load_disk"].update(self._create_load_disk_panel())
        layout["network"].update(self._create_network_panel())
        layout["footer"].update(self._create_footer())

        return layout

    def _create_header(self) -> Panel:
        """Create the header panel."""
        uptime_str = self._format_uptime(self.stats.uptime_seconds)

        header_text = Text()
        header_text.append("🖥️  Cascade System Dashboard", style="bold cyan")
        header_text.append(" | ")
        header_text.append(f"Uptime: {uptime_str}", style="yellow")
        header_text.append(" | ")
        header_text.append(f"CPU Cores: {self.stats.cpu_cores}", style="green")
        header_text.append(" | ")
        header_text.append(
            f"Last Update: {datetime.datetime.now().strftime('%H:%M:%S')}", style="dim"
        )

        return Panel(
            Align.center(header_text), style="bold blue", border_style="bright_blue"
        )

    def _create_cpu_memory_panel(self) -> Panel:
        """Create CPU and Memory panel."""
        table = Table(show_header=False, box=None, padding=(0, 1))
        table.add_column("Metric", style="cyan", no_wrap=True)
        table.add_column("Value", style="yellow", no_wrap=True)
        table.add_column("Bar", style="green", no_wrap=True)

        cpu_total = self.stats.cpu_user + self.stats.cpu_system
        cpu_bar = self._create_progress_bar(cpu_total, 100, 20)
        cpu_style = "red" if cpu_total > self.alerts["cpu_high"] else "green"
        table.add_row(
            "CPU Usage", f"{cpu_total:.1f}%", f"[{cpu_style}]{cpu_bar}[/{cpu_style}]"
        )

        mem_usage = (
            (self.stats.mem_used / self.stats.mem_total * 100)
            if self.stats.mem_total > 0
            else 0
        )
        mem_bar = self._create_progress_bar(mem_usage, 100, 20)
        mem_style = "red" if mem_usage > self.alerts["memory_high"] else "green"
        table.add_row(
            "Memory", f"{mem_usage:.1f}%", f"[{mem_style}]{mem_bar}[/{mem_style}]"
        )

        mem_total_mb = self.stats.mem_total // 1024
        mem_used_mb = self.stats.mem_used // 1024
        table.add_row("Memory Details", f"{mem_used_mb}M / {mem_total_mb}M", "")

        return Panel(table, title="💻 CPU & Memory", border_style="bright_blue")

    def _create_processes_panel(self) -> Panel:
        """Create processes panel."""
        table = Table(show_header=False, box=None, padding=(0, 1))
        table.add_column("Metric", style="cyan", no_wrap=True)
        table.add_column("Value", style="yellow", no_wrap=True)

        table.add_row("Total Processes", str(self.stats.process_count))
        table.add_row("Running Processes", str(self.stats.running_processes))

        if self.stats.cpu_cores > 0:
            load_per_core = self.stats.load_1min / self.stats.cpu_cores
            load_style = "red" if load_per_core > self.alerts["load_high"] else "green"
            table.add_row(
                "Load per Core", f"[{load_style}]{load_per_core:.2f}[/{load_style}]"
            )
        else:
            table.add_row("Load per Core", "N/A")

        return Panel(table, title="📊 Processes", border_style="bright_blue")

    def _create_load_disk_panel(self) -> Panel:
        """Create load averages and disk I/O panel."""
        table = Table(show_header=False, box=None, padding=(0, 1))
        table.add_column("Metric", style="cyan", no_wrap=True)
        table.add_column("Value", style="yellow", no_wrap=True)

        table.add_row("Load 1min", f"{self.stats.load_1min:.2f}")
        table.add_row("Load 5min", f"{self.stats.load_5min:.2f}")
        table.add_row("Load 15min", f"{self.stats.load_15min:.2f}")

        table.add_row("Disk Reads", f"{self.stats.disk_reads:,}")
        table.add_row("Disk Writes", f"{self.stats.disk_writes:,}")
        table.add_row("Disk Read KB", f"{self.stats.disk_read_kb:,}")
        table.add_row("Disk Write KB", f"{self.stats.disk_write_kb:,}")

        return Panel(table, title="⚡ Load & Disk", border_style="bright_blue")

    def _create_network_panel(self) -> Panel:
        """Create network interfaces panel."""
        table = Table(show_header=False, box=None, padding=(0, 1))
        table.add_column("Interface", style="cyan", no_wrap=True)
        table.add_column("RX/TX", style="yellow", no_wrap=True)

        for interface, stats in list(self.stats.network_interfaces.items())[
            :5
        ]:  # Show top 5
            rx_mb = stats["rx_bytes"] // (1024 * 1024)
            tx_mb = stats["tx_bytes"] // (1024 * 1024)
            table.add_row(interface, f"{rx_mb}M / {tx_mb}M")

        if not self.stats.network_interfaces:
            table.add_row("No data", "N/A")

        return Panel(table, title="🌐 Network", border_style="bright_blue")

    def _create_footer(self) -> Panel:
        """Create the footer panel with alerts and controls."""
        footer_text = Text()
        footer_text.append("Press ", style="dim")
        footer_text.append("Ctrl+C", style="bold red")
        footer_text.append(" to exit dashboard | ", style="dim")
        footer_text.append("Refresh: 2s", style="green")

        alerts: list[str] = []
        if self.stats.cpu_user + self.stats.cpu_system > self.alerts["cpu_high"]:
            alerts.append("High CPU")
        if (
            self.stats.mem_total > 0
            and (self.stats.mem_used / self.stats.mem_total * 100)
            > self.alerts["memory_high"]
        ):
            alerts.append("High Memory")
        if self.stats.load_1min > self.alerts["load_high"]:
            alerts.append("High Load")

        if alerts:
            footer_text.append(" | Alerts: ", style="dim")
            footer_text.append(", ".join(alerts), style="bold red")

        return Panel(Align.center(footer_text), style="dim", border_style="bright_blue")

    def _create_progress_bar(self, value: float, max_value: float, width: int) -> str:
        """Create a text-based progress bar."""
        if max_value <= 0:
            return "█" * width

        filled = int((value / max_value) * width)
        bar = "█" * filled + "░" * (width - filled)
        return bar

    def _format_uptime(self, seconds: int) -> str:
        """Format uptime in human readable format."""
        days = seconds // 86400
        hours = (seconds % 86400) // 3600
        minutes = (seconds % 3600) // 60

        if days > 0:
            return f"{days}d {hours}h {minutes}m"
        if hours > 0:
            return f"{hours}h {minutes}m"
        return f"{minutes}m"
