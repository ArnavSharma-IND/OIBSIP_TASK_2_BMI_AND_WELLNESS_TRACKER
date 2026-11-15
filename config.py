"""
Application Configuration & Environment Settings
Handles dynamic path resolution (development and PyInstaller frozen executable),
system font resolution, default preferences, and application constants.
"""

import os
import sys
import json
import tempfile
from pathlib import Path

# Ensure Matplotlib config dir is writable to eliminate warnings
os.environ.setdefault("MPLCONFIGDIR", os.path.join(tempfile.gettempdir(), "bmi_tracker_mpl"))

# Determine base directory whether running as script or PyInstaller frozen bundle
if getattr(sys, "frozen", False):
    # Running in a PyInstaller bundle
    BASE_DIR = Path(sys.executable).parent
    BUNDLE_DIR = Path(getattr(sys, "_MEIPASS", sys.executable))
else:
    # Running in normal Python environment
    BASE_DIR = Path(__file__).resolve().parent
    BUNDLE_DIR = BASE_DIR

# Core application paths
DATA_DIR = BASE_DIR / "data"
ASSETS_DIR = BASE_DIR / "assets"
DB_PATH = DATA_DIR / "bmi_records.db"
SETTINGS_PATH = DATA_DIR / "settings.json"
LOG_PATH = DATA_DIR / "app.log"

# Ensure data directory exists
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Application metadata
APP_NAME = "BMI & Wellness Tracker"
APP_VERSION = "1.0.0"
APP_AUTHOR = "Arnav Sharma"
APP_TITLE = f"{APP_NAME} v{APP_VERSION}"

# UI Window configurations
WINDOW_WIDTH = 1120
WINDOW_HEIGHT = 740
MIN_WINDOW_WIDTH = 960
MIN_WINDOW_HEIGHT = 640

# Database constants
SCHEMA_VERSION = 1

# Default user settings
DEFAULT_SETTINGS = {
    "theme": "light",
    "active_user_id": None,
    "last_tab": "overview",
    "enable_insights": True,
}


def load_settings() -> dict:
    """Load user settings from settings.json or return defaults."""
    if SETTINGS_PATH.exists():
        try:
            with open(SETTINGS_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                settings = dict(DEFAULT_SETTINGS)
                settings.update(data)
                return settings
        except Exception:
            return dict(DEFAULT_SETTINGS)
    return dict(DEFAULT_SETTINGS)


def save_settings(settings: dict) -> bool:
    """Persist settings to settings.json."""
    try:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=4)
        return True
    except Exception:
        return False


def get_font_family() -> str:
    """
    Select the cleanest modern typographic font available on the system.
    Prioritizes modern sans-serif fonts for the editorial minimalist aesthetic.
    """
    # Standard clean fonts in order of preference
    candidates = ["Inter", "Segoe UI", "SF Pro Text", "Helvetica Neue", "Arial"]
    # In Tkinter on Windows, Segoe UI is universally available and looks modern & crisp
    return "Segoe UI"
