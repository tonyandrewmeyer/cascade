#!/usr/bin/env python3

"""Demo script showing built-in command capabilities."""

import os
import sys
import tempfile

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import ops

from pebble_shell.shell import PebbleShell


def run_builtin_demo():
    """Run a demo of built-in commands."""
    print("=== Pebble Debug Shell - Built-in Commands Demo ===\n")

    socket_path = os.getenv(
        "PEBBLE_SOCKET", os.path.join(tempfile.gettempdir(), ".pebble-demo.socket")
    )
    shell = PebbleShell(ops.pebble.Client(socket_path=socket_path))

    print(f"Connecting to Pebble at {socket_path}...")
    print("Note: Start Pebble server with: pebble run --socket", socket_path)
    print("Or set PEBBLE_SOCKET environment variable to use custom socket path.\n")
    if not shell.connect():
        print("Failed to connect to Pebble. Please start a Pebble server first:")
        print(f"  pebble run --socket {socket_path}")
        return 1

    print("Connected successfully!\n")

    commands = [
        ("Print Current Directory", "pwd"),
        ("Show Current User", "whoami"),
        ("Show User/Group IDs", "id"),
        ("List Root Directory", "ls /"),
        ("Change to /etc", "cd /etc"),
        ("Print Working Directory", "pwd"),
        ("List Current Directory", "ls"),
        ("Show Environment Variables", "env"),
        ("Echo Test Message", "echo Hello from Pebble shell!"),
        ("Count Lines in passwd", "wc -l passwd"),
        ("Search for root in passwd", "grep root passwd"),
        ("Change Back to Root", "cd /"),
        ("Final Directory Check", "pwd"),
    ]

    for title, command in commands:
        print(f"=== {title} ===")
        print(f"Command: {command}")
        try:
            shell.run_command(command)
        except Exception as e:
            print(f"Error running '{command}': {e}")
        print()

    print("=== Demo Complete ===")

    return 0


if __name__ == "__main__":
    sys.exit(run_builtin_demo())
