"""Tests for table builder utilities."""

from rich import box
from rich.table import Table
from src.pebble_shell.utils.table_builder import (
    TableBuilder,
    add_file_columns,
    add_network_columns,
    add_process_columns,
    add_service_columns,
    create_details_table,
    create_enhanced_table,
    create_file_listing_table,
    create_network_table,
    create_standard_table,
    create_system_table,
)


class TestTableBuilder:
    """Test the TableBuilder class."""

    def test_init_with_table(self):
        """Test TableBuilder initialization with a Rich table."""
        table = Table()
        builder = TableBuilder(table)
        assert builder.build() is table

    def test_add_column_basic(self):
        """Test adding a basic column."""
        builder = create_standard_table()
        builder.add_column("Test Column")

        table = builder.build()
        assert len(table.columns) == 1
        assert table.columns[0].header == "Test Column"

    def test_add_column_with_styling(self):
        """Test adding a column with custom styling."""
        builder = create_standard_table()
        builder.add_column("Test", style="red", justify="center", no_wrap=True)

        table = builder.build()
        column = table.columns[0]
        assert column.header == "Test"
        assert column.style == "red"
        assert column.justify == "center"
        assert column.no_wrap is True

    def test_primary_id_column(self):
        """Test adding a primary ID column."""
        builder = create_standard_table()
        builder.primary_id_column("PID")

        table = builder.build()
        column = table.columns[0]
        assert column.header == "PID"
        assert column.style == "cyan"
        assert column.no_wrap is True

    def test_data_column(self):
        """Test adding a data column."""
        builder = create_standard_table()
        builder.data_column("Command")

        table = builder.build()
        column = table.columns[0]
        assert column.header == "Command"
        assert column.style == "green"

    def test_status_column(self):
        """Test adding a status column."""
        builder = create_standard_table()
        builder.status_column("Status")

        table = builder.build()
        column = table.columns[0]
        assert column.header == "Status"
        assert column.style == "yellow"
        assert column.no_wrap is True

    def test_secondary_column(self):
        """Test adding a secondary column."""
        builder = create_standard_table()
        builder.secondary_column("User")

        table = builder.build()
        column = table.columns[0]
        assert column.header == "User"
        assert column.style == "white"
        assert column.no_wrap is True

    def test_numeric_column(self):
        """Test adding a numeric column."""
        builder = create_standard_table()
        builder.numeric_column("Size")

        table = builder.build()
        column = table.columns[0]
        assert column.header == "Size"
        assert column.style == "yellow"
        assert column.justify == "right"
        assert column.no_wrap is True

    def test_numeric_column_custom_style(self):
        """Test adding a numeric column with custom style."""
        builder = create_standard_table()
        builder.numeric_column("Memory", style="green")

        table = builder.build()
        column = table.columns[0]
        assert column.style == "green"

    def test_add_row(self):
        """Test adding rows to the table."""
        builder = create_standard_table()
        builder.add_column("Col1").add_column("Col2")
        builder.add_row("Value1", "Value2")
        builder.add_row("Value3", "Value4")

        table = builder.build()
        assert len(table.rows) == 2

    def test_method_chaining(self):
        """Test that methods return self for chaining."""
        builder = create_standard_table()
        result = (
            builder.primary_id_column("ID")
            .data_column("Data")
            .status_column("Status")
            .add_row("1", "test", "active")
        )

        assert result is builder
        table = builder.build()
        assert len(table.columns) == 3
        assert len(table.rows) == 1


class TestTableCreators:
    """Test table creation functions."""

    def test_create_standard_table(self):
        """Test creating a standard table."""
        builder = create_standard_table()
        table = builder.build()

        assert table.show_header is True
        assert table.header_style == "bold magenta"
        assert table.box is None
        assert table.expand is False

    def test_create_standard_table_with_title(self):
        """Test creating a standard table with title."""
        builder = create_standard_table("Test Title")
        table = builder.build()

        assert table.title == "Test Title"

    def test_create_enhanced_table(self):
        """Test creating an enhanced table."""
        builder = create_enhanced_table()
        table = builder.build()

        assert table.show_header is True
        assert table.header_style == "bold magenta"
        assert table.box == box.SIMPLE_HEAVY
        assert table.expand is False
        assert table.border_style == "bright_blue"

    def test_create_enhanced_table_uses_theme(self):
        """Test creating an enhanced table uses theme styling."""
        builder = create_enhanced_table()
        table = builder.build()

        # Theme system controls border style - should use default theme value
        assert table.border_style == "bright_blue"  # Default theme border color

    def test_create_details_table(self):
        """Test creating a details table."""
        builder = create_details_table()
        table = builder.build()

        assert table.show_header is False
        assert table.box is None
        assert table.expand is False
        assert table.padding == (0, 1, 0, 1)

    def test_create_system_table(self):
        """Test creating a system table."""
        builder = create_system_table()
        table = builder.build()

        assert table.box == box.SIMPLE_HEAVY
        assert table.border_style == "bright_blue"

    def test_create_network_table(self):
        """Test creating a network table."""
        builder = create_network_table()
        table = builder.build()

        assert table.box == box.SIMPLE_HEAVY
        # Network table now uses theme's default border color, not hardcoded cyan
        assert table.border_style == "bright_blue"

    def test_create_file_listing_table_basic(self):
        """Test creating a basic file listing table."""
        builder = create_file_listing_table(long_format=False)
        table = builder.build()

        assert table.show_header is True
        assert table.box is None

    def test_create_file_listing_table_long(self):
        """Test creating a long format file listing table."""
        builder = create_file_listing_table(long_format=True)
        table = builder.build()

        assert table.show_header is True
        assert table.header_style == "bold magenta"


class TestColumnHelpers:
    """Test column helper functions."""

    def test_add_process_columns(self):
        """Test adding standard process columns."""
        builder = create_standard_table()
        add_process_columns(builder)

        table = builder.build()
        assert len(table.columns) == 4

        # Check column headers
        headers = [col.header for col in table.columns]
        assert headers == ["PID", "User", "Command", "Status"]

        # Check column styles
        styles = [col.style for col in table.columns]
        assert styles == ["cyan", "white", "green", "yellow"]

    def test_add_file_columns_basic(self):
        """Test adding basic file columns."""
        builder = create_standard_table()
        add_file_columns(builder, long_format=False)

        table = builder.build()
        assert len(table.columns) == 1
        assert table.columns[0].header == "Name"
        assert table.columns[0].style == "green"

    def test_add_file_columns_long(self):
        """Test adding long format file columns."""
        builder = create_standard_table()
        add_file_columns(builder, long_format=True)

        table = builder.build()
        assert len(table.columns) == 6

        headers = [col.header for col in table.columns]
        expected = ["Mode", "Owner", "Group", "Size", "Modified", "Name"]
        assert headers == expected

    def test_add_network_columns(self):
        """Test adding standard network columns."""
        builder = create_standard_table()
        add_network_columns(builder)

        table = builder.build()
        assert len(table.columns) == 5

        headers = [col.header for col in table.columns]
        expected = ["Interface", "Address", "RX Bytes", "TX Bytes", "Status"]
        assert headers == expected

    def test_add_service_columns(self):
        """Test adding standard service columns."""
        builder = create_standard_table()
        add_service_columns(builder)

        table = builder.build()
        assert len(table.columns) == 4

        headers = [col.header for col in table.columns]
        expected = ["Service", "Status", "Current", "Since"]
        assert headers == expected


class TestIntegration:
    """Test integration scenarios."""

    def test_complete_table_workflow(self):
        """Test a complete table building workflow."""
        builder = create_enhanced_table("Process List")
        add_process_columns(builder)
        builder.add_row("1234", "root", "/bin/bash", "running")
        builder.add_row("5678", "user", "python", "sleeping")

        table = builder.build()

        # Verify table structure
        assert table.title == "Process List"
        assert len(table.columns) == 4
        assert len(table.rows) == 2
        assert table.box == box.SIMPLE_HEAVY

        # Verify column styles
        assert table.columns[0].style == "cyan"  # PID
        assert table.columns[1].style == "white"  # User
        assert table.columns[2].style == "green"  # Command
        assert table.columns[3].style == "yellow"  # Status

    def test_custom_table_with_mixed_columns(self):
        """Test creating a custom table with mixed column types."""
        builder = create_standard_table()
        (
            builder.primary_id_column("ID")
            .data_column("Name")
            .numeric_column("Count", style="cyan")
            .status_column("State")
            .add_row("001", "Item A", "42", "active")
            .add_row("002", "Item B", "17", "inactive")
        )

        table = builder.build()
        assert len(table.columns) == 4
        assert len(table.rows) == 2

        # Verify numeric column properties
        count_col = table.columns[2]
        assert count_col.justify == "right"
        assert count_col.style == "cyan"
