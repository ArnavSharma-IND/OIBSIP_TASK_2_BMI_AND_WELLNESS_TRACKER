"""
History Management Module
Dedicated measurement log table with date-range filtering, chronological sorting,
record deletion with confirmation, and CSV spreadsheet export.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

from themes.manager import theme_mgr
from services.app_state import app_state
from services.database_service import db_service
from services.export_service import export_service
from utils.helpers import format_display_date
from utils.logger import logger


class HistoryView(tk.Frame):
    """Clean historical records view with filters, actions, and tabular presentation."""

    def __init__(self, parent: tk.Widget):
        super().__init__(parent, bg=theme_mgr.get("bg"))

        self._filter_preset = "All"
        self._sort_order = "DESC"
        self._current_records: List[Dict[str, Any]] = []

        self._build_ui()
        self.load_records()

        # Observers
        theme_mgr.subscribe(self._on_theme_changed)
        app_state.subscribe_user_changed(self._on_user_changed)
        app_state.subscribe_data_modified(self.load_records)

    def _build_ui(self) -> None:
        """Construct the layout with header, filter bar, table, and action controls."""
        t = theme_mgr.theme

        self.container = tk.Frame(self, bg=t["bg"])
        self.container.pack(fill=tk.BOTH, expand=True, padx=48, pady=36)

        # -------------------------------------------------------------
        # Header: Title & Eyebrow
        # -------------------------------------------------------------
        header_row = tk.Frame(self.container, bg=t["bg"])
        header_row.pack(fill=tk.X, pady=(0, 20))

        title_subframe = tk.Frame(header_row, bg=t["bg"])
        title_subframe.pack(side=tk.LEFT)

        self.lbl_eyebrow = tk.Label(
            title_subframe,
            text="RECORD ARCHIVE",
            font=theme_mgr.font_caption,
            fg=t["accent"],
            bg=t["bg"],
            anchor="w",
        )
        self.lbl_eyebrow.pack(anchor="w")

        self.lbl_title = tk.Label(
            title_subframe,
            text="Measurement History",
            font=theme_mgr.font_title,
            fg=t["text_primary"],
            bg=t["bg"],
            anchor="w",
        )
        self.lbl_title.pack(anchor="w", pady=(2, 0))

        # Top Actions: Export to CSV & Refresh
        top_actions = tk.Frame(header_row, bg=t["bg"])
        top_actions.pack(side=tk.RIGHT, anchor="center")

        self.btn_export = tk.Button(
            top_actions,
            text="Export to CSV",
            command=self._on_export_csv,
            font=theme_mgr.font_body_bold,
            bg=t["accent"],
            fg=t["text_on_accent"],
            activebackground=t["accent_hover"],
            activeforeground=t["text_on_accent"],
            relief=tk.FLAT,
            bd=0,
            padx=16,
            pady=8,
            cursor="hand2",
        )
        self.btn_export.pack(side=tk.LEFT, padx=(0, 10))

        self.btn_refresh = tk.Button(
            top_actions,
            text="Refresh",
            command=self.load_records,
            font=theme_mgr.font_body,
            bg=t["surface_secondary"],
            fg=t["text_primary"],
            activebackground=t["surface_active"],
            activeforeground=t["text_primary"],
            relief=tk.FLAT,
            bd=0,
            padx=14,
            pady=8,
            cursor="hand2",
        )
        self.btn_refresh.pack(side=tk.LEFT)

        # Divider
        self.sep = tk.Frame(self.container, height=1, bg=t["border"])
        self.sep.pack(fill=tk.X, pady=(0, 20))

        # -------------------------------------------------------------
        # Filter & Sort Bar (Clean, open layout)
        # -------------------------------------------------------------
        filter_bar = tk.Frame(self.container, bg=t["bg"])
        filter_bar.pack(fill=tk.X, pady=(0, 16))

        # Date Range Preset Buttons
        self.lbl_filter_tag = tk.Label(
            filter_bar,
            text="TIMEFRAME:",
            font=theme_mgr.font_caption,
            fg=t["text_secondary"],
            bg=t["bg"],
        )
        self.lbl_filter_tag.pack(side=tk.LEFT, padx=(0, 12))

        self.preset_buttons: Dict[str, tk.Button] = {}
        for preset in ["All", "Last 30 Days", "Last 90 Days", "This Year"]:
            btn = tk.Button(
                filter_bar,
                text=preset,
                command=lambda p=preset: self._on_preset_click(p),
                font=theme_mgr.font_small,
                bg=t["accent"] if preset == self._filter_preset else t["surface_secondary"],
                fg=t["text_on_accent"] if preset == self._filter_preset else t["text_primary"],
                relief=tk.FLAT,
                bd=0,
                padx=10,
                pady=4,
                cursor="hand2",
            )
            btn.pack(side=tk.LEFT, padx=(0, 6))
            self.preset_buttons[preset] = btn

        # Sort Order Selector (Right aligned)
        sort_frame = tk.Frame(filter_bar, bg=t["bg"])
        sort_frame.pack(side=tk.RIGHT)

        tk.Label(
            sort_frame,
            text="SORT:",
            font=theme_mgr.font_caption,
            fg=t["text_secondary"],
            bg=t["bg"],
        ).pack(side=tk.LEFT, padx=(0, 8))

        self.btn_sort = tk.Button(
            sort_frame,
            text="Newest First  ▼",
            command=self._on_toggle_sort,
            font=theme_mgr.font_small,
            bg=t["surface_secondary"],
            fg=t["text_primary"],
            relief=tk.FLAT,
            bd=0,
            padx=10,
            pady=4,
            cursor="hand2",
        )
        self.btn_sort.pack(side=tk.LEFT)

        # -------------------------------------------------------------
        # Table Container (ttk.Treeview styled to theme)
        # -------------------------------------------------------------
        table_container = tk.Frame(self.container, bg=t["surface"], highlightbackground=t["border"], highlightthickness=1)
        table_container.pack(fill=tk.BOTH, expand=True, pady=(0, 16))

        columns = ("date", "weight", "height", "bmi", "category", "actions")
        self.tree = ttk.Treeview(
            table_container,
            columns=columns,
            show="headings",
            selectmode="browse",
        )

        # Configure Headings & Columns
        self.tree.heading("date", text="DATE & TIME", anchor="w")
        self.tree.heading("weight", text="WEIGHT (KG)", anchor="w")
        self.tree.heading("height", text="HEIGHT (M)", anchor="w")
        self.tree.heading("bmi", text="BMI INDEX", anchor="w")
        self.tree.heading("category", text="CLASSIFICATION", anchor="w")
        self.tree.heading("actions", text="RECORD ID", anchor="e")

        self.tree.column("date", width=220, anchor="w")
        self.tree.column("weight", width=130, anchor="w")
        self.tree.column("height", width=120, anchor="w")
        self.tree.column("bmi", width=130, anchor="w")
        self.tree.column("category", width=180, anchor="w")
        self.tree.column("actions", width=100, anchor="e")

        # Scrollbar
        scroll = ttk.Scrollbar(table_container, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)

        # -------------------------------------------------------------
        # Bottom Controls: Record Deletion & Summary Count
        # -------------------------------------------------------------
        bottom_bar = tk.Frame(self.container, bg=t["bg"])
        bottom_bar.pack(fill=tk.X)

        self.lbl_record_count = tk.Label(
            bottom_bar,
            text="0 records found",
            font=theme_mgr.font_small,
            fg=t["text_secondary"],
            bg=t["bg"],
        )
        self.lbl_record_count.pack(side=tk.LEFT)

        self.btn_delete = tk.Button(
            bottom_bar,
            text="Delete Selected Record",
            command=self._on_delete_selected,
            font=theme_mgr.font_small,
            bg=t["surface_secondary"],
            fg="#C94A4A",
            activebackground=t["surface_active"],
            activeforeground="#C94A4A",
            relief=tk.FLAT,
            bd=0,
            padx=14,
            pady=6,
            cursor="hand2",
        )
        self.btn_delete.pack(side=tk.RIGHT)

    def load_records(self) -> None:
        """Fetch and populate historical records based on active timeframe and sort order."""
        # Clear existing rows
        for item in self.tree.get_children():
            self.tree.delete(item)

        user_id = app_state.active_user_id
        if not user_id:
            self.lbl_record_count.config(text="No active user selected.")
            return

        # Determine date filter
        start_date = None
        end_date = None
        now = datetime.now()

        if self._filter_preset == "Last 30 Days":
            start_date = (now - timedelta(days=30)).strftime("%Y-%m-%d")
        elif self._filter_preset == "Last 90 Days":
            start_date = (now - timedelta(days=90)).strftime("%Y-%m-%d")
        elif self._filter_preset == "This Year":
            start_date = f"{now.year}-01-01"

        records = db_service.get_records_by_user(
            user_id=user_id,
            start_date=start_date,
            end_date=end_date,
            order=self._sort_order,
        )
        self._current_records = records

        # Populate rows
        for r in records:
            display_date = format_display_date(r["recorded_at"], include_time=True)
            self.tree.insert(
                "",
                tk.END,
                iid=str(r["record_id"]),
                values=(
                    display_date,
                    f"{r['weight']:.2f} kg",
                    f"{r['height']:.2f} m",
                    f"{r['bmi']:.2f}",
                    r["category"],
                    f"#{r['record_id']}",
                ),
            )

        count_text = f"Showing {len(records)} measurement{'s' if len(records) != 1 else ''}"
        if self._filter_preset != "All":
            count_text += f" ({self._filter_preset})"
        self.lbl_record_count.config(text=count_text)

    def _on_preset_click(self, preset: str) -> None:
        """Switch timeframe preset and refresh."""
        self._filter_preset = preset
        t = theme_mgr.theme

        for name, btn in self.preset_buttons.items():
            if name == preset:
                btn.config(bg=t["accent"], fg=t["text_on_accent"])
            else:
                btn.config(bg=t["surface_secondary"], fg=t["text_primary"])

        self.load_records()

    def _on_toggle_sort(self) -> None:
        """Toggle sorting order between Newest First and Oldest First."""
        if self._sort_order == "DESC":
            self._sort_order = "ASC"
            self.btn_sort.config(text="Oldest First  ▲")
        else:
            self._sort_order = "DESC"
            self.btn_sort.config(text="Newest First  ▼")

        self.load_records()

    def _on_delete_selected(self) -> None:
        """Delete currently highlighted record after user confirmation."""
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo("Select Record", "Please click on a record in the table to select it for deletion.")
            return

        record_id = int(selected[0])
        rec = db_service.get_record_by_id(record_id)
        if not rec:
            return

        rec_date = format_display_date(rec["recorded_at"], include_time=True)
        confirm = messagebox.askyesno(
            "Confirm Deletion",
            f"Are you sure you want to delete this measurement?\n\n"
            f"Date: {rec_date}\n"
            f"BMI: {rec['bmi']:.2f} ({rec['category']})\n\n"
            "This action cannot be undone.",
            icon=messagebox.WARNING,
        )

        if confirm:
            success = db_service.delete_record(record_id)
            if success:
                app_state.notify_data_modified()
                logger.info(f"Deleted record #{record_id}")
            else:
                messagebox.showerror("Error", "Could not delete the selected record.")

    def _on_export_csv(self) -> None:
        """Prompt user for target file location and export records."""
        user = app_state.active_user
        if not user:
            messagebox.showwarning("Export Warning", "No active profile selected.")
            return

        user_id = user["user_id"]
        username = user["username"]

        # Suggest default filename
        clean_name = "".join(c for c in username if c.isalnum() or c in ("-", "_")).replace(" ", "_")
        default_file = f"bmi_records_{clean_name}_{datetime.now().strftime('%Y%m%d')}.csv"

        target_file = filedialog.asksaveasfilename(
            title="Export Records to CSV",
            initialfile=default_file,
            defaultextension=".csv",
            filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")],
        )

        if not target_file:
            return

        res = export_service.export_user_history_to_csv(user_id=user_id, target_path=target_file)
        if res["success"]:
            messagebox.showinfo(
                "Export Complete",
                f"Successfully exported {res['rows_exported']} records to:\n{res['file_path']}",
            )
        else:
            messagebox.showerror("Export Error", res.get("error", "Unknown error during export."))

    def _on_user_changed(self, user: Dict[str, Any]) -> None:
        """Reload records when active user changes."""
        self.load_records()

    def _on_theme_changed(self, theme: Dict[str, Any]) -> None:
        """Update colors on theme switch."""
        self.config(bg=theme["bg"])
        self.container.config(bg=theme["bg"])
        self.lbl_eyebrow.config(fg=theme["accent"], bg=theme["bg"])
        self.lbl_title.config(fg=theme["text_primary"], bg=theme["bg"])
        self.sep.config(bg=theme["border"])
        self.btn_export.config(
            bg=theme["accent"],
            fg=theme["text_on_accent"],
            activebackground=theme["accent_hover"],
            activeforeground=theme["text_on_accent"],
        )
        self.btn_refresh.config(
            bg=theme["surface_secondary"],
            fg=theme["text_primary"],
            activebackground=theme["surface_active"],
            activeforeground=theme["text_primary"],
        )
        self.lbl_filter_tag.config(fg=theme["text_secondary"], bg=theme["bg"])
        self.lbl_record_count.config(fg=theme["text_secondary"], bg=theme["bg"])
        self.btn_sort.config(bg=theme["surface_secondary"], fg=theme["text_primary"])
        self.btn_delete.config(bg=theme["surface_secondary"])

        # Re-color preset buttons
        for name, btn in self.preset_buttons.items():
            if name == self._filter_preset:
                btn.config(bg=theme["accent"], fg=theme["text_on_accent"])
            else:
                btn.config(bg=theme["surface_secondary"], fg=theme["text_primary"])

        self.load_records()
