"""Implementation of DashboardCommand."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ...utils import SystemDashboard
from ...utils.command_helpers import handle_help_flag
from .._base import Command

if TYPE_CHECKING:
    import ops
    import shimmer


class DashboardCommand(Command):
    """Launch real-time system monitoring dashboard."""

    name = "dashboard"
    help = "Launch real-time system monitoring dashboard with live statistics"
    category = "System"

    def execute(
        self, client: ops.pebble.Client | shimmer.PebbleCliClient, args: list[str]
    ):
        """Execute dashboard command."""
        if handle_help_flag(self, args):
            return 0
        try:
            self.console.print("🚀 Starting Cascade System Dashboard...")
            self.console.print("📊 Real-time monitoring with live statistics")
            self.console.print("💡 Press Ctrl+C to exit dashboard")
            self.console.print()

            dashboard = SystemDashboard(self.shell)
            dashboard.start()
        except KeyboardInterrupt:
            self.console.print("\n👋 Dashboard stopped.")
        except Exception as e:
            self.console.print(f"Error starting dashboard: {e}")
            return 1

        return 0
