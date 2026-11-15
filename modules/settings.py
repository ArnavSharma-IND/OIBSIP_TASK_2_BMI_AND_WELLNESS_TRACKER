"""
Settings & System Administration Module
Handles theme preferences, SQLite database location & file metrics,
verified backup & disaster recovery, unit standards, and privacy disclosure.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from pathlib import Path
from typing import Dict, Any

from themes.manager import theme_mgr
from config import DB_PATH, APP_NAME, APP_VERSION, APP_AUTHOR, load_settings, save_settings
from services.backup_service import backup_service
from services.app_state import app_state
from utils.helpers import format_file_size
from utils.logger import logger
from bmi_calculator import DISCLAIMER_TEXT


class SettingsView(tk.Frame):
    """Settings view with theme controls, database backup/restore, and system metrics."""

    def __init__(self, parent: tk.Widget):
        super().__init__(parent, bg=theme_mgr.get("bg"))

        self._build_ui()
        self.refresh_database_info()

        # Observers
        theme_mgr.subscribe(self._on_theme_changed)

    def _build_ui(self) -> None:
        """Construct settings sections with open canvas layout."""
        t = theme_mgr.theme

        self.canvas = tk.Canvas(self, bg=t["bg"], highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self, orient=tk.VERTICAL, command=self.canvas.yview)
        self.scroll_content = tk.Frame(self.canvas, bg=t["bg"])

        self.scroll_content.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")),
        )
        self.window_id = self.canvas.create_window((0, 0), window=self.scroll_content, anchor="nw")

        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.canvas.bind(
            "<Configure>",
            lambda e: self.canvas.itemconfig(self.window_id, width=e.width),
        )

        self.bind_all("<MouseWheel>", self._on_mousewheel)

        self._build_content()

    def _on_mousewheel(self, event):
        try:
            if self.winfo_ismapped():
                self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        except Exception:
            pass

    def _build_content(self) -> None:
        """Populate scrolling settings items."""
        for child in self.scroll_content.winfo_children():
            child.destroy()

        t = theme_mgr.theme
        pad_frame = tk.Frame(self.scroll_content, bg=t["bg"], padx=48, pady=36)
        pad_frame.pack(fill=tk.BOTH, expand=True)

        # -------------------------------------------------------------
        # Header: Title
        # -------------------------------------------------------------
        header_row = tk.Frame(pad_frame, bg=t["bg"])
        header_row.pack(fill=tk.X, pady=(0, 20))

        title_sub = tk.Frame(header_row, bg=t["bg"])
        title_sub.pack(side=tk.LEFT)

        tk.Label(
            title_sub,
            text="PREFERENCES & SYSTEM",
            font=theme_mgr.font_caption,
            fg=t["accent"],
            bg=t["bg"],
            anchor="w",
        ).pack(anchor="w")

        tk.Label(
            title_sub,
            text="Application Settings",
            font=theme_mgr.font_title,
            fg=t["text_primary"],
            bg=t["bg"],
            anchor="w",
        ).pack(anchor="w", pady=(2, 0))

        # Divider
        tk.Frame(pad_frame, height=1, bg=t["border"]).pack(fill=tk.X, pady=(0, 28))

        # -------------------------------------------------------------
        # Section 1: Appearance & Theme
        # -------------------------------------------------------------
        sec_theme = tk.Frame(pad_frame, bg=t["bg"])
        sec_theme.pack(fill=tk.X, pady=(0, 32))

        tk.Label(
            sec_theme,
            text="Visual Appearance & Theme",
            font=theme_mgr.font_subtitle,
            fg=t["text_primary"],
            bg=t["bg"],
            anchor="w",
        ).pack(anchor="w")

        tk.Label(
            sec_theme,
            text="Choose between the warm Scandinavian beige theme and the restrained violet dark theme.",
            font=theme_mgr.font_small,
            fg=t["text_secondary"],
            bg=t["bg"],
            anchor="w",
        ).pack(anchor="w", pady=(2, 12))

        theme_btn_row = tk.Frame(sec_theme, bg=t["bg"])
        theme_btn_row.pack(fill=tk.X)

        is_dark = theme_mgr.is_dark

        self.btn_light = tk.Button(
            theme_btn_row,
            text="● Light Mode (Beige & Burnt Orange)",
            command=lambda: self._set_theme("light"),
            font=theme_mgr.font_body_bold if not is_dark else theme_mgr.font_body,
            bg=t["accent"] if not is_dark else t["surface_secondary"],
            fg=t["text_on_accent"] if not is_dark else t["text_primary"],
            relief=tk.FLAT,
            bd=0,
            padx=16,
            pady=9,
            cursor="hand2",
        )
        self.btn_light.pack(side=tk.LEFT, padx=(0, 12))

        self.btn_dark = tk.Button(
            theme_btn_row,
            text="● Dark Mode (Black & Soft Violet)",
            command=lambda: self._set_theme("dark"),
            font=theme_mgr.font_body_bold if is_dark else theme_mgr.font_body,
            bg=t["accent"] if is_dark else t["surface_secondary"],
            fg=t["text_on_accent"] if is_dark else t["text_primary"],
            relief=tk.FLAT,
            bd=0,
            padx=16,
            pady=9,
            cursor="hand2",
        )
        self.btn_dark.pack(side=tk.LEFT)

        # -------------------------------------------------------------
        # Section 2: Database Management, Backup & Disaster Recovery
        # -------------------------------------------------------------
        sec_db = tk.Frame(pad_frame, bg=t["bg"])
        sec_db.pack(fill=tk.X, pady=(0, 32))

        tk.Label(
            sec_db,
            text="Database & Disaster Recovery",
            font=theme_mgr.font_subtitle,
            fg=t["text_primary"],
            bg=t["bg"],
            anchor="w",
        ).pack(anchor="w")

        tk.Label(
            sec_db,
            text="Your data is permanently stored in an offline SQLite database file on your local disk.",
            font=theme_mgr.font_small,
            fg=t["text_secondary"],
            bg=t["bg"],
            anchor="w",
        ).pack(anchor="w", pady=(2, 12))

        # DB Info Card
        db_info_box = tk.Frame(
            sec_db,
            bg=t["surface"],
            highlightbackground=t["border"],
            highlightthickness=1,
            padx=16,
            pady=14,
        )
        db_info_box.pack(fill=tk.X, pady=(0, 16))

        self.lbl_db_path = tk.Label(
            db_info_box,
            text=f"Location:  {DB_PATH}",
            font=theme_mgr.font_small,
            fg=t["text_primary"],
            bg=t["surface"],
            anchor="w",
        )
        self.lbl_db_path.pack(anchor="w", pady=(0, 4))

        self.lbl_db_size = tk.Label(
            db_info_box,
            text="File Size:  Checking...",
            font=theme_mgr.font_small,
            fg=t["text_secondary"],
            bg=t["surface"],
            anchor="w",
        )
        self.lbl_db_size.pack(anchor="w")

        # Backup & Restore Action Buttons
        db_actions = tk.Frame(sec_db, bg=t["bg"])
        db_actions.pack(fill=tk.X)

        self.btn_backup = tk.Button(
            db_actions,
            text="Create Safe Backup",
            command=self._on_backup,
            font=theme_mgr.font_body_bold,
            bg=t["accent"],
            fg=t["text_on_accent"],
            activebackground=t["accent_hover"],
            activeforeground=t["text_on_accent"],
            relief=tk.FLAT,
            bd=0,
            padx=16,
            pady=9,
            cursor="hand2",
        )
        self.btn_backup.pack(side=tk.LEFT, padx=(0, 12))

        self.btn_restore = tk.Button(
            db_actions,
            text="Restore from Backup...",
            command=self._on_restore,
            font=theme_mgr.font_body,
            bg=t["surface_secondary"],
            fg=t["text_primary"],
            activebackground=t["surface_active"],
            activeforeground=t["text_primary"],
            relief=tk.FLAT,
            bd=0,
            padx=16,
            pady=9,
            cursor="hand2",
        )
        self.btn_restore.pack(side=tk.LEFT)

        # -------------------------------------------------------------
        # Section 3: Metric Standard & Units Reference
        # -------------------------------------------------------------
        sec_units = tk.Frame(pad_frame, bg=t["bg"])
        sec_units.pack(fill=tk.X, pady=(0, 32))

        tk.Label(
            sec_units,
            text="Measurement Standards",
            font=theme_mgr.font_subtitle,
            fg=t["text_primary"],
            bg=t["bg"],
            anchor="w",
        ).pack(anchor="w")

        tk.Label(
            sec_units,
            text=(
                "• Weight: Kilograms (kg)\n"
                "• Height: Metres (m)\n"
                "• Calculation Formula: BMI = Weight (kg) / [Height (m)]²\n"
                "• WHO Classification: Underweight (< 18.5) • Normal (18.5–24.9) • Overweight (25.0–29.9) • Obese (≥ 30.0)"
            ),
            font=theme_mgr.font_body,
            fg=t["text_secondary"],
            bg=t["bg"],
            justify=tk.LEFT,
        ).pack(anchor="w", pady=(6, 0))

        # -------------------------------------------------------------
        # Section 4: Privacy & Health Disclaimer
        # -------------------------------------------------------------
        sec_privacy = tk.Frame(pad_frame, bg=t["bg"])
        sec_privacy.pack(fill=tk.X, pady=(0, 10))

        tk.Label(
            sec_privacy,
            text="Privacy & Health Notice",
            font=theme_mgr.font_subtitle,
            fg=t["text_primary"],
            bg=t["bg"],
            anchor="w",
        ).pack(anchor="w")

        tk.Label(
            sec_privacy,
            text=(
                f"• {DISCLAIMER_TEXT}\n"
                "• 100% Offline-First: No metrics or personal details are ever uploaded to cloud servers or external networks.\n"
                f"• Application: {APP_NAME} v{APP_VERSION} • Built by {APP_AUTHOR}"
            ),
            font=theme_mgr.font_small,
            fg=t["text_muted"],
            bg=t["bg"],
            justify=tk.LEFT,
        ).pack(anchor="w", pady=(6, 0))

    def refresh_database_info(self) -> None:
        """Update database path and size labels."""
        if hasattr(self, "lbl_db_size"):
            if DB_PATH.exists():
                size_str = format_file_size(DB_PATH.stat().st_size)
                self.lbl_db_size.config(text=f"File Size:  {size_str} • Verified SQLite database")
            else:
                self.lbl_db_size.config(text="File Size:  Database not yet created on disk")

    def _set_theme(self, theme_name: str) -> None:
        """Switch theme and re-render."""
        theme_mgr.set_theme(theme_name)

    def _on_backup(self) -> None:
        """Perform database backup."""
        default_name = f"bmi_records_backup.sqlite"
        target = filedialog.asksaveasfilename(
            title="Save Database Backup",
            initialfile=default_name,
            defaultextension=".sqlite",
            filetypes=[("SQLite Database", "*.sqlite;*.db;*.bak"), ("All Files", "*.*")],
        )

        if not target:
            return

        res = backup_service.create_backup(target_path=Path(target))
        if res["success"]:
            messagebox.showinfo(
                "Backup Succeeded",
                f"Database successfully backed up to:\n{res['backup_path']}",
            )
        else:
            messagebox.showerror("Backup Failed", res.get("error", "Unknown error."))

    def _on_restore(self) -> None:
        """Restore database from chosen file after validation and user confirmation."""
        file_path = filedialog.askopenfilename(
            title="Select Backup to Restore",
            filetypes=[("SQLite Database", "*.sqlite;*.db;*.bak"), ("All Files", "*.*")],
        )

        if not file_path:
            return

        backup_p = Path(file_path)

        # Validate file
        is_valid, msg = backup_service.validate_backup_file(backup_p)
        if not is_valid:
            messagebox.showerror("Invalid Backup File", f"Cannot restore: {msg}")
            return

        confirm = messagebox.askyesno(
            "Confirm Database Restoration",
            "Are you sure you want to restore this database?\n\n"
            "• Current records will be replaced by the contents of the backup file.\n"
            "• A temporary safeguard copy of your current database will be saved.\n\n"
            "Proceed with restoration?",
            icon=messagebox.WARNING,
        )

        if confirm:
            res = backup_service.restore_backup(backup_p)
            if res["success"]:
                app_state.notify_data_modified()
                self.refresh_database_info()
                messagebox.showinfo(
                    "Restoration Complete",
                    "Database successfully restored! All records have been reloaded.",
                )
            else:
                messagebox.showerror("Restoration Failed", res.get("error", "Unknown error."))

    def _on_theme_changed(self, theme: Dict[str, Any]) -> None:
        """Re-render settings on theme switch."""
        self.config(bg=theme["bg"])
        self.canvas.config(bg=theme["bg"])
        self.scroll_content.config(bg=theme["bg"])
        self._build_content()
        self.refresh_database_info()
