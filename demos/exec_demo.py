#!/usr/bin/env python3

"""Demo script showing remote execution capabilities."""

import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import ops

from pebble_shell.shell import PebbleShell


def run_exec_demo():
    """Run a demo of remote execution features."""
    print("=== Pebble Debug Shell - Remote Execution Demo ===\n")

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
    print("🚀 This demo shows remote command execution using Pebble's exec API")
    print("Commands will be executed inside the container, not just on files\n")

    commands = [
        ("System Information", "info"),
        ("Basic Remote Execution", "exec uname"),
        ("Process List", "exec ps aux"),
        ("Memory Information", "exec free -h"),
        ("Disk Usage", "exec df -h"),
        ("Network Interfaces", "exec ip addr show || exec ifconfig"),
        ("Find Commands", "which python3"),
        ("Find Multiple Commands", "which bash python3 git docker"),
        ("Check Command Availability", "exec command -v curl"),
        ("Environment Variables", "exec env | head -10"),
        ("Current Working Directory", "exec pwd"),
        ("List Current Directory", "exec ls -la"),
        ("Remote Text Processing", "exec ps aux | head -5"),
        ("Remote Pipe Example", "exec cat /etc/passwd | head -3"),
        ("Remote Grep Example", "exec ps aux | grep -v grep"),
        ("File Operations", "exec touch /tmp/remote_test.txt"),
        ("Verify File Creation", "exec ls -la /tmp/remote_test.txt"),
        (
            "Remote Echo to File",
            "exec sh -c 'echo Hello from remote > /tmp/remote_test.txt'",
        ),
        ("Read Remote File", "exec cat /tmp/remote_test.txt"),
        ("Clean Up", "exec rm /tmp/remote_test.txt"),
        ("Network Tools", "exec ping -c 3 8.8.8.8 || echo 'ping not available'"),
        (
            "DNS Lookup",
            "exec nslookup google.com || exec host google.com || echo 'DNS tools not available'",
        ),
        (
            "Package Information",
            "exec which apt && exec apt list --installed | head -5 || echo 'apt not available'",
        ),
        (
            "System Services",
            "exec systemctl list-units --type=service --state=running | head -5 || echo 'systemd not available'",
        ),
        ("Development Tools", "exec python3 --version || echo 'Python not available'"),
        ("Node.js Version", "exec node --version || echo 'Node.js not available'"),
        ("Git Version", "exec git --version || echo 'Git not available'"),
        ("Docker Status", "exec docker ps || echo 'Docker not available'"),
        ("Interactive Demo Setup", "echo 'Use shell command for interactive session'"),
        ("Shell Command Info", "echo 'Try: shell /bin/bash for interactive shell'"),
        ("Exec Interactive Info", "echo 'Try: exec -i /bin/bash for interactive mode'"),
        ("Advanced Examples", "echo 'Advanced remote execution patterns:'"),
        ("Remote Scripting", "exec sh -c 'for i in 1 2 3; do echo Step $i; done'"),
        ("Remote Find", "exec find /usr/bin -name '*python*' | head -3"),
        ("Remote System Load", "exec uptime"),
        ("Remote CPU Info", "exec grep processor /proc/cpuinfo | wc -l"),
        ("Final Status", "echo 'Remote execution demo completed!'"),
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
    sys.exit(run_exec_demo())
