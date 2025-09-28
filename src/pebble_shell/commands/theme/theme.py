"""Theme management command for Cascade."""

from __future__ import annotations

from typing import TYPE_CHECKING

from rich.panel import Panel

if TYPE_CHECKING:
    import ops
    import shimmer

from ...utils.command_helpers import (
    handle_help_flag,
    validate_min_args,
)
from ...utils.table_builder import create_standard_table
from ...utils.theme import (
    create_dark_theme,
    create_light_theme,
    create_minimal_theme,
    get_theme,
    set_theme,
)
from .._base import Command


class ThemeCommand(Command):
    """Manage display themes for Cascade."""

    name = "theme"
    help = "Manage display themes. Usage: theme [list|show|set <theme-name>|preview <theme-name>]"
    category = "System"

    def execute(
        self, client: ops.pebble.Client | shimmer.PebbleCliClient, args: list[str]
    ):
        """Execute theme command."""
        if handle_help_flag(self, args):
            return 0

        if not args:
            # Show current theme
            self._show_current_theme()
            return 0

        subcommand = args[0].lower()

        if subcommand == "list":
            self._list_available_themes()
        elif subcommand == "show":
            self._show_current_theme()
        elif subcommand == "set":
            if not validate_min_args(self.shell, args[1:], 1, "theme set <theme-name>"):
                return 1
            return self._set_theme(args[1])
        elif subcommand == "preview":
            if not validate_min_args(
                self.shell, args[1:], 1, "theme preview <theme-name>"
            ):
                return 1
            return self._preview_theme(args[1])
        else:
            self.console.print(f"Unknown theme command: {subcommand}")
            self.console.print(
                "Available commands: list, show, set <theme-name>, preview <theme-name>"
            )
            return 1

        return 0

    def _show_current_theme(self):
        """Show current theme information."""
        theme = get_theme()

        table = create_standard_table()
        table.add_column("Property", style=theme.secondary, no_wrap=True)
        table.add_column("Color", style=theme.data)
        table.add_column("Example", style="default")

        color_info = [
            ("Primary", theme.primary, theme.primary_text("identifier")),
            ("Secondary", theme.secondary, theme.secondary_text("metadata")),
            ("Data", theme.data, theme.data_text("content")),
            ("Numeric", theme.numeric, theme.numeric_text("123")),
            ("Status", theme.status, theme.status_text("active")),
            ("Success", theme.success, theme.success_text("success")),
            ("Warning", theme.warning, theme.warning_text("warning")),
            ("Error", theme.error, theme.error_text("error")),
            ("Info", theme.info, theme.info_text("info")),
            ("Highlight", theme.highlight, theme.highlight_text("header")),
            ("Muted", theme.muted, theme.muted_text("less important")),
        ]

        for property_name, color_value, example in color_info:
            table.add_row(property_name, color_value, example)

        self.console.print(
            Panel(
                table.build(),
                title=get_theme().highlight_text("Current Theme Configuration"),
                style=get_theme().info,
            )
        )

    def _list_available_themes(self):
        """List all available themes."""
        themes = [
            ("default", "Standard theme with balanced colors"),
            ("dark", "High contrast theme optimized for dark terminals"),
            ("light", "Theme optimized for light backgrounds"),
            ("minimal", "Monochrome theme using only white colors"),
        ]

        table = create_standard_table()
        table.add_column("Theme Name", style=get_theme().primary, no_wrap=True)
        table.add_column("Description", style=get_theme().data)

        for theme_name, description in themes:
            table.add_row(theme_name, description)

        self.console.print(
            Panel(
                table.build(),
                title=get_theme().highlight_text("Available Themes"),
                style=get_theme().info,
            )
        )

        self.console.print()
        self.console.print(
            get_theme().muted_text("Use 'theme set <name>' to change theme")
        )
        self.console.print(
            get_theme().muted_text(
                "Use 'theme preview <name>' to see a theme without changing"
            )
        )

    def _set_theme(self, theme_name: str) -> int:
        """Set the active theme."""
        theme_name = theme_name.lower()

        if theme_name == "default":
            # Keep current theme (already default)
            pass
        elif theme_name == "dark":
            set_theme(create_dark_theme())
        elif theme_name == "light":
            set_theme(create_light_theme())
        elif theme_name == "minimal":
            set_theme(create_minimal_theme())
        else:
            self.console.print(
                Panel(
                    get_theme().error_text(f"Unknown theme: {theme_name}"),
                    title=get_theme().error_text("Theme Error"),
                    style=get_theme().error,
                )
            )
            self.console.print(
                get_theme().muted_text("Use 'theme list' to see available themes")
            )
            return 1

        self.console.print(
            Panel(
                get_theme().success_text(f"Theme changed to: {theme_name}"),
                title=get_theme().success_text("Theme Updated"),
                style=get_theme().success,
            )
        )
        return 0

    def _preview_theme(self, theme_name: str) -> int:
        """Preview a theme without changing the current one."""
        theme_name = theme_name.lower()

        if theme_name == "default":
            preview_theme = get_theme()
            display_name = "Default"
        elif theme_name == "dark":
            preview_theme = create_dark_theme()
            display_name = "Dark"
        elif theme_name == "light":
            preview_theme = create_light_theme()
            display_name = "Light"
        elif theme_name == "minimal":
            preview_theme = create_minimal_theme()
            display_name = "Minimal"
        else:
            self.console.print(
                Panel(
                    get_theme().error_text(f"Unknown theme: {theme_name}"),
                    title=get_theme().error_text("Theme Error"),
                    style=get_theme().error,
                )
            )
            return 1

        table = (
            create_standard_table()
            .secondary_column("Element Type")
            .data_column("Preview")
            .build()
        )

        examples = [
            ("Identifiers", preview_theme.primary_text("service-name")),
            ("Data Content", preview_theme.data_text("Running for 2 days")),
            ("Numbers", preview_theme.numeric_text("1.2GB")),
            ("Status Info", preview_theme.status_text("active")),
            ("Success", preview_theme.success_text("✓ Operation completed")),
            ("Warning", preview_theme.warning_text("⚠ Resource limit reached")),
            ("Error", preview_theme.error_text("✗ Connection failed")),
            ("Info", preview_theme.info_text("i Additional information")),
            ("Headers", preview_theme.highlight_text("Section Header")),
            ("Metadata", preview_theme.secondary_text("Last modified: 2024-01-15")),
            ("Muted", preview_theme.muted_text("(optional details)")),
        ]

        for element_type, preview_text in examples:
            table.add_row(element_type, preview_text)

        panel = Panel(
            table,
            title=f"[{preview_theme.highlight}]{display_name} Theme Preview[/{preview_theme.highlight}]",
            style=preview_theme.info,
            border_style=preview_theme.border,
        )

        self.console.print(panel)
        self.console.print()
        self.console.print(
            get_theme().muted_text(f"Use 'theme set {theme_name}' to apply this theme")
        )
        return 0
