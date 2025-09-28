"""Central theme management system for Rich display styling across Cascade commands.

This module provides a unified theming system that standardizes colors, styles, and
formatting patterns used throughout the Cascade shell interface.
"""

from __future__ import annotations

from dataclasses import dataclass

from rich import box
from rich.panel import Panel
from rich.table import Table


@dataclass
class ColorScheme:
    """Color scheme configuration for consistent styling."""

    # Core colors for different types of information
    primary: str = "cyan"  # Primary identifiers (PIDs, names, paths)
    secondary: str = "white"  # Secondary information (timestamps, metadata)
    data: str = "green"  # Main content/data display
    numeric: str = "yellow"  # Numbers, counts, sizes
    status: str = "yellow"  # Status indicators, types

    # State-based colors
    success: str = "green"  # Success messages, active states
    warning: str = "yellow"  # Warnings, non-critical issues
    error: str = "red"  # Errors, failures, critical issues
    info: str = "blue"  # Informational messages

    # Special purpose colors
    highlight: str = "magenta"  # Headers, emphasized text
    muted: str = "dim"  # Less important text
    link: str = "blue"  # Links, references

    # Table-specific colors
    header: str = "bold magenta"  # Table headers
    border: str = "bright_blue"  # Table borders


@dataclass
class ThemeConfig:
    """Complete theme configuration including colors and styling options."""

    colors: ColorScheme

    # Table styling options
    table_box_style: box.Box = box.SIMPLE_HEAVY
    table_expand: bool = False
    table_padding: tuple[int, int] = (0, 1)

    # Panel styling options
    panel_border_style: str = "bright_blue"
    panel_expand: bool = False

    # Progress bar styling
    progress_style: str = "cyan"
    progress_complete_style: str = "green"


class ThemeManager:
    """Central theme manager for Rich display styling."""

    def __init__(self, theme_config: ThemeConfig | None = None):
        """Initialize theme manager with optional custom config."""
        self.config = theme_config or ThemeConfig(colors=ColorScheme())

    # Color access methods
    @property
    def primary(self) -> str:
        """Get primary color for identifiers."""
        return self.config.colors.primary

    @property
    def secondary(self) -> str:
        """Get secondary color for metadata."""
        return self.config.colors.secondary

    @property
    def data(self) -> str:
        """Get data color for content."""
        return self.config.colors.data

    @property
    def numeric(self) -> str:
        """Get numeric color for numbers."""
        return self.config.colors.numeric

    @property
    def status(self) -> str:
        """Get status color for indicators."""
        return self.config.colors.status

    @property
    def success(self) -> str:
        """Get success color."""
        return self.config.colors.success

    @property
    def warning(self) -> str:
        """Get warning color."""
        return self.config.colors.warning

    @property
    def error(self) -> str:
        """Get error color."""
        return self.config.colors.error

    @property
    def info(self) -> str:
        """Get info color."""
        return self.config.colors.info

    @property
    def highlight(self) -> str:
        """Get highlight color for headers."""
        return self.config.colors.highlight

    @property
    def muted(self) -> str:
        """Get muted color for less important text."""
        return self.config.colors.muted

    @property
    def header(self) -> str:
        """Get header color for table headers."""
        return self.config.colors.header

    @property
    def border(self) -> str:
        """Get border color for table borders."""
        return self.config.colors.border

    # Styled text methods.
    def primary_text(self, text: str) -> str:
        """Format text with primary styling."""
        return f"[{self.primary}]{text}[/{self.primary}]"

    def secondary_text(self, text: str) -> str:
        """Format text with secondary styling."""
        return f"[{self.secondary}]{text}[/{self.secondary}]"

    def data_text(self, text: str) -> str:
        """Format text with data styling."""
        return f"[{self.data}]{text}[/{self.data}]"

    def numeric_text(self, text: str | int | float) -> str:
        """Format numeric text with numeric styling."""
        return f"[{self.numeric}]{text}[/{self.numeric}]"

    def status_text(self, text: str) -> str:
        """Format text with status styling."""
        return f"[{self.status}]{text}[/{self.status}]"

    def success_text(self, text: str) -> str:
        """Format text with success styling."""
        return f"[{self.success}]{text}[/{self.success}]"

    def warning_text(self, text: str) -> str:
        """Format text with warning styling."""
        return f"[{self.warning}]{text}[/{self.warning}]"

    def error_text(self, text: str) -> str:
        """Format text with error styling."""
        return f"[{self.error}]{text}[/{self.error}]"

    def info_text(self, text: str) -> str:
        """Format text with info styling."""
        return f"[{self.info}]{text}[/{self.info}]"

    def highlight_text(self, text: str) -> str:
        """Format text with highlight styling."""
        return f"[{self.highlight}]{text}[/{self.highlight}]"

    def muted_text(self, text: str) -> str:
        """Format text with muted styling."""
        return f"[{self.muted}]{text}[/{self.muted}]"

    # Component creation methods.
    def create_standard_table(self, title: str | None = None) -> Table:
        """Create a table with standard theme styling."""
        return Table(
            show_header=True,
            header_style=self.header,
            box=None,
            expand=self.config.table_expand,
            title=title,
        )

    def create_enhanced_table(self, title: str | None = None) -> Table:
        """Create a table with enhanced theme styling (borders)."""
        return Table(
            show_header=True,
            header_style=self.header,
            box=self.config.table_box_style,
            expand=self.config.table_expand,
            border_style=self.border,
            title=title,
        )

    def create_details_table(self, title: str | None = None) -> Table:
        """Create a table for key-value details display."""
        return Table(
            show_header=False,
            box=None,
            expand=self.config.table_expand,
            padding=self.config.table_padding,
            title=title,
        )

    def create_panel(
        self,
        content: str,
        title: str | None = None,
        style: str | None = None,
        border_style: str | None = None,
    ) -> Panel:
        """Create a panel with theme styling."""
        return Panel(
            content,
            title=title,
            style=style,
            border_style=border_style or self.config.panel_border_style,
            expand=self.config.panel_expand,
        )

    def create_error_panel(self, message: str, title: str = "Error") -> Panel:
        """Create an error panel with consistent styling."""
        return self.create_panel(
            self.error_text(message),
            title=title,
            border_style=self.error,
        )

    def create_success_panel(self, message: str, title: str = "Success") -> Panel:
        """Create a success panel with consistent styling."""
        return self.create_panel(
            self.success_text(message),
            title=title,
            border_style=self.success,
        )

    def create_warning_panel(self, message: str, title: str = "Warning") -> Panel:
        """Create a warning panel with consistent styling."""
        return self.create_panel(
            self.warning_text(message),
            title=title,
            border_style=self.warning,
        )

    def create_info_panel(self, message: str, title: str = "Info") -> Panel:
        """Create an info panel with consistent styling."""
        return self.create_panel(
            self.info_text(message),
            title=title,
            border_style=self.info,
        )


# Global theme instance - can be overridden for customisation.
# TODO: try to move this somewhere else? Maybe the shell object?
_default_theme = ThemeManager()


def get_theme() -> ThemeManager:
    """Get the current global theme manager."""
    return _default_theme


def set_theme(theme: ThemeManager) -> None:
    """Set a new global theme manager."""
    global _default_theme
    _default_theme = theme


def create_dark_theme() -> ThemeManager:
    """Create a dark theme variant."""
    dark_colors = ColorScheme(
        primary="bright_cyan",
        secondary="bright_white",
        data="bright_green",
        numeric="bright_yellow",
        status="bright_yellow",
        success="bright_green",
        warning="bright_yellow",
        error="bright_red",
        info="bright_blue",
        highlight="bright_magenta",
        muted="dim white",
        header="bold bright_magenta",
        border="bright_blue",
    )
    return ThemeManager(ThemeConfig(colors=dark_colors))


def create_light_theme() -> ThemeManager:
    """Create a light theme variant."""
    light_colors = ColorScheme(
        primary="blue",
        secondary="black",
        data="dark_green",
        numeric="dark_orange",
        status="dark_orange",
        success="dark_green",
        warning="dark_orange",
        error="dark_red",
        info="blue",
        highlight="purple",
        muted="dim black",
        header="bold purple",
        border="blue",
    )
    return ThemeManager(ThemeConfig(colors=light_colors))


def create_minimal_theme() -> ThemeManager:
    """Create a minimal monochrome theme."""
    minimal_colors = ColorScheme(
        primary="white",
        secondary="white",
        data="white",
        numeric="white",
        status="white",
        success="white",
        warning="white",
        error="white",
        info="white",
        highlight="bold white",
        muted="dim white",
        header="bold white",
        border="white",
    )
    return ThemeManager(ThemeConfig(colors=minimal_colors))


# Common styling functions using the global theme.
def primary(text: str) -> str:
    """Format text with primary styling using global theme."""
    return get_theme().primary_text(text)


def secondary(text: str) -> str:
    """Format text with secondary styling using global theme."""
    return get_theme().secondary_text(text)


def data(text: str) -> str:
    """Format text with data styling using global theme."""
    return get_theme().data_text(text)


def numeric(text: str | int | float) -> str:
    """Format numeric text using global theme."""
    return get_theme().numeric_text(text)


def status(text: str) -> str:
    """Format text with status styling using global theme."""
    return get_theme().status_text(text)


def success(text: str) -> str:
    """Format text with success styling using global theme."""
    return get_theme().success_text(text)


def warning(text: str) -> str:
    """Format text with warning styling using global theme."""
    return get_theme().warning_text(text)


def error(text: str) -> str:
    """Format text with error styling using global theme."""
    return get_theme().error_text(text)


def info(text: str) -> str:
    """Format text with info styling using global theme."""
    return get_theme().info_text(text)


def highlight(text: str) -> str:
    """Format text with highlight styling using global theme."""
    return get_theme().highlight_text(text)


def muted(text: str) -> str:
    """Format text with muted styling using global theme."""
    return get_theme().muted_text(text)
