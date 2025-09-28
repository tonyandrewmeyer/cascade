"""Implementation of AliasCommand."""

from __future__ import annotations

from typing import TYPE_CHECKING, Union

import ops
from rich.panel import Panel
from rich.table import Table

from ...utils.command_helpers import handle_help_flag
from .._base import Command

if TYPE_CHECKING:
    import shimmer

    from pebble_shell.shell import PebbleShell

# TODO: Use the prototype from Shimmer.
ClientType = Union[ops.pebble.Client, "shimmer.PebbleCliClient"]


class AliasCommand(Command):
    """Manage command aliases."""

    name = "alias"
    help = "Manage command aliases"
    category = "Built-in Commands"

    def __init__(self, shell: PebbleShell):
        super().__init__(shell)
        self.aliases = {
            "ll": "ls -l -a -h",
            "la": "ls -a",
            "l": "ls",
            "h": "history",
            "c": "clear",
            "q": "exit",
            "?": "help",
        }

    def execute(
        self, client: ops.pebble.Client | shimmer.PebbleCliClient, args: list[str]
    ):
        """Execute alias command."""
        if handle_help_flag(self, args):
            return 0

        if not args:
            # Show all aliases.
            if not self.aliases:
                self.console.print(Panel("No aliases defined", style="bold yellow"))
                return 0

            table = Table(
                show_header=True, header_style="bold magenta", box=None, expand=False
            )
            table.add_column("Alias", style="bold cyan", no_wrap=True)
            table.add_column("Command", style="green")
            for alias, command in sorted(self.aliases.items()):
                table.add_row(
                    f"[bold cyan]{alias}[/bold cyan]", f"[green]{command}[/green]"
                )
            self.console.print(table)
            return 0

        if len(args) == 1 and "=" not in args[0]:
            # Show specific alias.
            alias_name = args[0]
            if alias_name in self.aliases:
                self.console.print(
                    Panel(
                        f"[bold cyan]{alias_name}[/bold cyan] = [white]{self.aliases[alias_name]}[/white]",
                        style="bold green",
                    )
                )
                return 0
            self.console.print(
                Panel(f"alias: [red]{alias_name}[/red]: not found", style="bold red")
            )
            return 1

        # Set alias (alias name=command).
        alias_def = " ".join(args)
        if "=" not in alias_def:
            self.show_help()
            return 1

        name, command = alias_def.split("=", 1)
        name = name.strip()
        command = command.strip().strip("'\"")  # Remove quotes.

        if not name:
            self.console.print(Panel("alias: invalid alias name", style="bold red"))
            return 1

        self.aliases[name] = command
        self.console.print(
            Panel(
                f"alias [bold cyan]{name}[/bold cyan]='[white]{command}[/white]' added",
                style="bold green",
            )
        )
        return 0

    def get_alias(self, name: str) -> str | None:
        """Get alias command for name."""
        return self.aliases.get(name)

    def expand_alias(self, command_line: str) -> str:
        """Expand aliases in command line."""
        if not command_line.strip():
            return command_line
        parts = command_line.split()
        if parts[0] in self.aliases:
            alias_command = self.aliases[parts[0]]
            return alias_command + " " + " ".join(parts[1:])
        return command_line
