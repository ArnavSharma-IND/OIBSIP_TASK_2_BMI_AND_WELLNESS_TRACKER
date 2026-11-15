"""
BMI & Wellness Tracker – Master Application Shell
Production-quality desktop application with persistent SQLite storage, multi-user profiles,
editorial minimalist aesthetics, light & dark theme switching, and live analytics.
"""

import sys
import ctypes
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, Any, Optional

from config import (
    APP_NAME,
    APP_VERSION,
    APP_TITLE,
    WINDOW_WIDTH,
    WINDOW_HEIGHT,
    MIN_WINDOW_WIDTH,
    MIN_WINDOW_HEIGHT,
    load_settings,
    save_settings,
)
from utils.logger import logger
from utils.helpers import center_window
from themes.manager import theme_mgr
from services.app_state import app_state
from database import db

# Import UI Views
from modules.dashboard import DashboardView
from modules.calculator import CalculatorView
from modules.history import HistoryView
from modules.trends import TrendsView
from modules.user_management import UserManagementView
from modules.settings import SettingsView


def enable_windows_high_dpi():
    """Enable Windows Per-Monitor High DPI awareness for crisp fonts and graphics."""
    if sys.platform == "win32":
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(1)  # Process_System_DPI_Aware
        except Exception:
            try:
                ctypes.windll.user32.SetProcessDPIAware()
            except Exception:
                pass


class MainApplication(tk.Tk):
    """Top-level Tkinter application container and navigation shell."""

    def __init__(self):
        super().__init__()

        logger.info(f"Starting {APP_NAME} v{APP_VERSION}")

        # Window Configurations
        self.title(APP_TITLE)
        self.minsize(MIN_WINDOW_WIDTH, MIN_WINDOW_HEIGHT)
        center_window(self, WINDOW_WIDTH, WINDOW_HEIGHT)

        # Style System
        self.style = ttk.Style(self)
        theme_mgr.configure_ttk_styles(self.style)

        # Active Section Tracking
        settings = load_settings()
        self._current_tab = settings.get("last_tab", "overview")

        # Views Storage
        self._views: Dict[str, tk.Widget] = {}

        # Shell Structure
        self._build_shell()

        # Listeners
        theme_mgr.subscribe(self._on_theme_changed)
        app_state.subscribe_user_changed(self._on_user_changed)
        app_state.subscribe_nav_requested(self.navigate_to)

        # Protocol for clean exit
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        # Initial Navigation
        self.navigate_to(self._current_tab)

    def _build_shell(self) -> None:
        """Construct the two-pane application layout: minimalist navigation sidebar + view canvas."""
        t = theme_mgr.theme
        self.config(bg=t["bg"])

        # -------------------------------------------------------------
        # Left Sidebar (Floating Minimalist Navigation)
        # -------------------------------------------------------------
        self.sidebar = tk.Frame(self, bg=t["surface"], width=230)
        self.sidebar.pack(side=tk.LEFT, fill=tk.Y)
        self.sidebar.pack_propagate(False)

        # Hairline Vertical Separator
        self.sidebar_border = tk.Frame(self, width=1, bg=t["border"])
        self.sidebar_border.pack(side=tk.LEFT, fill=tk.Y)

        # Brand Title Block
        brand_frame = tk.Frame(self.sidebar, bg=t["surface"], padx=24, pady=32)
        brand_frame.pack(fill=tk.X)

        self.lbl_brand_tag = tk.Label(
            brand_frame,
            text="EDITORIAL WELLNESS",
            font=theme_mgr.font_caption,
            fg=t["accent"],
            bg=t["surface"],
            anchor="w",
        )
        self.lbl_brand_tag.pack(anchor="w")

        self.lbl_brand_name = tk.Label(
            brand_frame,
            text="BMI Tracker",
            font=theme_mgr.font_title,
            fg=t["text_primary"],
            bg=t["surface"],
            anchor="w",
        )
        self.lbl_brand_name.pack(anchor="w", pady=(2, 0))

        # Thin divider below brand
        self.sep_brand = tk.Frame(self.sidebar, height=1, bg=t["border"])
        self.sep_brand.pack(fill=tk.X, padx=20, pady=(0, 20))

        # Navigation Links List
        self.nav_frame = tk.Frame(self.sidebar, bg=t["surface"])
        self.nav_frame.pack(fill=tk.X, padx=14)

        self.nav_items = [
            ("overview", "Overview"),
            ("calculator", "Calculator"),
            ("history", "History"),
            ("trends", "Trends"),
            ("profiles", "Profiles"),
            ("settings", "Settings"),
        ]

        self.nav_buttons: Dict[str, tk.Label] = {}
        for tab_id, tab_label in self.nav_items:
            btn = tk.Label(
                self.nav_frame,
                text=tab_label,
                font=theme_mgr.font_body,
                fg=t["text_secondary"],
                bg=t["surface"],
                padx=16,
                pady=11,
                anchor="w",
                cursor="hand2",
            )
            btn.pack(fill=tk.X, pady=2)
            btn.bind("<Button-1>", lambda e, tid=tab_id: self.navigate_to(tid))
            self.nav_buttons[tab_id] = btn

        # Bottom Sidebar Elements: Active User Pill + Theme Toggle
        bottom_nav = tk.Frame(self.sidebar, bg=t["surface"], padx=18, pady=24)
        bottom_nav.pack(side=tk.BOTTOM, fill=tk.X)

        # Hairline divider above footer
        self.sep_footer = tk.Frame(self.sidebar, height=1, bg=t["border"])
        self.sep_footer.pack(side=tk.BOTTOM, fill=tk.X, padx=20, pady=(0, 14))

        # Active User indicator
        self.active_user_frame = tk.Frame(bottom_nav, bg=t["surface_secondary"], padx=12, pady=8)
        self.active_user_frame.pack(fill=tk.X, pady=(0, 12))

        self.lbl_active_prefix = tk.Label(
            self.active_user_frame,
            text="ACTIVE PROFILE",
            font=theme_mgr.font_caption,
            fg=t["text_secondary"],
            bg=t["surface_secondary"],
            anchor="w",
        )
        self.lbl_active_prefix.pack(anchor="w")

        self.lbl_active_user = tk.Label(
            self.active_user_frame,
            text=app_state.active_username,
            font=theme_mgr.font_body_bold,
            fg=t["text_primary"],
            bg=t["surface_secondary"],
            anchor="w",
        )
        self.lbl_active_user.pack(anchor="w")

        # Theme Quick Switch Button
        self.btn_theme_toggle = tk.Button(
            bottom_nav,
            text=f"Switch to {'Dark' if not theme_mgr.is_dark else 'Light'} Theme",
            command=self._on_toggle_theme,
            font=theme_mgr.font_small,
            bg=t["surface_secondary"],
            fg=t["text_primary"],
            activebackground=t["surface_active"],
            activeforeground=t["text_primary"],
            relief=tk.FLAT,
            bd=0,
            padx=10,
            pady=7,
            cursor="hand2",
        )
        self.btn_theme_toggle.pack(fill=tk.X)

        # -------------------------------------------------------------
        # Right Main Content Canvas
        # -------------------------------------------------------------
        self.content_area = tk.Frame(self, bg=t["bg"])
        self.content_area.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    def navigate_to(self, tab_id: str) -> None:
        """Switch view in the main content container and update navigation styles."""
        if tab_id not in [item[0] for item in self.nav_items]:
            tab_id = "overview"

        self._current_tab = tab_id
        t = theme_mgr.theme

        # Persist last visited tab
        settings = load_settings()
        settings["last_tab"] = tab_id
        save_settings(settings)

        # Update navigation styles
        for tid, btn in self.nav_buttons.items():
            if tid == tab_id:
                btn.config(
                    bg=t["surface_secondary"],
                    fg=t["accent"],
                    font=theme_mgr.font_body_bold,
                )
            else:
                btn.config(
                    bg=t["surface"],
                    fg=t["text_secondary"],
                    font=theme_mgr.font_body,
                )

        # Destroy current view if present
        for child in self.content_area.winfo_children():
            child.pack_forget()

        # Instantiate or retrieve target view
        if tab_id not in self._views:
            if tab_id == "overview":
                self._views[tab_id] = DashboardView(self.content_area)
            elif tab_id == "calculator":
                self._views[tab_id] = CalculatorView(self.content_area)
            elif tab_id == "history":
                self._views[tab_id] = HistoryView(self.content_area)
            elif tab_id == "trends":
                self._views[tab_id] = TrendsView(self.content_area)
            elif tab_id == "profiles":
                self._views[tab_id] = UserManagementView(self.content_area)
            elif tab_id == "settings":
                self._views[tab_id] = SettingsView(self.content_area)

        # Show target view
        view = self._views[tab_id]
        view.pack(fill=tk.BOTH, expand=True)

        # Refresh data if view supports it
        if hasattr(view, "refresh_data"):
            view.refresh_data()
        elif hasattr(view, "load_records"):
            view.load_records()
        elif hasattr(view, "render_analytics"):
            view.render_analytics()
        elif hasattr(view, "load_users"):
            view.load_users()

    def _on_toggle_theme(self) -> None:
        """Toggle light/dark theme."""
        theme_mgr.toggle_theme()

    def _on_user_changed(self, user: Dict[str, Any]) -> None:
        """Update active user label in sidebar."""
        self.lbl_active_user.config(text=user["username"])

    def _on_theme_changed(self, theme: Dict[str, Any]) -> None:
        """Update shell borders and navigation colors."""
        theme_mgr.configure_ttk_styles(self.style)

        self.config(bg=theme["bg"])
        self.sidebar.config(bg=theme["surface"])
        self.sidebar_border.config(bg=theme["border"])
        self.lbl_brand_tag.config(fg=theme["accent"], bg=theme["surface"])
        self.lbl_brand_name.config(fg=theme["text_primary"], bg=theme["surface"])
        self.sep_brand.config(bg=theme["border"])
        self.nav_frame.config(bg=theme["surface"])
        self.sep_footer.config(bg=theme["border"])
        self.active_user_frame.config(bg=theme["surface_secondary"])
        self.lbl_active_prefix.config(fg=theme["text_secondary"], bg=theme["surface_secondary"])
        self.lbl_active_user.config(fg=theme["text_primary"], bg=theme["surface_secondary"])
        self.btn_theme_toggle.config(
            text=f"Switch to {'Dark' if not theme_mgr.is_dark else 'Light'} Theme",
            bg=theme["surface_secondary"],
            fg=theme["text_primary"],
            activebackground=theme["surface_active"],
            activeforeground=theme["text_primary"],
        )
        self.content_area.config(bg=theme["bg"])

        # Re-apply active nav highlight
        for tid, btn in self.nav_buttons.items():
            if tid == self._current_tab:
                btn.config(
                    bg=theme["surface_secondary"],
                    fg=theme["accent"],
                    font=theme_mgr.font_body_bold,
                )
            else:
                btn.config(
                    bg=theme["surface"],
                    fg=theme["text_secondary"],
                    font=theme_mgr.font_body,
                )

    def _on_close(self) -> None:
        """Handle application exit gracefully."""
        logger.info("Application shutting down.")
        self.destroy()


def main():
    """Application entry point."""
    enable_windows_high_dpi()
    app = MainApplication()
    app.mainloop()


if __name__ == "__main__":
    main()
