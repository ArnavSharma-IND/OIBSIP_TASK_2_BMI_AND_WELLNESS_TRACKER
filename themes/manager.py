"""
Centralized Theme Manager
Handles theme state, dynamic switching, ttk style configuration, observer subscriptions,
and typography definitions.
"""

from typing import Dict, Any, Callable, List
from tkinter import ttk
from themes.light import LIGHT_THEME
from themes.dark import DARK_THEME
from config import load_settings, save_settings, get_font_family
from utils.logger import logger


class ThemeManager:
    """Singleton-style manager providing unified styling and live theme toggling."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ThemeManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if getattr(self, "_initialized", False):
            return

        settings = load_settings()
        initial_theme = settings.get("theme", "light")
        self._current_theme_name = initial_theme if initial_theme in ("light", "dark") else "light"
        self._font_family = get_font_family()
        self._listeners: List[Callable[[Dict[str, Any]], None]] = []
        self._initialized = True

    @property
    def current_theme_name(self) -> str:
        return self._current_theme_name

    @property
    def is_dark(self) -> bool:
        return self._current_theme_name == "dark"

    @property
    def theme(self) -> Dict[str, Any]:
        return DARK_THEME if self.is_dark else LIGHT_THEME

    def get(self, key: str, default: Any = None) -> Any:
        """Fetch a color or style value by key from the active theme."""
        return self.theme.get(key, default)

    def get_category_color(self, category: str) -> str:
        """Fetch theme-harmonized color for a given BMI category."""
        mapping = {
            "Underweight": self.get("category_underweight"),
            "Normal": self.get("category_normal"),
            "Overweight": self.get("category_overweight"),
            "Obese": self.get("category_obese"),
        }
        return mapping.get(category, self.get("text_primary"))

    def set_theme(self, theme_name: str) -> None:
        """Switch active theme ('light' or 'dark'), persist preference, and notify observers."""
        if theme_name not in ("light", "dark"):
            logger.warning(f"Ignored unknown theme request: '{theme_name}'")
            return

        if self._current_theme_name == theme_name:
            return

        self._current_theme_name = theme_name
        logger.info(f"Theme switched to: {theme_name}")

        # Persist to settings
        settings = load_settings()
        settings["theme"] = theme_name
        save_settings(settings)

        # Notify observers
        for listener in list(self._listeners):
            try:
                listener(self.theme)
            except Exception as e:
                logger.error(f"Error notifying theme observer: {e}")

    def toggle_theme(self) -> str:
        """Toggle between light and dark themes."""
        new_theme = "light" if self.is_dark else "dark"
        self.set_theme(new_theme)
        return new_theme

    def subscribe(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        """Register a callback that receives the new theme dict whenever it updates."""
        if callback not in self._listeners:
            self._listeners.append(callback)

    def unsubscribe(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        """Unregister a theme change callback."""
        if callback in self._listeners:
            self._listeners.remove(callback)

    # Typography definitions
    @property
    def font_family(self) -> str:
        return self._font_family

    @property
    def font_hero(self) -> tuple:
        return (self._font_family, 38, "bold")

    @property
    def font_hero_small(self) -> tuple:
        return (self._font_family, 26, "bold")

    @property
    def font_title(self) -> tuple:
        return (self._font_family, 18, "bold")

    @property
    def font_subtitle(self) -> tuple:
        return (self._font_family, 13, "bold")

    @property
    def font_body(self) -> tuple:
        return (self._font_family, 10, "normal")

    @property
    def font_body_bold(self) -> tuple:
        return (self._font_family, 10, "bold")

    @property
    def font_small(self) -> tuple:
        return (self._font_family, 9, "normal")

    @property
    def font_caption(self) -> tuple:
        return (self._font_family, 8, "bold")

    def configure_ttk_styles(self, style: ttk.Style) -> None:
        """Apply minimalist palette to standard ttk widgets."""
        t = self.theme

        try:
            style.theme_use("clam")
        except Exception:
            pass

        # Treeview (History Table)
        style.configure(
            "Treeview",
            background=t["surface"],
            foreground=t["text_primary"],
            fieldbackground=t["surface"],
            rowheight=34,
            borderwidth=0,
            font=self.font_body,
        )
        style.configure(
            "Treeview.Heading",
            background=t["surface_secondary"],
            foreground=t["text_secondary"],
            relief="flat",
            font=self.font_caption,
            padding=8,
            borderwidth=0,
        )
        style.map(
            "Treeview",
            background=[("selected", t["accent"])],
            foreground=[("selected", t["text_on_accent"])],
        )

        # Scrollbars
        style.configure(
            "Vertical.TScrollbar",
            gripcount=0,
            background=t["surface_secondary"],
            darkcolor=t["surface_secondary"],
            lightcolor=t["surface_secondary"],
            troughcolor=t["bg"],
            bordercolor=t["bg"],
            arrowcolor=t["text_secondary"],
        )

        # Combobox
        style.configure(
            "TCombobox",
            background=t["surface_secondary"],
            fieldbackground=t["surface"],
            foreground=t["text_primary"],
            darkcolor=t["border"],
            lightcolor=t["border"],
            arrowcolor=t["text_primary"],
            bordercolor=t["border"],
            relief="flat",
            padding=5,
        )
        style.map(
            "TCombobox",
            fieldbackground=[("readonly", t["surface"])],
            selectbackground=[("readonly", t["accent"])],
            selectforeground=[("readonly", t["text_on_accent"])],
        )


# Global Theme Manager instance
theme_mgr = ThemeManager()
