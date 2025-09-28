#!/usr/bin/env python3

"""Demo script showing the real-time system monitoring dashboard in Cascade shell."""

import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import ops

from pebble_shell.shell import PebbleShell


def main():
    """Run the dashboard demo."""
    print("Cascade Shell - Real-time System Dashboard Demo")
    print("=" * 65)
    print()
    print("This demo showcases the new real-time system monitoring dashboard:")
    print()
    print("Dashboard Features:")
    print("   • Real-time CPU and Memory monitoring")
    print("   • Live load average tracking")
    print("   • Process count and statistics")
    print("   • Disk I/O activity monitoring")
    print("   • Network interface statistics")
    print("   • System uptime and core count")
    print("   • Visual progress bars and alerts")
    print("   • Auto-refreshing every 2 seconds")
    print()
    print("Real-time Monitoring Panels:")
    print()
    print("   CPU & Memory Panel:")
    print("   • CPU usage percentage with visual bar")
    print("   • Memory usage with progress indicator")
    print("   • Memory details (used/total)")
    print("   • Color-coded alerts for high usage")
    print()
    print("   Processes Panel:")
    print("   • Total process count")
    print("   • Running processes count")
    print("   • Load average per CPU core")
    print("   • Performance indicators")
    print()
    print("   Load & Disk Panel:")
    print("   • 1, 5, and 15-minute load averages")
    print("   • Total disk reads and writes")
    print("   • Disk I/O in KB")
    print("   • Storage activity monitoring")
    print()
    print("   Network Panel:")
    print("   • Network interface statistics")
    print("   • RX/TX bytes for each interface")
    print("   • Top 5 network interfaces")
    print("   • Network traffic monitoring")
    print()
    print("Smart Features:")
    print("   • Automatic alert thresholds")
    print("   • Color-coded status indicators")
    print("   • Historical data tracking")
    print("   • Graceful error handling")
    print("   • Responsive layout design")
    print("   • Keyboard interrupt handling")
    print()
    print("Usage:")
    print("   • Press Ctrl+C to exit dashboard")
    print("   • Dashboard updates every 2 seconds")
    print()

    socket_path = os.getenv("PEBBLE_SOCKET", os.path.join(tempfile.gettempdir(), ".pebble-demo.socket"))
    shell = PebbleShell(ops.pebble.Client(socket_path=socket_path))

    if not shell.connect():
        print(f"Failed to connect to Pebble at {socket_path}")
        print(f"   Start Pebble server with: pebble run --socket {socket_path}")
        return 1

    try:
        shell.run_command("dashboard")
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")

    return 0


if __name__ == "__main__":
    sys.exit(main())
