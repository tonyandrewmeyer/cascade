#!/usr/bin/env python3

"""Demo script showing shell features like pipes, redirection, and chaining."""

import os
import pathlib
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import ops

from pebble_shell.shell import PebbleShell


def run_shell_features_demo(tmp_dir: pathlib.Path):
    """Run a demo of shell features."""
    print("=== Pebble Debug Shell - Features Demo ===\n")

    socket_path = os.getenv("PEBBLE_SOCKET", os.path.join(tempfile.gettempdir(), ".pebble-demo.socket"))
    shell = PebbleShell(ops.pebble.Client(socket_path=socket_path))

    print(f"Connecting to Pebble at {socket_path}...")
    if not shell.connect():
        print("Failed to connect to Pebble. Make sure Pebble is running.")
        print("To start Pebble server for demo: pebble run --socket /tmp/.pebble-demo.socket")
        return 1

    print("Connected successfully!\n")
    print(f"WARNING: This demo will create and modify files in {tmp_dir}")
    print("Make sure this is safe in your environment!\n")

    commands = [
        (f"Setup - Navigate to {tmp_dir}", f"cd {tmp_dir}"),
        (
            "Setup - Create test data",
            "echo 'apple\nbanana\ncherry\napricot' > fruits.txt",
        ),
        (
            "Setup - Create more test data",
            "echo 'user1:1001:admin\nuser2:1002:users\nuser3:1003:admin' > users.txt",
        ),
        ("Variable Assignment - Set custom variable", "MYVAR=hello"),
        ("Variable Usage - Use variable in command", "echo $MYVAR world"),
        ("Environment - Show current user", "echo Current user: $USER"),
        ("Environment - Show working directory", "echo Working in: $PWD"),
        ("Pipes - Basic pipe operation", "cat fruits.txt | grep a"),
        ("Pipes - Multiple stage pipeline", "cat fruits.txt | grep a | sort"),
        ("Pipes - Complex pipeline with wc", "cat fruits.txt | grep a | wc -l"),
        ("Redirection - Output to file", "ps > processes.txt"),
        ("Redirection - Append to file", "echo 'Additional line' >> fruits.txt"),
        ("Redirection - Show appended content", "cat fruits.txt"),
        ("Input Redirection - Process file input", "wc < fruits.txt"),
        ("Input Redirection - Sort from file", "sort < fruits.txt"),
        ("Text Processing - Extract usernames", "cat users.txt | cut -f1 -d:"),
        ("Text Processing - Find admin users", "cat users.txt | grep admin"),
        ("Text Processing - Count admin users", "cat users.txt | grep admin | wc -l"),
        (
            "Text Processing - Admin UIDs only",
            "cat users.txt | grep admin | cut -f2 -d:",
        ),
        ("Globbing - List text files", "ls *.txt"),
        ("Globbing - Process multiple files", "wc *.txt"),
        ("Command Chaining - Success chain", "echo 'Success test' && echo 'This runs'"),
        (
            "Command Chaining - Failure chain",
            "ls /nonexistent || echo 'Fallback executed'",
        ),
        ("Command Chaining - Sequential", "echo 'First'; echo 'Second'; echo 'Third'"),
        (
            "Complex Example - User analysis",
            "cat users.txt | cut -f3 -d: | sort | uniq -c || echo 'Analysis failed'",
        ),
        (
            "Complex Example - Process monitoring",
            "ps | grep -v PID | wc -l > process_count.txt && cat process_count.txt",
        ),
        ("File Operations with Pipes", "ls -la | grep '^-' | wc -l"),
        (
            "Combined Operations",
            "echo 'Test content' > test.log && cat test.log | wc && rm test.log",
        ),
        ("Verification - List created files", "ls *.txt"),
        ("Verification - Show file contents", "head -3 processes.txt"),
        (
            "Cleanup - Remove test files",
            "rm fruits.txt users.txt processes.txt process_count.txt",
        ),
        ("Final Check", "ls *.txt || echo 'All test files cleaned up'"),
        ("Return to root", "cd /"),
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
        sys.exit(run_shell_features_demo(pathlib.Path(tmp_dir)))
