#!/usr/bin/env python3

"""A filesystem-based process monitor similar to htop."""

from __future__ import annotations

import curses
import dataclasses
import logging
import os
import signal
import time
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    import ops
    import shimmer

from ..utils.command_helpers import handle_help_flag
from ..utils.formatting import format_bytes, format_time
from ..utils.proc_reader import parse_proc_meminfo, parse_proc_stat, read_proc_file
from ..utils.table_builder import add_process_columns, create_enhanced_table
from .base import Command


@dataclasses.dataclass
class ProcessInfo:
    """Process information."""

    pid: int
    ppid: int
    name: str
    state: str
    cpu_percent: float
    memory_percent: float
    memory_kb: int
    user: str
    priority: int
    nice: int
    threads: int
    start_time: int
    cpu_time: int
    cmdline: str


# TODO: Replace this with the common proc reader code.
class ProcReader:
    """Reads process information from /proc filesystem."""

    def __init__(self, client: ops.pebble.Client | shimmer.PebbleCliClient):
        self._client = client
        self.last_cpu_stats: dict[int, tuple[int, int | float]] = {}
        self.last_system_stats: tuple[int, int] | None = None
        self.boot_time = self._get_boot_time()
        self.clock_ticks = os.sysconf(os.sysconf_names["SC_CLK_TCK"])

    def _get_boot_time(self) -> int:
        """Get system boot time from /proc/stat."""
        try:
            stat_data = parse_proc_stat(self._client)
            system_data = stat_data.get("system", {})
            if isinstance(system_data, dict):
                btime = system_data.get("btime", 0)
                return btime if isinstance(btime, int) else 0
            return 0
        except Exception:
            return 0

    def _get_system_cpu_stats(self) -> tuple[int, int]:
        """Get total system CPU time from /proc/stat."""
        try:
            stat_data = parse_proc_stat(self._client)
            cpu_data = stat_data.get("cpu", {})
            if isinstance(cpu_data, dict):
                user = cpu_data.get("user", 0)
                nice = cpu_data.get("nice", 0)
                system = cpu_data.get("system", 0)
                idle = cpu_data.get("idle", 0)
                # Ensure all values are integers before adding
                if all(isinstance(val, int) for val in [user, nice, system, idle]):
                    # Type checker now knows these are all integers
                    user_int = user if isinstance(user, int) else 0
                    nice_int = nice if isinstance(nice, int) else 0
                    system_int = system if isinstance(system, int) else 0
                    idle_int = idle if isinstance(idle, int) else 0
                    total = user_int + nice_int + system_int + idle_int
                    return total, idle_int
        except Exception:  # noqa: S110
            # Silently ignore parsing errors and return default values
            pass
        return 0, 0

    def get_memory_info(self) -> tuple[int, int]:
        """Get total and available memory from /proc/meminfo."""
        try:
            mem_data = parse_proc_meminfo(self._client)
            mem_total = mem_data.get("MemTotal", 0)
            mem_available = mem_data.get("MemAvailable", 0)
            return mem_total, mem_available
        except Exception:
            return 0, 0

    def _get_process_info(self, pid: int) -> ProcessInfo | None:
        """Get information for a specific process."""
        try:
            try:
                stat_line = read_proc_file(self._client, f"/proc/{pid}/stat").strip()
            except Exception:
                return None

            parts = stat_line.split()
            if len(parts) < 44:
                return None

            name_end = -1
            for i, part in enumerate(parts):
                if part.endswith(")"):
                    name_end = i
                    break

            if name_end == -1:
                return None

            name = " ".join(parts[1 : name_end + 1])[1:-1]
            stat_fields = parts[name_end + 1 :]

            if len(stat_fields) < 40:
                return None

            state = stat_fields[0]
            ppid = int(stat_fields[1])
            priority = int(stat_fields[15])
            nice = int(stat_fields[16])
            threads = int(stat_fields[17])
            start_time = int(stat_fields[19])
            utime = int(stat_fields[11])
            stime = int(stat_fields[12])
            cpu_time = utime + stime

            memory_kb = 0
            try:
                content = read_proc_file(self._client, f"/proc/{pid}/status")
                for line in content.splitlines():
                    if line.startswith("VmRSS:"):
                        memory_kb = int(line.split()[1])
                        break
            except Exception as e:
                logging.debug(f"Failed to read memory info for PID {pid}: {e}")

            cmdline = ""
            try:
                content = read_proc_file(self._client, f"/proc/{pid}/cmdline")
                cmdline = content.replace("\0", " ").strip()
                if not cmdline:
                    cmdline = f"[{name}]"
            except Exception:
                cmdline = f"[{name}]"

            user = "root"

            # Calculate CPU percentage.
            cpu_percent = 0.0
            current_time = time.time()
            if pid in self.last_cpu_stats:
                last_cpu_time, last_time = self.last_cpu_stats[pid]
                time_diff = current_time - last_time
                cpu_time_diff = cpu_time - last_cpu_time
                if time_diff > 0:
                    cpu_percent = (cpu_time_diff / self.clock_ticks) / time_diff * 100

            self.last_cpu_stats[pid] = (cpu_time, current_time)

            total_memory, _ = self.get_memory_info()
            memory_percent = (memory_kb / total_memory * 100) if total_memory > 0 else 0

            return ProcessInfo(
                pid=pid,
                ppid=ppid,
                name=name,
                state=state,
                cpu_percent=cpu_percent,
                memory_percent=memory_percent,
                memory_kb=memory_kb,
                user=user,
                priority=priority,
                nice=nice,
                threads=threads,
                start_time=start_time,
                cpu_time=cpu_time,
                cmdline=cmdline,
            )

        except (FileNotFoundError, PermissionError, ValueError, IndexError):
            return None

    def get_all_processes(self) -> list[ProcessInfo]:
        """Get information for all processes."""
        processes: list[ProcessInfo] = []

        current_pids: set[int] = set()
        try:
            proc_entries = self._client.list_files("/proc")
            for entry in proc_entries:
                if entry.name.isdigit():
                    current_pids.add(int(entry.name))
        except Exception:
            # Fallback: try common PID range if listing fails
            for pid in range(1, 1000):  # Limited range for performance
                try:
                    # Test if PID exists by trying to read stat file
                    read_proc_file(self._client, f"/proc/{pid}/stat")
                    current_pids.add(pid)
                except Exception:  # noqa: PERF203, S112
                    continue

        # Clean up old CPU stats for processes that no longer exist
        old_pids = set(self.last_cpu_stats.keys()) - current_pids
        for pid in old_pids:
            del self.last_cpu_stats[pid]

        # Get process info for each valid PID
        for pid in current_pids:
            proc_info = self._get_process_info(pid)
            if proc_info:
                processes.append(proc_info)

        return processes


class TopCommand(Command):
    """Display system processes in a top-like interface."""

    name = "top"
    help = "Display system processes in a top-like interface"
    category = "System Commands"

    def execute(
        self, client: ops.pebble.Client | shimmer.PebbleCliClient, args: list[str]
    ):
        """Execute the top command."""
        if handle_help_flag(self, args):
            self.show_help()
            return 0

        # Parse arguments for batch mode
        batch_mode = False
        _ = 1

        if "-b" in args:
            batch_mode = True

        if "-n" in args:
            try:
                n_index = args.index("-n")
                _ = int(args[n_index + 1]) if n_index + 1 < len(args) else 1
            except (ValueError, IndexError):
                _ = 1

        if "--once" in args or batch_mode:
            # One-shot rich table output
            proc_reader = ProcReader(client)
            processes = proc_reader.get_all_processes()
            table = add_process_columns(create_enhanced_table()).build()
            # Sort by CPU descending by default
            processes.sort(key=lambda p: p.cpu_percent, reverse=True)
            for proc in processes:
                cpu_style = (
                    "bold red"
                    if proc.cpu_percent > 50
                    else ("yellow" if proc.cpu_percent > 10 else "")
                )
                mem_style = (
                    "bold red"
                    if proc.memory_percent > 20
                    else ("blue" if proc.memory_percent > 5 else "")
                )
                table.add_row(
                    str(proc.pid),
                    proc.user,
                    f"[{cpu_style}]{proc.cpu_percent:>6.1f}[/{cpu_style}]"
                    if cpu_style
                    else f"{proc.cpu_percent:>6.1f}",
                    f"[{mem_style}]{proc.memory_percent:>6.1f}[/{mem_style}]"
                    if mem_style
                    else f"{proc.memory_percent:>6.1f}",
                    format_bytes(proc.memory_kb),
                    proc.state,
                    str(proc.threads),
                    proc.cmdline[:30],
                )
            self.console.print(table)
            return 0
        try:
            app = PebbleTopViewer(client)
            curses.wrapper(app.run)
        except KeyboardInterrupt:
            # Normal exit via Ctrl+C
            pass
        except Exception as e:
            print(f"Error: {e}")
            return 1
        return 0


class PebbleTopViewer:
    """Main application class for the top-like interface."""

    def __init__(self, client: ops.pebble.Client | shimmer.PebbleCliClient):
        self._client = client
        self.proc_reader = ProcReader(client)
        self.sort_column = "cpu_percent"
        self.sort_reverse = True
        self.show_threads = False
        self.running = True

    def draw_header(self, stdscr: curses.window, processes: list[ProcessInfo]):
        """Draw the header with system information, with color."""
        _, width = stdscr.getmaxyx()
        try:
            content = read_proc_file(self._client, "/proc/uptime")
            uptime = float(content.split()[0])
            uptime_str = format_time(int(uptime))
        except (FileNotFoundError, ValueError):
            uptime_str = "unknown"
        try:
            content = read_proc_file(self._client, "/proc/loadavg")
            load_avg = content.split()[:3]
            load_str = f"Load: {' '.join(load_avg)}"
        except FileNotFoundError:
            load_str = "Load: unknown"
        total_memory, available_memory = self.proc_reader.get_memory_info()
        used_memory = total_memory - available_memory
        if total_memory > 0:
            mem_percent = (used_memory / total_memory) * 100
            mem_str = f"Mem: {format_bytes(used_memory)}/{format_bytes(total_memory)} ({mem_percent:.1f}%)"
        else:
            mem_str = "Mem: unknown"
        process_count = len(processes)
        # Color header lines:
        stdscr.attron(curses.color_pair(1))
        stdscr.addstr(0, 0, f"PebbleTop - Uptime: {uptime_str}, {load_str}")
        stdscr.addstr(1, 0, f"{mem_str}, Processes: {process_count}")
        stdscr.attroff(curses.color_pair(1))
        stdscr.attron(curses.A_BOLD)
        stdscr.addstr(2, 0, "=" * min(width - 1, 80))
        stdscr.attroff(curses.A_BOLD)
        # Column headers:
        stdscr.attron(curses.color_pair(2))
        header = f"{'PID':>7} {'USER':>8} {'%CPU':>6} {'%MEM':>6} {'RES':>8} {'S':>1} {'THR':>3} {'COMMAND':<30}"
        stdscr.addstr(3, 0, header[: width - 1])
        stdscr.attroff(curses.color_pair(2))

    def draw_processes(self, stdscr: curses.window, processes: list[ProcessInfo]):
        """Draw the process list with color highlighting."""
        height, width = stdscr.getmaxyx()
        if self.sort_column == "cpu_percent":
            processes.sort(key=lambda p: p.cpu_percent, reverse=self.sort_reverse)
        elif self.sort_column == "memory_percent":
            processes.sort(key=lambda p: p.memory_percent, reverse=self.sort_reverse)
        elif self.sort_column == "pid":
            processes.sort(key=lambda p: p.pid, reverse=self.sort_reverse)
        elif self.sort_column == "user":
            processes.sort(key=lambda p: p.user, reverse=self.sort_reverse)
        # Draw processes:
        start_row = 4
        for i, proc in enumerate(processes[: height - start_row - 1]):
            row = start_row + i
            command = proc.cmdline[:30] if len(proc.cmdline) > 30 else proc.cmdline
            line = f"{proc.pid:>7} {proc.user:>8} {proc.cpu_percent:>6.1f} {proc.memory_percent:>6.1f} {format_bytes(proc.memory_kb):>8} {proc.state:>1} {proc.threads:>3} {command:<30}"
            # Highlight high CPU/mem:
            if proc.cpu_percent > 50 or proc.memory_percent > 20:
                stdscr.attron(curses.color_pair(3))
            elif proc.cpu_percent > 10 or proc.memory_percent > 5:
                stdscr.attron(curses.color_pair(4))
            else:
                stdscr.attron(curses.color_pair(0))
            stdscr.addstr(row, 0, line[: width - 1])
            stdscr.attroff(curses.color_pair(0))
            stdscr.attroff(curses.color_pair(3))
            stdscr.attroff(curses.color_pair(4))

    def draw_help(self, stdscr: curses.window):
        """Draw help information."""
        height, width = stdscr.getmaxyx()
        help_text = [
            "PebbleTop Help",
            "",
            "Keys:",
            "  q, Q     - Quit",
            "  c        - Sort by CPU usage",
            "  m        - Sort by memory usage",
            "  p        - Sort by PID",
            "  u        - Sort by user",
            "  r        - Reverse sort order",
            "  t        - Toggle thread display",
            "  h, ?     - Show this help",
            "  <space>  - Refresh display",
            "",
            "Press any key to continue...",
        ]

        stdscr.clear()
        for i, line in enumerate(help_text):
            if i < height - 1:
                stdscr.addstr(i, 0, line[: width - 1])
        stdscr.refresh()
        stdscr.getch()

    def run(self, stdscr: curses.window):
        """Main application loop with color setup."""
        # Configure curses:
        curses.curs_set(0)  # Hide cursor
        stdscr.nodelay(True)  # Non-blocking input
        stdscr.timeout(1000)  # Refresh every second
        # Set up color pairs:
        curses.start_color()
        curses.init_pair(1, curses.COLOR_CYAN, curses.COLOR_BLACK)  # Header
        curses.init_pair(2, curses.COLOR_MAGENTA, curses.COLOR_BLACK)  # Column header
        curses.init_pair(3, curses.COLOR_RED, curses.COLOR_BLACK)  # High CPU/mem
        curses.init_pair(4, curses.COLOR_YELLOW, curses.COLOR_BLACK)  # Medium CPU/mem

        # Set up signal handler for clean exit:
        def signal_handler(signum: int, frame: Any):
            self.running = False

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        while self.running:
            try:
                stdscr.clear()
                processes = self.proc_reader.get_all_processes()
                self.draw_header(stdscr, processes)
                self.draw_processes(stdscr, processes)
                # Status line:
                height, width = stdscr.getmaxyx()
                status = f"Sort: {self.sort_column} ({'desc' if self.sort_reverse else 'asc'}) | Press 'h' for help"
                stdscr.attron(curses.color_pair(2))
                try:
                    stdscr.addstr(height - 1, 0, status[: width - 1], curses.A_REVERSE)
                except curses.error:
                    # Terminal might be too small or other display issue
                    logging.debug(
                        "Failed to display status line due to terminal constraints"
                    )
                stdscr.attroff(curses.color_pair(2))
                stdscr.refresh()
                key = stdscr.getch()
                if key in (ord("q"), ord("Q")):
                    break
                if key == ord("c"):
                    self.sort_column = "cpu_percent"
                elif key == ord("m"):
                    self.sort_column = "memory_percent"
                elif key == ord("p"):
                    self.sort_column = "pid"
                elif key == ord("u"):
                    self.sort_column = "user"
                elif key == ord("r"):
                    self.sort_reverse = not self.sort_reverse
                elif key == ord("t"):
                    self.show_threads = not self.show_threads
                elif key in (ord("h"), ord("?")):
                    self.draw_help(stdscr)
                elif key == ord(" "):
                    continue  # Just refresh
            except KeyboardInterrupt:
                break
            except Exception as e:
                # Log unexpected errors during UI handling
                logging.debug(f"Unexpected error in UI loop: {e}")
                continue
