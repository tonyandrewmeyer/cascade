#!/usr/bin/env python3

"""Demo script for the new cpuinfo, meminfo, and fdinfo commands."""

import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import ops

from pebble_shell.shell import PebbleShell


def run_demo():
    """Run the demo for the new system commands."""
    print("Cascade System Commands Demo")
    print("=" * 50)

    socket_path = os.getenv("PEBBLE_SOCKET", os.path.join(tempfile.gettempdir(), ".pebble-demo.socket"))
    shell = PebbleShell(ops.pebble.Client(socket_path=socket_path))
    print(f"Note: Start Pebble server with: pebble run --socket {socket_path}\n")

    demo_commands = [
        ("CPU Information - Compact", "cpuinfo -c"),
        ("CPU Information - Topology", "cpuinfo -t"),
        ("CPU Information - Full", "cpuinfo -a"),
        ("Memory Information - Summary", "meminfo -s"),
        ("Memory Information - Detailed", "meminfo -d"),
        ("Memory Information - Default", "meminfo"),
        ("File Descriptors - Current Process", "fdinfo"),
        ("File Descriptors - All Processes", "fdinfo -a"),
        ("File Descriptors - Specific Type", "fdinfo -t file"),
        ("File Descriptors - Process 1", "fdinfo 1"),
    ]

    print("These commands provide detailed system information:")
    print("   • cpuinfo: CPU architecture, cores, cache, topology")
    print("   • meminfo: Memory usage, swap, kernel memory details")
    print("   • fdinfo: File descriptors, open files, network sockets")
    print()

    for description, command in demo_commands:
        print(f"Running: {command} ({description})")
        shell.run_command(command)
        print()


if __name__ == "__main__":
    run_demo()
