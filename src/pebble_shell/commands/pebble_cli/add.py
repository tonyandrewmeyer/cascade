"""Implementation of AddCommand."""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

import ops
import yaml

from ...utils.command_helpers import handle_help_flag
from .._base import Command

if TYPE_CHECKING:
    import shimmer


class AddCommand(Command):
    """Add a layer to the plan."""

    name = "add"
    help = "Add a layer to the plan. Usage: add <layer-name> [options]"
    category = "Pebble Management"

    def execute(
        self, client: ops.pebble.Client | shimmer.PebbleCliClient, args: list[str]
    ):
        """Execute the add command."""
        if handle_help_flag(self, args):
            return 0

        if len(args) < 1:
            self.console.print("Usage: add <layer-name> [options]")
            self.console.print("Options:")
            self.console.print(
                "  --service <name> <command> [--startup enabled|disabled] [--user <user>]"
            )
            self.console.print(
                "  --check <name> <type> <target> [--level alive|ready] [--period <duration>]"
            )
            self.console.print(
                "  --log-target <name> <type> <location> [--services <service1,service2>]"
            )
            self.console.print("  --file <file.yaml|file.json>")
            return 1

        layer_name = args[0]
        layer_config: ops.pebble.LayerDict = {
            "services": {},
            "checks": {},
            "log-targets": {},
        }

        i = 1
        while i < len(args):
            arg = args[i]

            if arg == "--service":
                if i + 2 >= len(args):
                    self.console.print("Error: --service requires name and command")
                    return 1
                service_name = args[i + 1]
                service_command = args[i + 2]
                service_config: ops.pebble.ServiceDict = {"command": service_command}

                # Parse service options
                j = i + 3
                while j < len(args) and args[j].startswith("--"):
                    if args[j] == "--startup":
                        if j + 1 >= len(args):
                            self.console.print(
                                "Error: --startup requires enabled|disabled"
                            )
                            return 1
                        service_config["startup"] = args[j + 1]
                        j += 2
                    elif args[j] == "--user":
                        if j + 1 >= len(args):
                            self.console.print("Error: --user requires username")
                            return 1
                        service_config["user"] = args[j + 1]
                        j += 2
                    else:
                        break

                layer_config["services"][service_name] = service_config
                i = j

            elif arg == "--check":
                if i + 3 >= len(args):
                    self.console.print("Error: --check requires name, type, and target")
                    return 1
                check_name = args[i + 1]
                check_type = args[i + 2]
                check_target = args[i + 3]
                check_config: ops.pebble.CheckDict = {}

                # Configure check based on type
                if check_type == "http":
                    check_config["http"] = {"url": check_target}
                elif check_type == "tcp":
                    if ":" in check_target:
                        host, port = check_target.split(":", 1)
                        check_config["tcp"] = {"host": host, "port": int(port)}
                    else:
                        check_config["tcp"] = {"port": int(check_target)}
                elif check_type == "exec":
                    check_config["exec"] = {"command": check_target}
                else:
                    self.console.print(f"Error: Unknown check type '{check_type}'")
                    return 1

                # Parse check options
                j = i + 4
                while j < len(args) and args[j].startswith("--"):
                    if args[j] == "--level":
                        if j + 1 >= len(args):
                            self.console.print("Error: --level requires alive|ready")
                            return 1
                        check_config["level"] = args[j + 1]
                        j += 2
                    elif args[j] == "--period":
                        if j + 1 >= len(args):
                            self.console.print("Error: --period requires duration")
                            return 1
                        check_config["period"] = args[j + 1]
                        j += 2
                    else:
                        break

                layer_config["checks"][check_name] = check_config
                i = j

            elif arg == "--log-target":
                if i + 3 >= len(args):
                    self.console.print(
                        "Error: --log-target requires name, type, and location"
                    )
                    return 1
                target_name = args[i + 1]
                target_type = args[i + 2]
                assert target_type == "loki"  # The API forces this at the moment.
                target_location = args[i + 3]
                target_config: ops.pebble.LogTargetDict = {
                    "type": target_type,
                    "location": target_location,
                }

                # Parse log target options:
                j = i + 4
                while j < len(args) and args[j].startswith("--"):
                    if args[j] == "--services":
                        if j + 1 >= len(args):
                            self.console.print(
                                "Error: --services requires service list"
                            )
                            return 1
                        services = args[j + 1].split(",")
                        target_config["services"] = services
                        j += 2
                    else:
                        break

                layer_config["log-targets"][target_name] = target_config
                i = j

            elif arg == "--file":
                if i + 1 >= len(args):
                    self.console.print("Error: --file requires file path")
                    return 1
                file_path = args[i + 1]
                file_config = self._load_layer_from_file(file_path)
                # Merge file config with current config:
                for key in ["services", "checks", "log-targets"]:
                    if key in file_config:
                        layer_config[key].update(file_config[key])  # type: ignore
                i += 2

            else:
                self.console.print(f"Error: Unknown option '{arg}'")
                return 1

        # Remove empty sections:
        clean_layer_config: ops.pebble.LayerDict = {
            k: v for k, v in layer_config.items() if v
        }  # type: ignore

        if not clean_layer_config:
            self.console.print("Error: No layer components specified")
            return 1

        layer = ops.pebble.Layer(clean_layer_config)
        client.add_layer(layer_name, layer)
        self.console.print(f"Layer '{layer_name}' added successfully")
        return 0

    def _load_layer_from_file(self, file_path: str) -> ops.pebble.LayerDict:
        """Load layer configuration from a file."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        with open(file_path) as f:
            content = f.read()

        try:
            return yaml.safe_load(content)
        except yaml.YAMLError:
            raise ValueError("Could not parse file as JSON or YAML") from None
