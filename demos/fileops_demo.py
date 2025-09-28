#!/usr/bin/env python3

"""Demo script showing file operation capabilities."""

import os
import pathlib
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import ops

from pebble_shell.shell import PebbleShell


def run_fileops_demo(tmp_dir: pathlib.Path):
    """Run a demo of file operation commands."""
    print("=== Pebble Debug Shell - File Operations Demo ===\n")

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
    print(f"WARNING: This demo will create and modify files in {tmp_dir}")
    print("Make sure this is safe in your environment!\n")

    commands = [
        (f"Setup - Navigate to {tmp_dir}", f"cd {tmp_dir}"),
        ("Current Directory", "pwd"),
        ("File Creation - Touch empty files", "touch demo1.txt demo2.txt"),
        ("File Creation - Create directory", "mkdir demodir"),
        ("File Creation - Create nested directories", "mkdir -p nested/deep/structure"),
        ("File Operations - Copy file", "cp demo1.txt demo1_copy.txt"),
        ("File Operations - Copy to directory", "cp demo2.txt demodir/"),
        ("File Operations - Move file", "mv demo1_copy.txt renamed.txt"),
        ("Directory Operations - List current contents", "ls -lha"),
        ("Directory Operations - List demodir contents", "ls demodir"),
        ("Copy Operations - Recursive directory copy", "mkdir backup"),
        ("Copy Operations - Copy directory structure", "cp -r nested backup/"),
        ("Copy Operations - Verify copy", "ls -R backup"),
        ("Cleanup Preparation - List all created items", "ls"),
        (
            "Cleanup - Remove individual files",
            "rm demo1.txt demo2.txt renamed.txt doesnotexist.txt",
        ),
        ("Cleanup - Remove directory contents", "rm -r demodir"),
        ("Cleanup - Remove empty directory (should fail)", "rmdir nested"),
        ("Cleanup - Remove non-empty directory", "rm -r nested"),
        ("Cleanup - Remove backup", "rm -r backup"),
        (f"Final Verification - Check {tmp_dir} is clean", f"ls {tmp_dir}"),
        ("Return to Root", "cd /"),
        ("Final Status", "pwd"),
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
        sys.exit(run_fileops_demo(pathlib.Path(tmp_dir)))
