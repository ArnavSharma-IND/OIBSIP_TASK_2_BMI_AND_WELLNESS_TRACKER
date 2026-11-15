"""
General Helper Utilities
Time formatting, layout math, greeting generation, and presentation helpers.
"""

from datetime import datetime
from typing import Optional


def get_time_greeting() -> str:
    """Return a warm, natural time-of-day greeting."""
    hour = datetime.now().hour
    if 5 <= hour < 12:
        return "Good morning"
    elif 12 <= hour < 17:
        return "Good afternoon"
    elif 17 <= hour < 22:
        return "Good evening"
    else:
        return "Good night"


def format_display_date(date_str: str, include_time: bool = True) -> str:
    """Convert ISO date string into editorial display format like '14 Nov 2026'."""
    if not date_str:
        return "-"
    try:
        # Handles 'YYYY-MM-DD HH:MM:SS' or 'YYYY-MM-DDTHH:MM:SS' or 'YYYY-MM-DD'
        cleaned = date_str.replace("T", " ")
        if " " in cleaned:
            dt = datetime.strptime(cleaned.split(".")[0], "%Y-%m-%d %H:%M:%S")
        else:
            dt = datetime.strptime(cleaned, "%Y-%m-%d")

        if include_time:
            return dt.strftime("%d %b %Y, %H:%M")
        return dt.strftime("%d %b %Y")
    except Exception:
        return str(date_str)


def format_delta_bmi(current_bmi: float, previous_bmi: Optional[float]) -> str:
    """Format the change between consecutive BMI readings with explicit signs."""
    if previous_bmi is None:
        return "—"
    delta = current_bmi - previous_bmi
    if abs(delta) < 0.005:
        return "0.00 (stable)"
    sign = "+" if delta > 0 else ""
    return f"{sign}{delta:.2f}"


def format_file_size(num_bytes: int) -> str:
    """Format raw byte counts into human-readable strings."""
    for unit in ["B", "KB", "MB", "GB"]:
        if abs(num_bytes) < 1024.0:
            return f"{num_bytes:3.1f} {unit}"
        num_bytes /= 1024.0
    return f"{num_bytes:.1f} TB"


def center_window(window, width: int, height: int):
    """Center a Tkinter window or dialog on the primary monitor."""
    window.update_idletasks()
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()
    x = max(0, (screen_width - width) // 2)
    y = max(0, (screen_height - height) // 2)
    window.geometry(f"{width}x{height}+{x}+{y}")
