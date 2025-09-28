"""Theme configuration utilities for user customisation of Cascade display styling.

This module provides utilities for loading, saving, and applying theme configurations,
allowing users to customise the appearance of the Cascade shell interface.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .theme import (
    ColorScheme,
    ThemeConfig,
    ThemeManager,
    create_dark_theme,
    create_light_theme,
    create_minimal_theme,
    get_theme,
    set_theme,
)


class ThemeConfigError(Exception):
    """Exception raised for theme configuration errors."""


class ThemeConfigManager:
    """Manager for loading, saving, and applying theme configurations."""

    def __init__(self, config_dir: str | Path | None = None):
        """Initialise theme configuration manager.

        Args:
            config_dir: Directory to store theme configuration files.
                Defaults to ~/.config/cascade/themes/
        """
        if config_dir is None:
            config_dir = Path.home() / ".config" / "cascade" / "themes"

        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)

        self._builtin_themes = {
            "default": self._create_default_theme,
            "dark": create_dark_theme,
            "light": create_light_theme,
            "minimal": create_minimal_theme,
        }

    def _create_default_theme(self) -> ThemeManager:
        """Create the default theme."""
        return ThemeManager()  # Uses default ColorScheme

    def list_available_themes(self) -> list[str]:
        """List all available themes (built-in and custom).

        Returns:
            List of theme names
        """
        themes = list(self._builtin_themes.keys())

        for theme_file in self.config_dir.glob("*.json"):
            theme_name = theme_file.stem
            if theme_name not in themes:
                themes.append(theme_name)

        return sorted(themes)

    def get_current_theme_name(self) -> str:
        """Get the name of the currently active theme.

        Returns:
            Theme name, or "custom" if it's a non-standard theme
        """
        current_theme = get_theme()

        for name, creator in self._builtin_themes.items():
            builtin_theme = creator()
            if self._themes_equal(current_theme, builtin_theme):
                return name

        for theme_file in self.config_dir.glob("*.json"):
            try:
                saved_theme = self.load_theme(theme_file.stem)
                if self._themes_equal(current_theme, saved_theme):
                    return theme_file.stem
            except ThemeConfigError:  # noqa: PERF203
                continue

        return "custom"

    def _themes_equal(self, theme1: ThemeManager, theme2: ThemeManager) -> bool:
        """Check if two themes have the same color configuration."""
        colors1 = theme1.config.colors
        colors2 = theme2.config.colors

        for attr in [
            "primary",
            "secondary",
            "data",
            "numeric",
            "status",
            "success",
            "warning",
            "error",
            "info",
            "highlight",
            "muted",
            "header",
            "border",
        ]:
            if getattr(colors1, attr) != getattr(colors2, attr):
                return False

        return True

    def apply_theme(self, theme_name: str) -> None:
        """Apply a theme by name.

        Args:
            theme_name: Name of the theme to apply

        Raises:
            ThemeConfigError: If theme cannot be found or loaded
        """
        theme = self.load_theme(theme_name)
        set_theme(theme)

    def load_theme(self, theme_name: str) -> ThemeManager:
        """Load a theme by name.

        Args:
            theme_name: Name of the theme to load

        Returns:
            ThemeManager instance for the theme

        Raises:
            ThemeConfigError: If theme cannot be found or loaded
        """
        if theme_name in self._builtin_themes:
            return self._builtin_themes[theme_name]()

        theme_file = self.config_dir / f"{theme_name}.json"
        if not theme_file.exists():
            raise ThemeConfigError(f"Theme '{theme_name}' not found")

        try:
            with open(theme_file) as f:
                theme_data = json.load(f)

            return self._theme_from_dict(theme_data)

        except (json.JSONDecodeError, KeyError, TypeError) as e:
            raise ThemeConfigError(f"Failed to load theme '{theme_name}': {e}") from e

    def save_theme(self, theme_name: str, theme: ThemeManager | None = None) -> None:
        """Save a theme to the configuration directory.

        Args:
            theme_name: Name to save the theme as
            theme: Theme to save. If None, saves the current theme.

        Raises:
            ThemeConfigError: If theme cannot be saved
        """
        if theme is None:
            theme = get_theme()

        if theme_name in self._builtin_themes:
            raise ThemeConfigError(f"Cannot overwrite built-in theme '{theme_name}'")

        theme_data = self._theme_to_dict(theme)
        theme_file = self.config_dir / f"{theme_name}.json"

        try:
            with open(theme_file, "w") as f:
                json.dump(theme_data, f, indent=2)
        except (OSError, ValueError) as e:
            raise ThemeConfigError(f"Failed to save theme '{theme_name}': {e}") from e

    def delete_theme(self, theme_name: str) -> None:
        """Delete a custom theme.

        Args:
            theme_name: Name of the theme to delete

        Raises:
            ThemeConfigError: If theme cannot be deleted
        """
        if theme_name in self._builtin_themes:
            raise ThemeConfigError(f"Cannot delete built-in theme '{theme_name}'")

        theme_file = self.config_dir / f"{theme_name}.json"
        if not theme_file.exists():
            raise ThemeConfigError(f"Theme '{theme_name}' not found")

        try:
            theme_file.unlink()
        except OSError as e:
            raise ThemeConfigError(f"Failed to delete theme '{theme_name}': {e}") from e

    def create_custom_theme(
        self,
        name: str,
        base_theme: str = "default",
        color_overrides: dict[str, str] | None = None,
    ) -> ThemeManager:
        """Create a custom theme based on an existing theme.

        Args:
            name: Name for the new theme
            base_theme: Base theme to start from
            color_overrides: Dictionary of color attributes to override

        Returns:
            ThemeManager for the new custom theme

        Raises:
            ThemeConfigError: If base theme cannot be loaded
        """
        base = self.load_theme(base_theme)

        base_colors = base.config.colors
        color_kwargs = {
            "primary": base_colors.primary,
            "secondary": base_colors.secondary,
            "data": base_colors.data,
            "numeric": base_colors.numeric,
            "status": base_colors.status,
            "success": base_colors.success,
            "warning": base_colors.warning,
            "error": base_colors.error,
            "info": base_colors.info,
            "highlight": base_colors.highlight,
            "muted": base_colors.muted,
            "header": base_colors.header,
            "border": base_colors.border,
        }

        if color_overrides:
            for key, value in color_overrides.items():
                if key in color_kwargs:
                    color_kwargs[key] = value

        custom_colors = ColorScheme(**color_kwargs)
        custom_config = ThemeConfig(colors=custom_colors)
        custom_theme = ThemeManager(custom_config)

        self.save_theme(name, custom_theme)

        return custom_theme

    def _theme_to_dict(self, theme: ThemeManager) -> dict[str, Any]:
        """Convert a theme to a dictionary for JSON serialisation."""
        colors = theme.config.colors
        return {
            "colors": {
                "primary": colors.primary,
                "secondary": colors.secondary,
                "data": colors.data,
                "numeric": colors.numeric,
                "status": colors.status,
                "success": colors.success,
                "warning": colors.warning,
                "error": colors.error,
                "info": colors.info,
                "highlight": colors.highlight,
                "muted": colors.muted,
                "header": colors.header,
                "border": colors.border,
            },
            "table_expand": theme.config.table_expand,
            "panel_expand": theme.config.panel_expand,
            "panel_border_style": theme.config.panel_border_style,
        }

    def _theme_from_dict(self, theme_data: dict[str, Any]) -> ThemeManager:
        """Create a theme from a dictionary."""
        colors_data = theme_data.get("colors", {})
        colors = ColorScheme(
            primary=colors_data.get("primary", "cyan"),
            secondary=colors_data.get("secondary", "white"),
            data=colors_data.get("data", "green"),
            numeric=colors_data.get("numeric", "yellow"),
            status=colors_data.get("status", "yellow"),
            success=colors_data.get("success", "green"),
            warning=colors_data.get("warning", "yellow"),
            error=colors_data.get("error", "red"),
            info=colors_data.get("info", "blue"),
            highlight=colors_data.get("highlight", "magenta"),
            muted=colors_data.get("muted", "dim"),
            header=colors_data.get("header", "bold magenta"),
            border=colors_data.get("border", "bright_blue"),
        )

        config = ThemeConfig(
            colors=colors,
            table_expand=theme_data.get("table_expand", False),
            panel_expand=theme_data.get("panel_expand", False),
            panel_border_style=theme_data.get("panel_border_style", "bright_blue"),
        )

        return ThemeManager(config)

    def get_theme_preview(self, theme_name: str) -> str:
        """Get a preview string showing what a theme looks like.

        Args:
            theme_name: Name of the theme to preview

        Returns:
            Rich markup string showing theme colors

        Raises:
            ThemeConfigError: If theme cannot be loaded
        """
        theme = self.load_theme(theme_name)

        preview_parts = [
            f"Theme: {theme_name}",
            "",
            f"Primary: {theme.primary_text('identifier')}",
            f"Data: {theme.data_text('content')}",
            f"Success: {theme.success_text('operation completed')}",
            f"Warning: {theme.warning_text('potential issue')}",
            f"Error: {theme.error_text('operation failed')}",
            f"Info: {theme.info_text('information')}",
            f"Highlight: {theme.highlight_text('emphasized text')}",
            f"Muted: {theme.muted_text('secondary details')}",
        ]

        return "\n".join(preview_parts)


# Global configuration manager instance.
# TODO: Can we move this somewhere? Maybe the shell object?
_config_manager = ThemeConfigManager()


def get_config_manager() -> ThemeConfigManager:
    """Get the global theme configuration manager."""
    return _config_manager


def set_config_manager(manager: ThemeConfigManager) -> None:
    """Set a new global theme configuration manager."""
    global _config_manager
    _config_manager = manager


# Convenience functions:


def list_themes() -> list[str]:
    """List all available themes."""
    return get_config_manager().list_available_themes()


def apply_theme(theme_name: str) -> None:
    """Apply a theme by name."""
    get_config_manager().apply_theme(theme_name)


def save_current_theme(theme_name: str) -> None:
    """Save the current theme with a given name."""
    get_config_manager().save_theme(theme_name)


def create_custom_theme(
    name: str,
    base_theme: str = "default",
    color_overrides: dict[str, str] | None = None,
):
    """Create and save a custom theme."""
    get_config_manager().create_custom_theme(name, base_theme, color_overrides)


def get_current_theme_name() -> str:
    """Get the name of the currently active theme."""
    return get_config_manager().get_current_theme_name()


def preview_theme(theme_name: str) -> str:
    """Get a preview of a theme."""
    return get_config_manager().get_theme_preview(theme_name)
