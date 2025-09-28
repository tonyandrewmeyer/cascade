#!/usr/bin/env python3

"""Demo script showing network command capabilities."""

import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import ops

from pebble_shell.shell import PebbleShell


def run_network_demo():
    """Run a demo of network commands."""
    print("=== Pebble Debug Shell - Network Commands Demo ===\n")

    socket_path = os.getenv("PEBBLE_SOCKET", os.path.join(tempfile.gettempdir(), ".pebble-demo.socket"))
    shell = PebbleShell(ops.pebble.Client(socket_path=socket_path))

    print(f"Connecting to Pebble at {socket_path}...")
    if not shell.connect():
        print("Failed to connect to Pebble. Make sure Pebble is running.")
        print("To start Pebble server for demo: pebble run --socket /tmp/.pebble-demo.socket")
        return 1

    print("Connected successfully!\n")

    commands = [
        ("Network Interface Statistics", "net"),
        ("TCP Connections", "netstat tcp"),
        ("UDP Connections", "netstat udp"),
        ("UNIX Sockets", "netstat unix"),
        ("Socket Statistics Summary", "ss"),
        ("Routing Table", "route"),
        ("ARP Table", "arp"),
    ]

    for title, command in commands:
        print(f"=== {title} ===")
        try:
            shell.run_command(command)
        except Exception as e:
            print(f"Error running '{command}': {e}")
        print()

    print("=== Demo Complete ===")
    return 0


if __name__ == "__main__":
    sys.exit(run_network_demo())
