#!/usr/bin/env python3

"""Demo script showing for loop functionality in the Cascade shell."""

import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import ops

from pebble_shell.shell import PebbleShell


def demo_for_loops():
    """Demonstrate for loop functionality."""
    print("=== Cascade Shell For Loop Demo ===\n")

    socket_path = os.getenv(
        "PEBBLE_SOCKET", os.path.join(tempfile.gettempdir(), ".pebble-demo.socket")
    )
    shell = PebbleShell(ops.pebble.Client(socket_path=socket_path))

    print("1. Simple for loop with space-separated values:")
    command = 'for i in 1 2 3 4 5; do echo "Processing item: $i"; done'
    print(f"Command: {command}")
    shell.run_command(command)
    print()

    print("2. For loop with quoted string:")
    command = (
        'for service in "web" "api" "db"; do echo "Starting service: $service"; done'
    )
    print(f"Command: {command}")
    shell.run_command(command)
    print()

    print("3. For loop with parenthesized list:")
    command = 'for port in (80 443 8080 8443); do echo "Checking port: $port"; done'
    print(f"Command: {command}")
    shell.run_command(command)
    print()

    print("4. For loop with brace expansion:")
    command = 'for env in {dev,staging,prod}; do echo "Deploying to: $env"; done'
    print(f"Command: {command}")
    shell.run_command(command)
    print()

    print("5. For loop with multiple commands:")
    command = (
        'for file in file1 file2 file3; do echo "Processing $file"; ls -la $file; done'
    )
    print(f"Command: {command}")
    shell.run_command(command)
    print()

    print("6. For loop with pebble commands:")
    command = "for service in web api db; do pebble-start $service; done"
    print(f"Command: {command}")
    shell.run_command(command)
    print()


if __name__ == "__main__":
    demo_for_loops()
