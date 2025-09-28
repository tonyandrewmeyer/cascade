"""Tests for theme management system."""

from rich.panel import Panel
from rich.table import Table

from pebble_shell.utils.theme import (
    ColorScheme,
    ThemeConfig,
    ThemeManager,
    create_dark_theme,
    create_light_theme,
    create_minimal_theme,
    data,
    error,
    get_theme,
    highlight,
    info,
    muted,
    numeric,
    primary,
    secondary,
    set_theme,
    status,
    success,
    warning,
)


class TestColorScheme:
    """Test ColorScheme configuration."""

    def test_default_colors(self):
        """Test default color scheme values."""
        scheme = ColorScheme()

        assert scheme.primary == "cyan"
        assert scheme.secondary == "white"
        assert scheme.data == "green"
        assert scheme.numeric == "yellow"
        assert scheme.status == "yellow"
        assert scheme.success == "green"
        assert scheme.warning == "yellow"
        assert scheme.error == "red"
        assert scheme.info == "blue"
        assert scheme.highlight == "magenta"
        assert scheme.muted == "dim"
        assert scheme.header == "bold magenta"
        assert scheme.border == "bright_blue"

    def test_custom_colors(self):
        """Test custom color scheme."""
        scheme = ColorScheme(
            primary="red",
            secondary="blue",
            data="yellow",
        )

        assert scheme.primary == "red"
        assert scheme.secondary == "blue"
        assert scheme.data == "yellow"
        # Other colors should use defaults
        assert scheme.success == "green"


class TestThemeConfig:
    """Test ThemeConfig configuration."""

    def test_default_config(self):
        """Test default theme configuration."""
        config = ThemeConfig(colors=ColorScheme())

        assert isinstance(config.colors, ColorScheme)
        assert config.table_expand is False
        assert config.table_padding == (0, 1)
        assert config.panel_border_style == "bright_blue"
        assert config.panel_expand is False


class TestThemeManager:
    """Test ThemeManager functionality."""

    def test_initialization(self):
        """Test theme manager initialization."""
        manager = ThemeManager()
        assert isinstance(manager.config, ThemeConfig)
        assert isinstance(manager.config.colors, ColorScheme)

    def test_custom_initialization(self):
        """Test theme manager with custom config."""
        custom_colors = ColorScheme(primary="red")
        custom_config = ThemeConfig(colors=custom_colors)
        manager = ThemeManager(custom_config)

        assert manager.config.colors.primary == "red"
        assert manager.primary == "red"

    def test_color_properties(self):
        """Test color property access."""
        manager = ThemeManager()

        assert manager.primary == "cyan"
        assert manager.secondary == "white"
        assert manager.data == "green"
        assert manager.numeric == "yellow"
        assert manager.status == "yellow"
        assert manager.success == "green"
        assert manager.warning == "yellow"
        assert manager.error == "red"
        assert manager.info == "blue"
        assert manager.highlight == "magenta"
        assert manager.muted == "dim"
        assert manager.header == "bold magenta"
        assert manager.border == "bright_blue"

    def test_text_formatting_methods(self):
        """Test text formatting methods."""
        manager = ThemeManager()

        assert manager.primary_text("test") == "[cyan]test[/cyan]"
        assert manager.secondary_text("test") == "[white]test[/white]"
        assert manager.data_text("test") == "[green]test[/green]"
        assert manager.numeric_text("123") == "[yellow]123[/yellow]"
        assert manager.numeric_text(123) == "[yellow]123[/yellow]"
        assert manager.numeric_text(12.5) == "[yellow]12.5[/yellow]"
        assert manager.status_text("test") == "[yellow]test[/yellow]"
        assert manager.success_text("test") == "[green]test[/green]"
        assert manager.warning_text("test") == "[yellow]test[/yellow]"
        assert manager.error_text("test") == "[red]test[/red]"
        assert manager.info_text("test") == "[blue]test[/blue]"
        assert manager.highlight_text("test") == "[magenta]test[/magenta]"
        assert manager.muted_text("test") == "[dim]test[/dim]"

    def test_table_creation(self):
        """Test table creation methods."""
        manager = ThemeManager()

        # Standard table
        table = manager.create_standard_table("Test")
        assert isinstance(table, Table)
        assert table.title == "Test"
        assert table.show_header is True
        assert table.box is None

        # Enhanced table
        table = manager.create_enhanced_table("Test")
        assert isinstance(table, Table)
        assert table.title == "Test"
        assert table.show_header is True
        assert table.box is not None

        # Details table
        table = manager.create_details_table("Test")
        assert isinstance(table, Table)
        assert table.title == "Test"
        assert table.show_header is False
        assert table.box is None

    def test_panel_creation(self):
        """Test panel creation methods."""
        manager = ThemeManager()

        # Basic panel
        panel = manager.create_panel("content", title="Test")
        assert isinstance(panel, Panel)

        # Error panel
        panel = manager.create_error_panel("error message")
        assert isinstance(panel, Panel)

        # Success panel
        panel = manager.create_success_panel("success message")
        assert isinstance(panel, Panel)

        # Warning panel
        panel = manager.create_warning_panel("warning message")
        assert isinstance(panel, Panel)

        # Info panel
        panel = manager.create_info_panel("info message")
        assert isinstance(panel, Panel)


class TestGlobalTheme:
    """Test global theme functionality."""

    def test_default_global_theme(self):
        """Test default global theme."""
        theme = get_theme()
        assert isinstance(theme, ThemeManager)
        assert theme.primary == "cyan"

    def test_set_global_theme(self):
        """Test setting global theme."""
        original_theme = get_theme()

        # Set custom theme
        custom_colors = ColorScheme(primary="red")
        custom_theme = ThemeManager(ThemeConfig(colors=custom_colors))
        set_theme(custom_theme)

        # Verify theme was set
        assert get_theme().primary == "red"

        # Restore original theme
        set_theme(original_theme)
        assert get_theme().primary == "cyan"


class TestThemeVariants:
    """Test theme variant creation."""

    def test_dark_theme(self):
        """Test dark theme creation."""
        theme = create_dark_theme()
        assert isinstance(theme, ThemeManager)
        assert theme.primary == "bright_cyan"
        assert theme.secondary == "bright_white"
        assert theme.data == "bright_green"

    def test_light_theme(self):
        """Test light theme creation."""
        theme = create_light_theme()
        assert isinstance(theme, ThemeManager)
        assert theme.primary == "blue"
        assert theme.secondary == "black"
        assert theme.data == "dark_green"

    def test_minimal_theme(self):
        """Test minimal theme creation."""
        theme = create_minimal_theme()
        assert isinstance(theme, ThemeManager)
        assert theme.primary == "white"
        assert theme.secondary == "white"
        assert theme.data == "white"
        # All colors should be white or variations
        for color in ["success", "warning", "error", "info"]:
            assert "white" in getattr(theme.config.colors, color)


class TestGlobalStylingFunctions:
    """Test global styling functions."""

    def test_global_functions_use_current_theme(self):
        """Test that global functions use the current theme."""
        original_theme = get_theme()

        # Test with default theme
        assert primary("test") == "[cyan]test[/cyan]"
        assert secondary("test") == "[white]test[/white]"
        assert data("test") == "[green]test[/green]"
        assert numeric("123") == "[yellow]123[/yellow]"
        assert numeric(123) == "[yellow]123[/yellow]"
        assert status("test") == "[yellow]test[/yellow]"
        assert success("test") == "[green]test[/green]"
        assert warning("test") == "[yellow]test[/yellow]"
        assert error("test") == "[red]test[/red]"
        assert info("test") == "[blue]test[/blue]"
        assert highlight("test") == "[magenta]test[/magenta]"
        assert muted("test") == "[dim]test[/dim]"

        # Change to custom theme
        custom_colors = ColorScheme(primary="red", data="blue")
        custom_theme = ThemeManager(ThemeConfig(colors=custom_colors))
        set_theme(custom_theme)

        # Test with custom theme
        assert primary("test") == "[red]test[/red]"
        assert data("test") == "[blue]test[/blue]"

        # Restore original theme
        set_theme(original_theme)

    def test_numeric_function_type_handling(self):
        """Test numeric function handles different types."""
        assert numeric("123") == "[yellow]123[/yellow]"
        assert numeric(123) == "[yellow]123[/yellow]"
        assert numeric(12.5) == "[yellow]12.5[/yellow]"


class TestThemeIntegration:
    """Test theme integration scenarios."""

    def test_theme_switching(self):
        """Test switching between different themes."""
        original_theme = get_theme()

        # Test dark theme
        dark_theme = create_dark_theme()
        set_theme(dark_theme)
        assert primary("test") == "[bright_cyan]test[/bright_cyan]"

        # Test light theme
        light_theme = create_light_theme()
        set_theme(light_theme)
        assert primary("test") == "[blue]test[/blue]"

        # Test minimal theme
        minimal_theme = create_minimal_theme()
        set_theme(minimal_theme)
        assert primary("test") == "[white]test[/white]"

        # Restore original
        set_theme(original_theme)
        assert primary("test") == "[cyan]test[/cyan]"

    def test_custom_theme_persistence(self):
        """Test that custom themes persist across function calls."""
        original_theme = get_theme()

        # Create custom theme with unique colors
        custom_colors = ColorScheme(primary="magenta", success="cyan", error="yellow")
        set_theme(ThemeManager(ThemeConfig(colors=custom_colors)))

        # Multiple calls should use the same theme
        assert primary("test1") == "[magenta]test1[/magenta]"
        assert primary("test2") == "[magenta]test2[/magenta]"
        assert success("ok") == "[cyan]ok[/cyan]"
        assert error("fail") == "[yellow]fail[/yellow]"

        # Restore original
        set_theme(original_theme)
