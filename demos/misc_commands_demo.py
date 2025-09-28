#!/usr/bin/env python3

"""Demo script showing miscellaneous command capabilities."""

import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import ops

from pebble_shell.shell import PebbleShell


def run_misc_commands_demo():
    """Run a demo of medium-priority commands."""
    print("=== Pebble Debug Shell - Misc Commands Demo ===\n")

    socket_path = os.getenv(
        "PEBBLE_SOCKET", os.path.join(tempfile.gettempdir(), ".pebble-demo.socket")
    )
    shell = PebbleShell(ops.pebble.Client(socket_path=socket_path))

    print(f"Connecting to Pebble at {socket_path}...")
    if not shell.connect():
        print("Failed to connect to Pebble. Make sure Pebble is running.")
        print(
            "To start Pebble server for demo: pebble run --socket /tmp/.pebble-demo.socket"
        )
        return 1

    print("Connected successfully!\n")

    commands = [
        ("Resource Limits - Show All Limits", "ulimit -a"),
        ("Resource Limits - Show File Descriptor Limit", "ulimit -n"),
        ("Navigate to /etc for File Processing", "cd /etc"),
        ("Text Processing - Sort passwd File", "sort passwd"),
        ("Text Processing - Reverse Sort passwd", "sort -r passwd"),
        ("Text Processing - Extract Usernames (Field 1)", "cut -f 1 -d : passwd"),
        (
            "Text Processing - Extract User and Home (Fields 1,6)",
            "cut -f 1,6 -d : passwd",
        ),
        ("Text Processing - Extract First 10 Characters", "cut -c 1-10 passwd"),
        ("Combined Example - Sort and Extract", "sort passwd | cut -f 1 -d :"),
        ("Word Count", "wc passwd"),
        ("Return to Root Directory", "cd /"),
        ("Final Status Check", "pwd"),
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
    sys.exit(run_misc_commands_demo())
