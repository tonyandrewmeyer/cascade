"""Utilities for reading and parsing /proc filesystem files through Pebble client.

This module provides common functionality for reading various /proc files
that are frequently accessed by system and network monitoring commands.
"""

from __future__ import annotations

import socket
import struct
from typing import TYPE_CHECKING

import ops

if TYPE_CHECKING:
    import shimmer

    PebbleClient = ops.pebble.Client | shimmer.PebbleCliClient


class ProcReadError(Exception):
    """Exception raised when reading /proc files fails."""

    def __init__(self, path: str, message: str):
        self.path: str = path
        self.message: str = message
        super().__init__(f"Error reading {path}: {message}")


def read_proc_file(client: PebbleClient, path: str) -> str:
    """Read a /proc file and return its content as string.

    Args:
        client: Pebble client instance
        path: Path to the /proc file (e.g., "/proc/version")

    Returns:
        Content of the file as a string

    Raises:
        ProcReadError: If the file cannot be read
    """
    try:
        with client.pull(path) as file:
            content = file.read()

        if isinstance(content, bytes):
            content = content.decode("utf-8", errors="replace")

        return content
    except (ops.pebble.PathError, ops.pebble.APIError) as e:
        raise ProcReadError(path, str(e)) from e


def parse_proc_table(content: str, skip_header_lines: int = 1) -> list[list[str]]:
    """Parse /proc table format into rows of columns.

    Many /proc files have tabular data with headers. This function
    parses them into a list of rows, where each row is a list of columns.

    Args:
        content: Raw content from /proc file
        skip_header_lines: Number of header lines to skip (default: 1)

    Returns:
        List of rows, where each row is a list of column values
    """
    lines = content.splitlines()

    # Skip header lines
    data_lines = lines[skip_header_lines:] if skip_header_lines > 0 else lines

    rows = []
    for raw_line in data_lines:
        line = raw_line.strip()
        if line:  # Skip empty lines
            # Split on whitespace, preserving structure
            columns = line.split()
            rows.append(columns)

    return rows


def read_proc_status_field(client: PebbleClient, pid: str, field: str) -> str | None:
    """Read a specific field from /proc/{pid}/status.

    Args:
        client: Pebble client instance
        pid: Process ID (or 'self' for current process)
        field: Field name to extract (e.g., 'Uid', 'Gid', 'Name')

    Returns:
        Value of the field, or None if not found

    Raises:
        ProcReadError: If the status file cannot be read
    """
    try:
        content = read_proc_file(client, f"/proc/{pid}/status")

        for line in content.splitlines():
            if line.startswith(f"{field}:"):
                # Extract value after the colon, split by whitespace
                parts = line.split(":", 1)[1].strip().split()
                return parts[0] if parts else None

        return None
    except ProcReadError:
        raise


def read_proc_status_fields(
    client: PebbleClient, pid: str, fields: list[str]
) -> dict[str, str]:
    """Read multiple fields from /proc/{pid}/status efficiently.

    Args:
        client: Pebble client instance
        pid: Process ID (or 'self' for current process)
        fields: List of field names to extract

    Returns:
        Dictionary mapping field names to their values

    Raises:
        ProcReadError: If the status file cannot be read
    """
    try:
        content = read_proc_file(client, f"/proc/{pid}/status")
        result = {}

        for line in content.splitlines():
            for field in fields:
                if line.startswith(f"{field}:"):
                    # Extract value after the colon, split by whitespace
                    parts = line.split(":", 1)[1].strip().split()
                    if parts:
                        result[field] = parts[0]
                    break

        return result
    except ProcReadError:
        raise


def read_proc_environ(client: PebbleClient, pid: str) -> dict[str, str]:
    """Read environment variables from /proc/{pid}/environ.

    Args:
        client: Pebble client instance
        pid: Process ID (or 'self' for current process)

    Returns:
        Dictionary of environment variables

    Raises:
        ProcReadError: If the environ file cannot be read
    """
    try:
        content = read_proc_file(client, f"/proc/{pid}/environ")

        # Environment variables are null-separated
        env_vars = {}
        for raw_var in content.split("\x00"):
            var = raw_var.strip()
            if var and "=" in var:
                key, value = var.split("=", 1)
                env_vars[key] = value
            elif var:  # Variable without value
                env_vars[var] = ""

        return env_vars
    except ProcReadError:
        raise


def parse_network_address(hex_addr: str) -> str:
    """Convert hex network address:port to readable format.

    Network addresses in /proc/net/* files are stored as hex values
    in little-endian format.

    Args:
        hex_addr: Hex address in format "XXXXXXXX:XXXX" (IP:port)

    Returns:
        Readable address in format "IP:port" (e.g., "127.0.0.1:80")
    """
    if ":" not in hex_addr:
        return hex_addr

    try:
        ip_hex, port_hex = hex_addr.split(":", 1)

        # Convert little-endian hex to IP
        ip_int = int(ip_hex, 16)
        ip_bytes = struct.pack("<I", ip_int)
        ip_addr = socket.inet_ntoa(ip_bytes)

        # Convert port
        port = int(port_hex, 16)

        return f"{ip_addr}:{port}"
    except (OSError, ValueError, struct.error):
        # If parsing fails, return original
        return hex_addr


def parse_tcp_state(state_hex: str) -> str:
    """Convert TCP state from hex to readable format.

    Args:
        state_hex: Hex representation of TCP state

    Returns:
        Human-readable TCP state name
    """
    tcp_states = {
        "01": "ESTABLISHED",
        "02": "SYN_SENT",
        "03": "SYN_RECV",
        "04": "FIN_WAIT1",
        "05": "FIN_WAIT2",
        "06": "TIME_WAIT",
        "07": "CLOSE",
        "08": "CLOSE_WAIT",
        "09": "LAST_ACK",
        "0A": "LISTEN",
        "0B": "CLOSING",
    }

    return tcp_states.get(state_hex.upper(), f"UNKNOWN({state_hex})")


def parse_proc_net_dev(client: PebbleClient) -> list[dict[str, int | str]]:
    """Parse /proc/net/dev for network interface statistics.

    Args:
        client: Pebble client instance

    Returns:
        List of dictionaries containing interface statistics

    Raises:
        ProcReadError: If the file cannot be read or parsed
    """
    try:
        content = read_proc_file(client, "/proc/net/dev")
        interfaces = []

        lines = content.splitlines()
        for line in lines[2:]:  # Skip first two header lines
            if ":" in line:
                parts = line.split(":")
                interface = parts[0].strip()
                stats = parts[1].split()

                if len(stats) >= 10:
                    interfaces.append(
                        {
                            "interface": interface,
                            "rx_bytes": int(stats[0]),
                            "rx_packets": int(stats[1]),
                            "rx_errors": int(stats[2]),
                            "rx_dropped": int(stats[3]),
                            "tx_bytes": int(stats[8]),
                            "tx_packets": int(stats[9]),
                            "tx_errors": int(stats[10]) if len(stats) > 10 else 0,
                            "tx_dropped": int(stats[11]) if len(stats) > 11 else 0,
                        }
                    )

        return interfaces
    except (ProcReadError, ValueError, IndexError) as e:
        raise ProcReadError(
            "/proc/net/dev", f"Failed to parse network interfaces: {e}"
        ) from e


def parse_proc_net_connections(
    client: PebbleClient, protocol: str
) -> list[dict[str, str]]:
    """Parse /proc/net/{tcp,udp,unix} for network connections.

    Args:
        client: Pebble client instance
        protocol: Protocol type ('tcp', 'udp', or 'unix')

    Returns:
        List of dictionaries containing connection information

    Raises:
        ProcReadError: If the file cannot be read or parsed
    """
    if protocol not in ["tcp", "udp", "unix"]:
        raise ValueError(f"Unsupported protocol: {protocol}")

    try:
        content = read_proc_file(client, f"/proc/net/{protocol}")

        if protocol == "unix":
            return _parse_unix_connections(content)
        return _parse_inet_connections(content, protocol)

    except ProcReadError:
        raise
    except (ValueError, IndexError) as e:
        raise ProcReadError(
            f"/proc/net/{protocol}", f"Failed to parse connections: {e}"
        ) from e


def _parse_inet_connections(content: str, protocol: str) -> list[dict[str, str]]:
    """Parse TCP/UDP connection data."""
    connections = []
    lines = content.splitlines()[1:]  # Skip header

    for line in lines:
        parts = line.split()
        if len(parts) >= 3:
            connection = {
                "protocol": protocol.upper(),
                "local_address": parse_network_address(parts[1]),
                "remote_address": parse_network_address(parts[2]),
            }

            # Add state for TCP connections
            if protocol == "tcp" and len(parts) >= 4:
                connection["state"] = parse_tcp_state(parts[3])

            connections.append(connection)

    return connections


def _parse_unix_connections(content: str) -> list[dict[str, str]]:
    """Parse UNIX domain socket data."""
    connections = []
    lines = content.splitlines()[1:]  # Skip header

    for line in lines:
        parts = line.split()
        if len(parts) >= 6:
            socket_type = "STREAM" if parts[4] == "0001" else "DGRAM"
            state = "CONNECTED" if parts[5] == "01" else "UNCONNECTED"
            path = parts[7] if len(parts) > 7 else "<unnamed>"

            connections.append(
                {
                    "protocol": "UNIX",
                    "type": socket_type,
                    "state": state,
                    "path": path,
                }
            )

    return connections


def parse_proc_route(client: PebbleClient) -> list[dict[str, str]]:
    """Parse /proc/net/route for routing table information.

    Args:
        client: Pebble client instance

    Returns:
        List of dictionaries containing route information

    Raises:
        ProcReadError: If the file cannot be read or parsed
    """
    try:
        content = read_proc_file(client, "/proc/net/route")
        routes = []

        lines = content.splitlines()[1:]  # Skip header
        for line in lines:
            parts = line.split()
            if len(parts) >= 8:
                flags = int(parts[3])
                flag_str = ""
                if flags & 0x0001:
                    flag_str += "U"  # Up
                if flags & 0x0002:
                    flag_str += "G"  # Gateway
                if flags & 0x0004:
                    flag_str += "H"  # Host

                routes.append(
                    {
                        "interface": parts[0],
                        "destination": _hex_to_ip(parts[1]),
                        "gateway": _hex_to_ip(parts[2]),
                        "flags": flag_str,
                        "metric": parts[6],
                        "mask": _hex_to_ip(parts[7]),
                    }
                )

        return routes
    except (ProcReadError, ValueError, IndexError) as e:
        raise ProcReadError(
            "/proc/net/route", f"Failed to parse routing table: {e}"
        ) from e


def parse_proc_meminfo(client: PebbleClient) -> dict[str, int]:
    """Parse /proc/meminfo for memory statistics.

    Args:
        client: Pebble client instance

    Returns:
        Dictionary mapping memory field names to values in KB

    Raises:
        ProcReadError: If the file cannot be read or parsed
    """
    try:
        content = read_proc_file(client, "/proc/meminfo")
        memory_info: dict[str, int] = {}

        for line in content.splitlines():
            if ":" in line:
                parts = line.split(":", 1)
                if len(parts) >= 2:
                    key = parts[0].strip()
                    value_str = parts[1].strip()

                    # Extract numeric value (remove 'kB' suffix if present)
                    if value_str.endswith(" kB"):
                        value_str = value_str[:-3].strip()
                    elif " " in value_str:
                        # Take first part if there are multiple words
                        value_str = value_str.split()[0]

                    try:
                        value = int(value_str)
                        memory_info[key] = value
                    except ValueError:
                        continue

        return memory_info
    except (ProcReadError, ValueError) as e:
        raise ProcReadError("/proc/meminfo", f"Failed to parse memory info: {e}") from e


def parse_proc_uptime(client: PebbleClient) -> dict[str, float]:
    """Parse /proc/uptime for system uptime information.

    Args:
        client: Pebble client instance

    Returns:
        Dictionary containing uptime and idle time in seconds

    Raises:
        ProcReadError: If the file cannot be read or parsed
    """
    try:
        content = read_proc_file(client, "/proc/uptime")
        parts = content.strip().split()

        if len(parts) >= 2:
            return {"uptime_seconds": float(parts[0]), "idle_seconds": float(parts[1])}
        else:
            raise ValueError("Invalid uptime format")

    except (ProcReadError, ValueError, IndexError) as e:
        raise ProcReadError("/proc/uptime", f"Failed to parse uptime: {e}") from e


def parse_proc_loadavg(client: PebbleClient) -> dict[str, str | int]:
    """Parse /proc/loadavg for system load averages.

    Args:
        client: Pebble client instance

    Returns:
        Dictionary containing load averages and process counts

    Raises:
        ProcReadError: If the file cannot be read or parsed
    """
    try:
        content = read_proc_file(client, "/proc/loadavg")
        parts = content.strip().split()

        if len(parts) >= 5:
            # Extract running/total processes from the fourth field (e.g., "2/305")
            processes = parts[3].split("/") if "/" in parts[3] else ["0", "0"]

            return {
                "load_1min": parts[0],
                "load_5min": parts[1],
                "load_15min": parts[2],
                "running_processes": int(processes[0]) if processes[0].isdigit() else 0,
                "total_processes": int(processes[1]) if processes[1].isdigit() else 0,
                "last_pid": int(parts[4]) if parts[4].isdigit() else 0,
            }
        else:
            raise ValueError("Invalid loadavg format")

    except (ProcReadError, ValueError, IndexError) as e:
        raise ProcReadError(
            "/proc/loadavg", f"Failed to parse load average: {e}"
        ) from e


def parse_proc_arp(client: PebbleClient) -> list[dict[str, str]]:
    """Parse /proc/net/arp for ARP table information.

    Args:
        client: Pebble client instance

    Returns:
        List of dictionaries containing ARP entries

    Raises:
        ProcReadError: If the file cannot be read or parsed
    """
    try:
        content = read_proc_file(client, "/proc/net/arp")
        arp_entries = []

        lines = content.splitlines()[1:]  # Skip header
        for line in lines:
            parts = line.split()
            if len(parts) >= 6:
                arp_entries.append(
                    {
                        "ip_address": parts[0],
                        "hw_type": parts[1],
                        "flags": parts[2],
                        "hw_address": parts[3],
                        "mask": parts[4],
                        "device": parts[5],
                    }
                )

        return arp_entries
    except (ProcReadError, ValueError, IndexError) as e:
        raise ProcReadError("/proc/net/arp", f"Failed to parse ARP table: {e}") from e


def _hex_to_ip(hex_ip: str) -> str:
    """Convert hex IP address to dotted decimal format."""
    try:
        if hex_ip == "00000000":
            return "0.0.0.0"  # noqa: S104 - legitimate use for default route/any interface

        ip_int = int(hex_ip, 16)
        ip_bytes = struct.pack("<I", ip_int)
        return socket.inet_ntoa(ip_bytes)
    except (OSError, ValueError, struct.error):
        return hex_ip


def get_user_name_for_uid(client: PebbleClient, uid: str) -> str | None:
    """Get username from /etc/passwd for a given UID.

    Args:
        client: Pebble client instance
        uid: User ID as string

    Returns:
        Username if found, None otherwise
    """
    try:
        content = read_proc_file(client, "/etc/passwd")

        for line in content.splitlines():
            if line.strip():
                parts = line.split(":")
                if len(parts) >= 3 and parts[2] == uid:
                    return parts[0]

        return None
    except ProcReadError:
        return None


def get_group_name_for_gid(client: PebbleClient, gid: str) -> str | None:
    """Get group name from /etc/group for a given GID.

    Args:
        client: Pebble client instance
        gid: Group ID as string

    Returns:
        Group name if found, None otherwise
    """
    try:
        content = read_proc_file(client, "/etc/group")

        for line in content.splitlines():
            if line.strip():
                parts = line.split(":")
                if len(parts) >= 3 and parts[2] == gid:
                    return parts[0]

        return None
    except ProcReadError:
        return None


def parse_proc_stat(
    client: PebbleClient,
) -> dict[str, dict[str, int] | dict[str, dict[str, int]]]:
    """Parse /proc/stat for CPU and system statistics.

    Args:
        client: Pebble client instance

    Returns:
        Dictionary containing CPU statistics and system counters.
        Structure: {"cpu": {...}, "cpus": {cpu_id: {...}}, "system": {...}}

    Raises:
        ProcReadError: If the file cannot be read or parsed
    """
    try:
        content = read_proc_file(client, "/proc/stat")
        stats: dict[str, dict[str, int]] = {"cpu": {}, "cpus": {}, "system": {}}

        for line in content.splitlines():
            parts = line.split()
            if not parts:
                continue

            if parts[0] == "cpu":
                # Overall CPU statistics
                if len(parts) >= 5:
                    stats["cpu"] = {
                        "user": int(parts[1]),
                        "nice": int(parts[2]),
                        "system": int(parts[3]),
                        "idle": int(parts[4]),
                        "iowait": int(parts[5]) if len(parts) > 5 else 0,
                        "irq": int(parts[6]) if len(parts) > 6 else 0,
                        "softirq": int(parts[7]) if len(parts) > 7 else 0,
                        "steal": int(parts[8]) if len(parts) > 8 else 0,
                        "guest": int(parts[9]) if len(parts) > 9 else 0,
                        "guest_nice": int(parts[10]) if len(parts) > 10 else 0,
                    }
            elif parts[0].startswith("cpu") and parts[0][3:].isdigit():
                # Per-CPU statistics
                cpu_num = parts[0][3:]
                if len(parts) >= 5:
                    stats["cpus"][cpu_num] = {
                        "user": int(parts[1]),
                        "nice": int(parts[2]),
                        "system": int(parts[3]),
                        "idle": int(parts[4]),
                        "iowait": int(parts[5]) if len(parts) > 5 else 0,
                        "irq": int(parts[6]) if len(parts) > 6 else 0,
                        "softirq": int(parts[7]) if len(parts) > 7 else 0,
                        "steal": int(parts[8]) if len(parts) > 8 else 0,
                        "guest": int(parts[9]) if len(parts) > 9 else 0,
                        "guest_nice": int(parts[10]) if len(parts) > 10 else 0,
                    }
            elif (
                parts[0]
                in [
                    "intr",
                    "ctxt",
                    "btime",
                    "processes",
                    "procs_running",
                    "procs_blocked",
                    "softirq",
                ]
                and len(parts) >= 2
            ):
                # System-wide statistics
                try:
                    stats["system"][parts[0]] = int(parts[1])
                except ValueError:
                    continue

        return stats
    except (ProcReadError, ValueError, IndexError) as e:
        raise ProcReadError("/proc/stat", f"Failed to parse CPU statistics: {e}") from e


def parse_proc_vmstat(client: PebbleClient) -> dict[str, int]:
    """Parse /proc/vmstat for virtual memory statistics.

    Args:
        client: Pebble client instance

    Returns:
        Dictionary mapping vmstat field names to values

    Raises:
        ProcReadError: If the file cannot be read or parsed
    """
    try:
        content = read_proc_file(client, "/proc/vmstat")
        vmstat_info: dict[str, int] = {}

        for line in content.splitlines():
            if " " in line:
                parts = line.split(" ", 1)
                if len(parts) >= 2:
                    key = parts[0].strip()
                    value_str = parts[1].strip()

                    try:
                        value = int(value_str)
                        vmstat_info[key] = value
                    except ValueError:
                        continue

        return vmstat_info
    except (ProcReadError, ValueError) as e:
        raise ProcReadError("/proc/vmstat", f"Failed to parse vmstat: {e}") from e


def parse_proc_diskstats(client: PebbleClient) -> list[dict[str, int | str]]:
    """Parse /proc/diskstats for disk I/O statistics.

    Args:
        client: Pebble client instance

    Returns:
        List of dictionaries containing disk statistics for each device

    Raises:
        ProcReadError: If the file cannot be read or parsed
    """
    try:
        content = read_proc_file(client, "/proc/diskstats")
        disk_stats: list[dict[str, int | str]] = []

        for line in content.splitlines():
            line = line.strip()
            if not line:
                continue

            parts = line.split()
            if len(parts) >= 14:
                try:
                    disk_stats.append(
                        {
                            "major": int(parts[0]),
                            "minor": int(parts[1]),
                            "device": parts[2],
                            "reads": int(parts[3]),
                            "read_merges": int(parts[4]),
                            "read_sectors": int(parts[5]),
                            "read_time": int(parts[6]),
                            "writes": int(parts[7]),
                            "write_merges": int(parts[8]),
                            "write_sectors": int(parts[9]),
                            "write_time": int(parts[10]),
                            "io_in_progress": int(parts[11]),
                            "io_time": int(parts[12]),
                            "io_weighted_time": int(parts[13]),
                        }
                    )
                except (ValueError, IndexError):
                    continue

        return disk_stats
    except (ProcReadError, ValueError, IndexError) as e:
        raise ProcReadError(
            "/proc/diskstats", f"Failed to parse disk statistics: {e}"
        ) from e


def parse_proc_cpuinfo(client: PebbleClient) -> dict[str, int | list[dict[str, str]]]:
    """Parse /proc/cpuinfo for CPU information.

    Args:
        client: Pebble client instance

    Returns:
        Dictionary containing CPU count and detailed CPU information

    Raises:
        ProcReadError: If the file cannot be read or parsed
    """
    try:
        content = read_proc_file(client, "/proc/cpuinfo")
        cpu_count = 0
        cpus: list[dict[str, str]] = []
        current_cpu: dict[str, str] = {}

        for line in content.splitlines():
            line = line.strip()
            if not line:
                # Empty line indicates end of a CPU block
                if current_cpu:
                    cpus.append(current_cpu)
                    current_cpu = {}
                continue

            if ":" in line:
                key, value = line.split(":", 1)
                key = key.strip()
                value = value.strip()

                if key == "processor":
                    # New processor entry - save any existing CPU first
                    if current_cpu:
                        cpus.append(current_cpu)
                        current_cpu = {}
                    cpu_count += 1

                current_cpu[key] = value

        # Add the last CPU if it exists
        if current_cpu:
            cpus.append(current_cpu)

        return {"cpu_count": cpu_count, "cpus": cpus}
    except (ProcReadError, ValueError) as e:
        raise ProcReadError("/proc/cpuinfo", f"Failed to parse CPU info: {e}") from e


def get_process_tty(client: PebbleClient, pid: str) -> str:
    """Get TTY information for a process.

    Args:
        client: Pebble client instance
        pid: Process ID as a string

    Returns:
        TTY device name (e.g., "pts/0") or "?" if no TTY

    Raises:
        ProcReadError: If the /proc/{pid}/stat file cannot be read
    """
    try:
        stat_content = read_proc_file(client, f"/proc/{pid}/stat")
        parts = stat_content.strip().split()
        if len(parts) >= 7:
            tty_nr = parts[6]
            if tty_nr != "0":
                # Convert TTY number to device name (simplified)
                return f"pts/{int(tty_nr) % 256}"
            return "?"
        return "?"
    except (ProcReadError, ValueError) as e:
        raise ProcReadError(
            f"/proc/{pid}/stat", f"Failed to parse TTY info: {e}"
        ) from e


def get_boot_time_from_stat(client: PebbleClient) -> int:
    """Get system boot time from /proc/stat btime field.

    Args:
        client: Pebble client instance

    Returns:
        Boot time as Unix timestamp

    Raises:
        ProcReadError: If boot time cannot be determined
    """
    try:
        content = read_proc_file(client, "/proc/stat")
        for line in content.splitlines():
            if line.startswith("btime"):
                parts = line.split()
                if len(parts) >= 2:
                    return int(parts[1])
        raise ValueError("btime line not found in /proc/stat")
    except (ValueError, IndexError) as e:
        raise ProcReadError("/proc/stat", f"Failed to parse boot time: {e}") from e


def parse_proc_limits_file(
    client: PebbleClient, pid: str = "self"
) -> dict[str, dict[str, str]]:
    """Parse /proc/{pid}/limits file for resource limits.

    Args:
        client: Pebble client instance
        pid: Process ID (default: "self")

    Returns:
        Dictionary mapping limit names to their soft/hard values and units

    Raises:
        ProcReadError: If limits cannot be read or parsed
    """
    try:
        content = read_proc_file(client, f"/proc/{pid}/limits")
        lines = content.splitlines()

        if not lines:
            raise ValueError("Empty limits file")

        limits: dict[str, dict[str, str]] = {}

        # Skip header line
        for line in lines[1:]:
            if line.strip():
                parts = line.split()
                if len(parts) >= 4:
                    limit_name = " ".join(parts[:-3])
                    soft_limit = parts[-3]
                    hard_limit = parts[-2]
                    units = parts[-1]
                    limits[limit_name] = {
                        "soft": soft_limit,
                        "hard": hard_limit,
                        "units": units,
                    }

        return limits
    except (ValueError, IndexError) as e:
        raise ProcReadError(
            f"/proc/{pid}/limits", f"Failed to parse limits: {e}"
        ) from e


def parse_proc_mounts_file(client: PebbleClient) -> list[dict[str, str]]:
    """Parse /proc/mounts to get mount information.

    Args:
        client: Pebble client instance

    Returns:
        List of mount dictionaries with device, mountpoint, fstype, options fields

    Raises:
        ProcReadError: If mounts cannot be read or parsed
    """
    try:
        content = read_proc_file(client, "/proc/mounts")
        mounts = []

        for line in content.splitlines():
            line = line.strip()
            if line:
                parts = line.split()
                if len(parts) >= 4:
                    mount_info = {
                        "device": parts[0],
                        "mountpoint": parts[1],
                        "fstype": parts[2],
                        "options": parts[3],
                    }
                    mounts.append(mount_info)

        return mounts
    except (ValueError, IndexError) as e:
        raise ProcReadError("/proc/mounts", f"Failed to parse mounts: {e}") from e


def get_hostname_from_proc_sys(client: PebbleClient) -> str:
    """Get hostname from /proc/sys/kernel/hostname.

    Args:
        client: Pebble client instance

    Returns:
        System hostname

    Raises:
        ProcReadError: If hostname cannot be read
    """
    try:
        content = read_proc_file(client, "/proc/sys/kernel/hostname")
        return content.strip()
    except Exception as e:
        raise ProcReadError(
            "/proc/sys/kernel/hostname", f"Failed to read hostname: {e}"
        ) from e


def read_proc_cmdline(client: PebbleClient, pid: str) -> str:
    """Read process command line from /proc/{pid}/cmdline.

    Args:
        client: Pebble client instance
        pid: Process ID (or 'self' for current process)

    Returns:
        Command line with null bytes replaced by spaces, or "unknown" if unavailable

    Raises:
        ProcReadError: If the cmdline file cannot be read
    """
    try:
        content = read_proc_file(client, f"/proc/{pid}/cmdline")
        if content:
            return content.replace("\x00", " ").strip()
        return "unknown"
    except ProcReadError:
        return "unknown"
