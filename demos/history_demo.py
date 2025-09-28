#!/usr/bin/env python3

"""Demo script showing shell history and alias capabilities."""

import os
import pathlib
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import ops

from pebble_shell.shell import PebbleShell


def run_history_demo(tmp_dir: pathlib.Path):
    """Run a demo of shell history and alias features."""
    print("=== Pebble Debug Shell - History & Alias Demo ===\n")

    socket_path = os.getenv("PEBBLE_SOCKET", os.path.join(tempfile.gettempdir(), ".pebble-demo.socket"))
    shell = PebbleShell(ops.pebble.Client(socket_path=socket_path))

    print(f"Connecting to Pebble at {socket_path}...")
    if not shell.connect():
        print("Failed to connect to Pebble. Make sure Pebble is running.")
        print("To start Pebble server for demo: pebble run --socket /tmp/.pebble-demo.socket")
        return 1

    print("Connected successfully!\n")

    commands = [
        ("Basic Commands - Build up history", "ls"),
        ("Navigation", "pwd"),
        ("System Info", "whoami"),
        ("Network Check", "net"),
        ("File Operations", f"touch {tmp_dir}/demo.txt"),
        ("History - Show all history", "history"),
        ("History - Show last 3 commands", "history 3"),
        ("History - Show statistics", "history -s"),
        ("Aliases - Show default aliases", "alias"),
        ("Aliases - Create custom alias", "alias ll='ls -la'"),
        ("Aliases - Create another alias", "alias mynet='net'"),
        ("Aliases - Show all aliases again", "alias"),
        ("Aliases - Show specific alias", "alias ll"),
        ("Test Aliases - Use ll alias", "ll"),  # Should expand to 'ls -la'
        ("Test Aliases - Use mynet alias", "mynet"),  # Should expand to 'net'
        ("Test Aliases - Use built-in alias", "h 5"),  # Should expand to 'history 5'
        ("History After Aliases", "history 10"),
        (
            "Search History",
            "ls",
        ),  # This would be via history search in interactive mode
        ("Final Statistics", "history -s"),
        ("Cleanup", f"rm {tmp_dir}/demo.txt"),
    ]

    for title, command in commands:
        print(f"=== {title} ===")
        print(f"Command: {command}")
        try:
            result = shell.run_command(command)
            if result is False:
                break  # Exit command was issued
        except Exception as e:
            print(f"Error running '{command}': {e}")
        print()

    print("=== Demo Complete ===")

    return 0


if __name__ == "__main__":
    with tempfile.TemporaryDirectory() as tmp_dir:
        sys.exit(run_history_demo(pathlib.Path(tmp_dir)))
