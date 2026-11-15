"""
GUI Smoke Tests
Verifies that Tkinter windows, ttk widgets, Matplotlib figure canvases,
and all 6 application views initialize and transition cleanly without graphical errors.
"""

import pytest
import tkinter as tk
from main import MainApplication
from themes.manager import theme_mgr


@pytest.fixture(scope="class")
def gui_app():
    """Create a live Tkinter application instance for testing and destroy after class tests."""
    app = MainApplication()
    # Withdraw window so it doesn't pop up during automated tests
    app.withdraw()
    yield app
    try:
        app.destroy()
    except Exception:
        pass


class TestGUIWorkflow:
    """Verifies GUI lifecycle, navigation, and theme switches."""

    def test_app_initialization(self, gui_app):
        assert gui_app is not None
        assert gui_app.title().startswith("BMI & Wellness Tracker")
        assert gui_app._current_tab in ["overview", "calculator", "history", "trends", "profiles", "settings"]

    def test_navigate_all_tabs(self, gui_app):
        # Test navigation to every tab
        tabs = ["overview", "calculator", "history", "trends", "profiles", "settings"]
        for tab in tabs:
            gui_app.navigate_to(tab)
            gui_app.update_idletasks()
            assert gui_app._current_tab == tab
            assert tab in gui_app._views

    def test_theme_toggle_in_gui(self, gui_app):
        initial_theme = theme_mgr.current_theme_name

        # Toggle theme
        gui_app._on_toggle_theme()
        gui_app.update_idletasks()
        assert theme_mgr.current_theme_name != initial_theme

        # Toggle back
        gui_app._on_toggle_theme()
        gui_app.update_idletasks()
        assert theme_mgr.current_theme_name == initial_theme
