"""Implementation of PlanCommand."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

import yaml
from rich.panel import Panel
from rich.syntax import Syntax

from ...utils.command_helpers import handle_help_flag
from ...utils.table_builder import create_standard_table
from ...utils.theme import get_theme
from .._base import Command

if TYPE_CHECKING:
    import ops
    import shimmer


class PlanCommand(Command):
    """Show or manage service plans."""

    name = "pebble-plan"
    help = "Show the current plan configuration. Usage: pebble-plan [--format json|yaml|table]"
    category = "Pebble Management"

    def execute(
        self, client: ops.pebble.Client | shimmer.PebbleCliClient, args: list[str]
    ):
        """Execute the plan command."""
        if handle_help_flag(self, args):
            return 0

        # Handle --format=value syntax manually since parse_flags doesn't support it well
        format_type = "table"  # default format
        processed_args = []

        i = 0
        while i < len(args):
            arg = args[i]
            if arg.startswith("--format"):
                if "=" in arg:
                    # --format=value syntax
                    format_type = arg.split("=", 1)[1]
                elif i + 1 < len(args):
                    # --format value syntax
                    format_type = args[i + 1]
                    i += 1
                else:
                    self.console.print(
                        "Error: --format requires a value (json, yaml, or table)"
                    )
                    return 1

                if format_type not in ["json", "yaml", "table"]:
                    self.console.print(
                        "Error: --format must be one of: json, yaml, table"
                    )
                    return 1
            else:
                processed_args.append(arg)
            i += 1

        if processed_args:
            self.console.print("Error: unknown argument: " + processed_args[0])
            return 1

        plan = client.get_plan()
        plan_dict = plan.to_dict()

        if format_type == "json":
            self._show_json_plan(plan_dict)
        elif format_type == "yaml":
            self._show_yaml_plan(plan_dict)
        else:
            self._show_plan_table(plan_dict)

        return 0

    def _show_json_plan(self, plan_dict: ops.pebble.PlanDict):
        """Display plan in pretty-printed JSON format with syntax highlighting."""
        json_str = json.dumps(plan_dict, indent=2)
        self.console.print_json(json_str)

    def _show_yaml_plan(self, plan_dict: ops.pebble.PlanDict):
        """Display plan in pretty-printed YAML format with syntax highlighting."""
        yaml_str = yaml.safe_dump(
            plan_dict, default_flow_style=False, indent=2, sort_keys=False
        )
        syntax = Syntax(
            yaml_str,
            "yaml",
            theme="monokai",
            word_wrap=True,
            line_numbers=True,
            background_color="default",
        )
        self.console.print(
            Panel(
                syntax,
                title=get_theme().highlight_text("Pebble Plan Configuration (YAML)"),
                style=get_theme().primary,
                border_style=get_theme().border,
            )
        )

    def _show_plan_table(self, plan_dict: ops.pebble.PlanDict):
        """Display plan in a Rich table format."""
        services = plan_dict.get("services", {})
        if services:
            services_table = create_standard_table()
            services_table.primary_id_column("Service")
            services_table.data_column("Command")
            services_table.status_column("Startup")
            services_table.secondary_column("User")
            services_table.data_column("Summary")

            for service_name, service_data in services.items():
                command = service_data.get("command", "N/A")
                startup = service_data.get("startup", "disabled")
                user = service_data.get("user", "default")
                summary = service_data.get("summary", "")

                services_table.add_row(service_name, command, startup, user, summary)

            self.console.print(
                Panel(
                    services_table,
                    title=get_theme().highlight_text("Services"),
                    style=get_theme().primary,
                )
            )

        checks = plan_dict.get("checks", {})
        if checks:
            checks_table = create_standard_table()
            checks_table.primary_id_column("Check")
            checks_table.status_column("Type")
            checks_table.status_column("Level")
            checks_table.secondary_column("Period")
            checks_table.secondary_column("Timeout")

            for check_name, check_data in checks.items():
                check_type = "unknown"
                if "http" in check_data and check_data["http"] is not None:
                    check_type = f"HTTP ({check_data['http'].get('url', 'N/A')})"
                elif "tcp" in check_data and check_data["tcp"] is not None:
                    port = check_data["tcp"].get("port", "N/A")
                    host = check_data["tcp"].get("host", "localhost")
                    check_type = f"TCP ({host}:{port})"
                elif "exec" in check_data and check_data["exec"] is not None:
                    command = check_data["exec"].get("command", "N/A")
                    check_type = f"Exec ({command})"

                level = check_data.get("level", "")
                period = check_data.get("period", "10s")
                timeout = check_data.get("timeout", "3s")

                checks_table.add_row(
                    check_name, check_type, str(level), period, timeout
                )

            self.console.print(
                Panel(
                    checks_table,
                    title=get_theme().highlight_text("Health Checks"),
                    style=get_theme().primary,
                )
            )

        log_targets = plan_dict.get("log-targets", {})
        if log_targets:
            log_table = create_standard_table()
            log_table.primary_id_column("Target")
            log_table.status_column("Type")
            log_table.data_column("Location")
            log_table.data_column("Services")

            for target_name, target_data in log_targets.items():
                target_type = target_data.get("type", "unknown")
                location = target_data.get("location", "N/A")
                services = target_data.get("services", [])
                services_str = ", ".join(services) if services else "all"

                log_table.add_row(target_name, target_type, location, services_str)

            self.console.print(
                Panel(
                    log_table,
                    title=get_theme().highlight_text("Log Targets"),
                    style=get_theme().primary,
                )
            )

        if not services and not checks and not log_targets:
            self.console.print(
                Panel(
                    get_theme().warning_text(
                        "No services, checks, or log targets configured in plan"
                    ),
                    title=get_theme().highlight_text("Plan Configuration"),
                    style=get_theme().warning,
                )
            )
