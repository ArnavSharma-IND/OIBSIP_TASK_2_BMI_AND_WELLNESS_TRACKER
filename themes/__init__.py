"""Theme management and definitions."""
from themes.manager import theme_mgr, ThemeManager
from themes.light import LIGHT_THEME
from themes.dark import DARK_THEME

__all__ = ["theme_mgr", "ThemeManager", "LIGHT_THEME", "DARK_THEME"]
