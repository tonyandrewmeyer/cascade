"""Base command class for Cascade commands."""

from __future__ import annotations

import abc
from typing import TYPE_CHECKING, ClassVar

from ..utils.theme import get_theme


if TYPE_CHECKING:
    import ops
    import shimmer

    from pebble_shell.shell import PebbleShell


class CommandMeta(abc.ABCMeta):
    """Metaclass that auto-registers commands."""

    _registry: ClassVar[dict[str, type[Command]]] = {}

    def __new__(mcs, name, bases, namespace, **kwargs):
        """Create a new command class and register it if it's a concrete command."""
        cls = super().__new__(mcs, name, bases, namespace, **kwargs)

        # Only register concrete Command subclasses that have a name.
        if (
            bases
            and hasattr(cls, "name")
            and isinstance(getattr(cls, "name", None), str)
        ):
            CommandMeta._registry[cls.name] = cls  # type: ignore[misc]

        return cls


class Command(abc.ABC, metaclass=CommandMeta):
    """Base class for shell commands."""

    name: str
    help: str
    category: str = "Other"

    def __init__(self, shell: PebbleShell):
        self.shell = shell
        self.console = shell.console

    @abc.abstractmethod
    def execute(
        self, client: ops.pebble.Client | shimmer.PebbleCliClient, args: list[str]
    ) -> int:
        """Execute the command.

        Args:
            client: The Pebble client
            args: Command arguments
        """
        pass

    # TODO: We have some more generic code for this elsewhere that we should switch to.
    def validate_args(
        self, args: list[str], min_args: int = 0, max_args: int | None = None
    ) -> bool:
        """Validate command arguments.

        Args:
            args: Command arguments
            min_args: Minimum number of arguments required
            max_args: Maximum number of arguments allowed (None for unlimited)

        Returns:
            True if arguments are valid, False otherwise
        """
        theme = get_theme()

        if len(args) < min_args:
            self.console.print(
                theme.error_text(
                    f"Error: This command requires at least {min_args} argument(s)"
                )
            )
            return False

        if max_args == 0 and len(args) > 0:
            self.console.print(
                theme.error_text("Error: This command does not accept any arguments")
            )
            return False

        if max_args is not None and len(args) > max_args:
            self.console.print(
                theme.error_text(
                    f"Error: This command accepts at most {max_args} argument(s)"
                )
            )
            return False

        return True

    def show_help(self):
        """Display help for this command."""
        from ..utils.theme import get_theme

        theme = get_theme()
        self.console.print(
            f"\n{theme.highlight_text('Usage:')} {theme.primary_text(self.name)}"
        )
        self.console.print(f"{theme.data_text(self.help)}\n")

    @classmethod
    def get_all_commands(cls) -> dict[str, type[Command]]:
        """Get all registered command classes."""
        return CommandMeta._registry.copy()
