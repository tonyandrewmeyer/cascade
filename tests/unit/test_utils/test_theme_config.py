"""Tests for theme configuration utilities."""

import json
import tempfile
from pathlib import Path

import pytest

from pebble_shell.utils.theme import (
    ColorScheme,
    ThemeConfig,
    ThemeManager,
    get_theme,
    set_theme,
)
from pebble_shell.utils.theme_config import (
    ThemeConfigError,
    ThemeConfigManager,
    apply_theme,
    create_custom_theme,
    get_config_manager,
    get_current_theme_name,
    list_themes,
    preview_theme,
    save_current_theme,
    set_config_manager,
)


class TestThemeConfigManager:
    """Test ThemeConfigManager functionality."""

    def test_initialization_default_config_dir(self):
        """Test theme config manager initialization with default config directory."""
        manager = ThemeConfigManager()
        expected_path = Path.home() / ".config" / "cascade" / "themes"
        assert manager.config_dir == expected_path

    def test_initialization_custom_config_dir(self):
        """Test theme config manager initialization with custom config directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = ThemeConfigManager(temp_dir)
            assert manager.config_dir == Path(temp_dir)

    def test_list_builtin_themes(self):
        """Test listing built-in themes."""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = ThemeConfigManager(temp_dir)
            themes = manager.list_available_themes()

            # Should include all built-in themes
            assert "default" in themes
            assert "dark" in themes
            assert "light" in themes
            assert "minimal" in themes

    def test_list_includes_custom_themes(self):
        """Test that custom themes are included in the list."""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = ThemeConfigManager(temp_dir)

            # Create a custom theme file
            custom_theme = {
                "colors": {"primary": "red", "secondary": "blue"},
                "table_expand": False,
                "panel_expand": False,
                "panel_border_style": "bright_blue",
            }
            theme_file = Path(temp_dir) / "custom.json"
            with open(theme_file, "w") as f:
                json.dump(custom_theme, f)

            themes = manager.list_available_themes()
            assert "custom" in themes

    def test_load_builtin_theme(self):
        """Test loading built-in themes."""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = ThemeConfigManager(temp_dir)

            # Test loading each built-in theme
            for theme_name in ["default", "dark", "light", "minimal"]:
                theme = manager.load_theme(theme_name)
                assert isinstance(theme, ThemeManager)

    def test_load_nonexistent_theme(self):
        """Test loading a theme that doesn't exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = ThemeConfigManager(temp_dir)

            with pytest.raises(ThemeConfigError, match="Theme 'nonexistent' not found"):
                manager.load_theme("nonexistent")

    def test_save_and_load_custom_theme(self):
        """Test saving and loading a custom theme."""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = ThemeConfigManager(temp_dir)

            # Create a custom theme
            custom_colors = ColorScheme(primary="red", data="blue")
            custom_config = ThemeConfig(colors=custom_colors)
            custom_theme = ThemeManager(custom_config)

            # Save the theme
            manager.save_theme("test_theme", custom_theme)

            # Load it back
            loaded_theme = manager.load_theme("test_theme")

            # Verify colors match
            assert loaded_theme.primary == "red"
            assert loaded_theme.data == "blue"

    def test_cannot_overwrite_builtin_theme(self):
        """Test that built-in themes cannot be overwritten."""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = ThemeConfigManager(temp_dir)

            with pytest.raises(
                ThemeConfigError, match="Cannot overwrite built-in theme"
            ):
                manager.save_theme("default", ThemeManager())

    def test_delete_custom_theme(self):
        """Test deleting a custom theme."""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = ThemeConfigManager(temp_dir)

            # Save a custom theme
            manager.save_theme("deleteme", ThemeManager())

            # Verify it exists
            assert "deleteme" in manager.list_available_themes()

            # Delete it
            manager.delete_theme("deleteme")

            # Verify it's gone
            assert "deleteme" not in manager.list_available_themes()

    def test_cannot_delete_builtin_theme(self):
        """Test that built-in themes cannot be deleted."""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = ThemeConfigManager(temp_dir)

            with pytest.raises(ThemeConfigError, match="Cannot delete built-in theme"):
                manager.delete_theme("default")

    def test_delete_nonexistent_theme(self):
        """Test deleting a theme that doesn't exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = ThemeConfigManager(temp_dir)

            with pytest.raises(ThemeConfigError, match="Theme 'nonexistent' not found"):
                manager.delete_theme("nonexistent")

    def test_apply_theme(self):
        """Test applying a theme."""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = ThemeConfigManager(temp_dir)
            original_theme = get_theme()

            try:
                # Apply dark theme
                manager.apply_theme("dark")

                # Verify theme changed
                current_theme = get_theme()
                assert current_theme.primary == "bright_cyan"

            finally:
                # Restore original theme
                set_theme(original_theme)

    def test_get_current_theme_name_builtin(self):
        """Test getting current theme name for built-in themes."""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = ThemeConfigManager(temp_dir)
            original_theme = get_theme()

            try:
                # Apply dark theme
                manager.apply_theme("dark")

                # Should recognize it as dark theme
                assert manager.get_current_theme_name() == "dark"

            finally:
                set_theme(original_theme)

    def test_get_current_theme_name_custom(self):
        """Test getting current theme name returns 'custom' for unrecognized themes."""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = ThemeConfigManager(temp_dir)
            original_theme = get_theme()

            try:
                # Apply a custom theme that's not saved
                custom_colors = ColorScheme(primary="magenta")
                custom_theme = ThemeManager(ThemeConfig(colors=custom_colors))
                set_theme(custom_theme)

                # Should return "custom"
                assert manager.get_current_theme_name() == "custom"

            finally:
                set_theme(original_theme)

    def test_create_custom_theme(self):
        """Test creating a custom theme based on existing theme."""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = ThemeConfigManager(temp_dir)

            # Create custom theme based on default with overrides
            custom_theme = manager.create_custom_theme(
                "my_theme",
                base_theme="default",
                color_overrides={"primary": "magenta", "error": "bright_red"},
            )

            # Verify overrides applied
            assert custom_theme.primary == "magenta"
            assert custom_theme.error == "bright_red"

            # Verify other colors inherited from base
            default_theme = manager.load_theme("default")
            assert custom_theme.data == default_theme.data

            # Verify theme was saved
            assert "my_theme" in manager.list_available_themes()

    def test_get_theme_preview(self):
        """Test getting theme preview."""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = ThemeConfigManager(temp_dir)

            preview = manager.get_theme_preview("default")

            # Should contain theme name and color examples
            assert "Theme: default" in preview
            assert "Primary:" in preview
            assert "Error:" in preview
            assert "[red]" in preview  # Should contain Rich markup


class TestGlobalFunctions:
    """Test global convenience functions."""

    def test_get_set_config_manager(self):
        """Test getting and setting global config manager."""
        original_manager = get_config_manager()

        try:
            # Create new manager
            with tempfile.TemporaryDirectory() as temp_dir:
                new_manager = ThemeConfigManager(temp_dir)
                set_config_manager(new_manager)

                # Verify it was set
                assert get_config_manager() is new_manager

        finally:
            # Restore original
            set_config_manager(original_manager)

    def test_list_themes_function(self):
        """Test global list_themes function."""
        themes = list_themes()
        assert isinstance(themes, list)
        assert "default" in themes

    def test_apply_theme_function(self):
        """Test global apply_theme function."""
        original_theme = get_theme()

        try:
            apply_theme("dark")
            assert get_theme().primary == "bright_cyan"

        finally:
            set_theme(original_theme)

    def test_save_current_theme_function(self):
        """Test global save_current_theme function."""
        original_manager = get_config_manager()

        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                test_manager = ThemeConfigManager(temp_dir)
                set_config_manager(test_manager)

                # Save current theme
                save_current_theme("saved_theme")

                # Verify it was saved
                assert "saved_theme" in list_themes()

        finally:
            set_config_manager(original_manager)

    def test_create_custom_theme_function(self):
        """Test global create_custom_theme function."""
        original_manager = get_config_manager()

        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                test_manager = ThemeConfigManager(temp_dir)
                set_config_manager(test_manager)

                # Create custom theme
                create_custom_theme("custom", color_overrides={"primary": "purple"})

                # Verify it was created
                assert "custom" in list_themes()

        finally:
            set_config_manager(original_manager)

    def test_get_current_theme_name_function(self):
        """Test global get_current_theme_name function."""
        original_theme = get_theme()

        try:
            apply_theme("minimal")
            assert get_current_theme_name() == "minimal"

        finally:
            set_theme(original_theme)

    def test_preview_theme_function(self):
        """Test global preview_theme function."""
        preview = preview_theme("light")
        assert "Theme: light" in preview
        assert "Primary:" in preview


class TestErrorHandling:
    """Test error handling in theme configuration."""

    def test_invalid_json_file(self):
        """Test handling of invalid JSON theme files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = ThemeConfigManager(temp_dir)

            # Create invalid JSON file
            theme_file = Path(temp_dir) / "invalid.json"
            with open(theme_file, "w") as f:
                f.write("{ invalid json }")

            with pytest.raises(ThemeConfigError, match="Failed to load theme"):
                manager.load_theme("invalid")

    def test_missing_required_fields(self):
        """Test handling of theme files with missing required fields."""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = ThemeConfigManager(temp_dir)

            # Create theme file with missing fields
            incomplete_theme = {"colors": {}}  # Missing required fields
            theme_file = Path(temp_dir) / "incomplete.json"
            with open(theme_file, "w") as f:
                json.dump(incomplete_theme, f)

            # Should still load with defaults
            theme = manager.load_theme("incomplete")
            assert isinstance(theme, ThemeManager)

    @pytest.mark.skip(
        reason="File permission test is platform-specific and flaky on macOS"
    )
    def test_file_permission_errors(self):
        """Test handling of file permission errors."""
        pass


class TestThemeComparison:
    """Test theme comparison functionality."""

    def test_themes_equal_same_colors(self):
        """Test that themes with same colors are considered equal."""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = ThemeConfigManager(temp_dir)

            colors1 = ColorScheme(primary="red", data="blue")
            colors2 = ColorScheme(primary="red", data="blue")

            theme1 = ThemeManager(ThemeConfig(colors=colors1))
            theme2 = ThemeManager(ThemeConfig(colors=colors2))

            assert manager._themes_equal(theme1, theme2)

    def test_themes_not_equal_different_colors(self):
        """Test that themes with different colors are not considered equal."""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = ThemeConfigManager(temp_dir)

            colors1 = ColorScheme(primary="red", data="blue")
            colors2 = ColorScheme(primary="green", data="blue")

            theme1 = ThemeManager(ThemeConfig(colors=colors1))
            theme2 = ThemeManager(ThemeConfig(colors=colors2))

            assert not manager._themes_equal(theme1, theme2)
