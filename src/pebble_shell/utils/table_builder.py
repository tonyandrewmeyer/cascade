"""Table builder utilities for creating Rich tables with consistent styling across Cascade commands."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from .theme import get_theme

if TYPE_CHECKING:
    from rich.table import Table


class TableBuilder:
    """Builder for Rich tables with consistent styling patterns."""

    def __init__(self, table: Table):
        """Initialize with a pre-configured table."""
        self._table = table

    def add_column(
        self,
        name: str,
        *,
        style: str = "white",
        justify: str = "left",
        no_wrap: bool = False,
        **kwargs: Any,
    ) -> TableBuilder:
        """Add a column to the table with specified styling."""
        self._table.add_column(
            name, style=style, justify=justify, no_wrap=no_wrap, **kwargs
        )
        return self

    def primary_id_column(self, name: str) -> TableBuilder:
        """Add a primary identifier column (theme-aware, no-wrap)."""
        return self.add_column(name, style=get_theme().primary, no_wrap=True)

    def data_column(self, name: str, no_wrap: bool = False) -> TableBuilder:
        """Add a data/content column (theme-aware)."""
        return self.add_column(name, style=get_theme().data, no_wrap=no_wrap)

    def status_column(self, name: str) -> TableBuilder:
        """Add a status/type column (theme-aware)."""
        return self.add_column(name, style=get_theme().status, no_wrap=True)

    def secondary_column(self, name: str) -> TableBuilder:
        """Add a secondary information column (theme-aware, no-wrap)."""
        return self.add_column(name, style=get_theme().secondary, no_wrap=True)

    def numeric_column(self, name: str, style: str | None = None) -> TableBuilder:
        """Add a numeric column (right-justified, theme-aware)."""
        column_style = style or get_theme().numeric
        return self.add_column(name, style=column_style, justify="right", no_wrap=True)

    def add_row(self, *values: str | Any) -> TableBuilder:
        """Add a row to the table."""
        self._table.add_row(*values)
        return self

    @property
    def row_count(self) -> int:
        """Get the number of rows in the table."""
        return self._table.row_count

    def build(self) -> Table:
        """Return the configured Rich table."""
        return self._table

    def __rich_console__(self, console, options):
        """Rich console protocol for rendering the table."""
        yield from self._table.__rich_console__(console, options)


def create_standard_table(title: str | None = None) -> TableBuilder:
    """Create a table with standard Cascade styling (most common pattern).

    This creates a table with:
    - Theme-aware headers
    - No box borders
    - Non-expanding layout
    """
    return TableBuilder(get_theme().create_standard_table(title))


def create_enhanced_table(
    title: str | None = None, border_style: str | None = None
) -> TableBuilder:
    """Create a table with enhanced styling (borders and colors).

    This creates a table with:
    - Theme-aware headers
    - Heavy box borders
    - Theme-aware border styling
    - Non-expanding layout
    """
    return TableBuilder(get_theme().create_enhanced_table(title))


def create_details_table(title: str | None = None) -> TableBuilder:
    """Create a table for key-value details display.

    This creates a table with:
    - No headers
    - No box borders
    - Padding for readability
    - Non-expanding layout
    """
    return TableBuilder(get_theme().create_details_table(title))


def create_system_table(title: str | None = None) -> TableBuilder:
    """Create a table optimized for system information display.

    This creates an enhanced table with system-appropriate styling.
    """
    return create_enhanced_table(title)


def create_network_table(title: str | None = None) -> TableBuilder:
    """Create a table optimized for network information display.

    This creates an enhanced table with network-appropriate styling.
    """
    return create_enhanced_table(title)


def create_file_listing_table(long_format: bool = False) -> TableBuilder:
    """Create a table specifically for file listings.

    Args:
        long_format: Whether to use long format (ls -l style) layout
    """
    if long_format:
        return create_standard_table()
    else:
        # Simple table for basic file listings
        return TableBuilder(get_theme().create_standard_table())


# Common column configurations for frequent use cases
def add_process_columns(builder: TableBuilder) -> TableBuilder:
    """Add standard process table columns (PID, User, Command, etc.)."""
    return (
        builder.primary_id_column("PID")
        .secondary_column("User")
        .data_column("Command")
        .status_column("Status")
    )


def add_file_columns(builder: TableBuilder, long_format: bool = False) -> TableBuilder:
    """Add standard file table columns."""
    if long_format:
        return (
            builder.secondary_column("Mode")
            .secondary_column("Owner")
            .secondary_column("Group")
            .numeric_column("Size")
            .secondary_column("Modified")
            .data_column("Name", no_wrap=False)
        )
    else:
        return builder.data_column("Name", no_wrap=False)


def add_network_columns(builder: TableBuilder) -> TableBuilder:
    """Add standard network table columns."""
    return (
        builder.primary_id_column("Interface")
        .secondary_column("Address")
        .numeric_column("RX Bytes")
        .numeric_column("TX Bytes")
        .status_column("Status")
    )


def add_service_columns(builder: TableBuilder) -> TableBuilder:
    """Add standard service table columns."""
    return (
        builder.primary_id_column("Service")
        .status_column("Status")
        .data_column("Current")
        .data_column("Since")
    )
