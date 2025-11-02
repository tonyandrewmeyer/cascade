"""Implementation of NotifyCommand."""

from __future__ import annotations

import json
import os
from typing import TYPE_CHECKING, Any

import ops
import yaml

from ...utils.command_helpers import handle_help_flag
from .._base import Command

if TYPE_CHECKING:
    import shimmer


class NotifyCommand(Command):
    """Send a notice."""

    name = "notify"
    help = "Send a notice. Usage: notify <type> <key> [--file <file.json|file.yaml>] [key=value...]"
    category = "Pebble Management"

    def execute(
        self, client: ops.pebble.Client | shimmer.PebbleCliClient, args: list[str]
    ):
        """Execute the notify command."""
        if handle_help_flag(self, args):
            return 0

        if len(args) < 2:
            self.console.print(
                "Usage: notify <type> <key> [--file <file.json|file.yaml>] [key=value...]"
            )
            self.console.print("Examples:")
            self.console.print("  notify warning service-down --file data.json")
            self.console.print(
                "  notify info deployment-complete status=success version=1.2.3"
            )
            self.console.print(
                "  notify error db-connection host=localhost port=5432 error=timeout"
            )
            return 1

        notice_type = ops.pebble.NoticeType(args[0])
        key = args[1]
        data: dict[str, str] = {}

        i = 2
        while i < len(args):
            arg = args[i]

            if arg == "--file":
                if i + 1 >= len(args):
                    self.console.print("Error: --file requires a file path")
                    return 1
                file_path = args[i + 1]
                try:
                    file_data = self._load_data_from_file(file_path)
                    data.update(file_data)
                except Exception as e:
                    self.console.print(f"Error loading data from file: {e}")
                    return 1
                i += 2

            elif "=" in arg:
                k, v = arg.split("=", 1)
                data[k] = v
                i += 1

            else:
                self.console.print(f"Error: Unknown argument '{arg}'")
                return 1

        notice_id = client.notify(notice_type, key, data=data)
        self.console.print(f"Notice sent with ID: {notice_id}")
        if data:
            self.console.print(f"Data: {json.dumps(data, indent=2)}")
        return 0

    def _load_data_from_file(self, file_path: str) -> dict[str, Any]:
        """Load data from a JSON or YAML file."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        with open(file_path) as f:
            content = f.read()

        try:
            return yaml.safe_load(content)
        except yaml.YAMLError:
            raise ValueError("Could not parse file as JSON or YAML") from None
