"""
Dashboard / Overview Module
Presents a typography-first editorial wellness summary: floating hero metrics,
delta tracking, contextual screening insights, recent log rows, and an unboxed trend preview.
"""

import tkinter as tk
from tkinter import ttk
from typing import Dict, Any, List, Optional
from datetime import datetime

import matplotlib
matplotlib.use("TkAgg")
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.dates as mdates

from themes.manager import theme_mgr
from services.app_state import app_state
from services.database_service import db_service
from services.bmi_service import bmi_service
from utils.helpers import get_time_greeting, format_display_date, format_delta_bmi
from utils.logger import logger


class DashboardView(tk.Frame):
    """Typography-led overview dashboard following open-canvas floating design principles."""

    def __init__(self, parent: tk.Widget):
        super().__init__(parent, bg=theme_mgr.get("bg"))

        # Canvas & Scrollbar for smooth vertical layout
        self._build_scrolling_canvas()

        # Initial data render
        self.refresh_data()

        # Observers
        theme_mgr.subscribe(self._on_theme_changed)
        app_state.subscribe_user_changed(self._on_user_changed)
        app_state.subscribe_data_modified(self.refresh_data)

    def _build_scrolling_canvas(self) -> None:
        """Create a smooth scrolling container for flexible desktop window heights."""
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

        # Ensure content matches canvas width on resize
        self.canvas.bind(
            "<Configure>",
            lambda e: self.canvas.itemconfig(self.window_id, width=e.width),
        )

        # Mousewheel binding
        self.bind_all("<MouseWheel>", self._on_mousewheel)

    def _on_mousewheel(self, event):
        """Scroll canvas on mouse wheel if content overflows."""
        try:
            if self.winfo_ismapped():
                self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        except Exception:
            pass

    def refresh_data(self) -> None:
        """Fetch latest user measurements and rebuild the dashboard content."""
        for child in self.scroll_content.winfo_children():
            child.destroy()

        t = theme_mgr.theme
        user_id = app_state.active_user_id

        # Outer padding frame
        pad_frame = tk.Frame(self.scroll_content, bg=t["bg"], padx=48, pady=36)
        pad_frame.pack(fill=tk.BOTH, expand=True)

        # -------------------------------------------------------------
        # 1. Header: Greeting & Active User Context
        # -------------------------------------------------------------
        header_row = tk.Frame(pad_frame, bg=t["bg"])
        header_row.pack(fill=tk.X, pady=(0, 20))

        greeting = f"{get_time_greeting()}, {app_state.active_username}"
        tk.Label(
            header_row,
            text=greeting,
            font=theme_mgr.font_title,
            fg=t["text_primary"],
            bg=t["bg"],
            anchor="w",
        ).pack(side=tk.LEFT)

        today_str = datetime.now().strftime("%A, %d %B %Y")
        tk.Label(
            header_row,
            text=today_str,
            font=theme_mgr.font_small,
            fg=t["text_secondary"],
            bg=t["bg"],
        ).pack(side=tk.RIGHT, anchor="s")

        # Hairline separator
        tk.Frame(pad_frame, height=1, bg=t["border"]).pack(fill=tk.X, pady=(0, 28))

        # Check if user has measurements
        records = db_service.get_records_by_user(user_id, order="DESC") if user_id else []

        if not records:
            self._render_onboarding_state(pad_frame)
            return

        latest = records[0]
        prev = records[1] if len(records) > 1 else None
        total_count = len(records)

        # -------------------------------------------------------------
        # 2. Hero Floating Metrics Row (No Card Boxes!)
        # -------------------------------------------------------------
        metrics_row = tk.Frame(pad_frame, bg=t["bg"])
        metrics_row.pack(fill=tk.X, pady=(0, 32))

        # Left: Big BMI Hero
        hero_left = tk.Frame(metrics_row, bg=t["bg"])
        hero_left.pack(side=tk.LEFT, padx=(0, 56))

        tk.Label(
            hero_left,
            text="LATEST BODY MASS INDEX",
            font=theme_mgr.font_caption,
            fg=t["text_secondary"],
            bg=t["bg"],
            anchor="w",
        ).pack(anchor="w")

        bmi_val_row = tk.Frame(hero_left, bg=t["bg"])
        bmi_val_row.pack(anchor="w", pady=(2, 4))

        tk.Label(
            bmi_val_row,
            text=f"{latest['bmi']:.2f}",
            font=theme_mgr.font_hero,
            fg=t["text_primary"],
            bg=t["bg"],
        ).pack(side=tk.LEFT)

        cat = latest["category"]
        cat_color = theme_mgr.get_category_color(cat)

        cat_badge = tk.Frame(bmi_val_row, bg=cat_color, padx=12, pady=4)
        cat_badge.pack(side=tk.LEFT, padx=(16, 0))
        tk.Label(
            cat_badge,
            text=cat.upper(),
            font=theme_mgr.font_caption,
            fg="#FFFFFF",
            bg=cat_color,
        ).pack()

        last_date = format_display_date(latest["recorded_at"], include_time=True)
        tk.Label(
            hero_left,
            text=f"Recorded on {last_date}",
            font=theme_mgr.font_small,
            fg=t["text_muted"],
            bg=t["bg"],
            anchor="w",
        ).pack(anchor="w")

        # Right: Floating Stat Columns
        stats_frame = tk.Frame(metrics_row, bg=t["bg"])
        stats_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Latest Weight
        stat1 = tk.Frame(stats_frame, bg=t["bg"])
        stat1.pack(side=tk.LEFT, padx=(0, 40))
        tk.Label(stat1, text="LATEST WEIGHT", font=theme_mgr.font_caption, fg=t["text_secondary"], bg=t["bg"]).pack(anchor="w")
        tk.Label(stat1, text=f"{latest['weight']:.1f} kg", font=theme_mgr.font_subtitle, fg=t["text_primary"], bg=t["bg"]).pack(anchor="w", pady=(4, 2))
        tk.Label(stat1, text=f"Height: {latest['height']:.2f} m", font=theme_mgr.font_small, fg=t["text_muted"], bg=t["bg"]).pack(anchor="w")

        # Previous Measurement & Delta
        stat2 = tk.Frame(stats_frame, bg=t["bg"])
        stat2.pack(side=tk.LEFT, padx=(0, 40))
        tk.Label(stat2, text="PREVIOUS BMI", font=theme_mgr.font_caption, fg=t["text_secondary"], bg=t["bg"]).pack(anchor="w")

        prev_text = f"{prev['bmi']:.2f}" if prev else "None recorded"
        tk.Label(stat2, text=prev_text, font=theme_mgr.font_subtitle, fg=t["text_primary"], bg=t["bg"]).pack(anchor="w", pady=(4, 2))

        delta_str = format_delta_bmi(latest["bmi"], prev["bmi"] if prev else None)
        delta_color = t["text_secondary"]
        if prev:
            delta_val = latest["bmi"] - prev["bmi"]
            if delta_val > 0.05:
                delta_color = t["accent"]
            elif delta_val < -0.05:
                delta_color = theme_mgr.get("category_normal")

        tk.Label(stat2, text=f"Change: {delta_str}", font=theme_mgr.font_small, fg=delta_color, bg=t["bg"]).pack(anchor="w")

        # Total Measurements
        stat3 = tk.Frame(stats_frame, bg=t["bg"])
        stat3.pack(side=tk.LEFT)
        tk.Label(stat3, text="TOTAL ENTRIES", font=theme_mgr.font_caption, fg=t["text_secondary"], bg=t["bg"]).pack(anchor="w")
        tk.Label(stat3, text=f"{total_count}", font=theme_mgr.font_subtitle, fg=t["text_primary"], bg=t["bg"]).pack(anchor="w", pady=(4, 2))
        tk.Label(stat3, text="Lifetime tracking", font=theme_mgr.font_small, fg=t["text_muted"], bg=t["bg"]).pack(anchor="w")

        # -------------------------------------------------------------
        # 3. Editorial Smart Insights Banner
        # -------------------------------------------------------------
        insights = bmi_service.generate_insights(user_id) if user_id else []
        if insights:
            insights_box = tk.Frame(
                pad_frame,
                bg=t["surface"],
                highlightbackground=t["border"],
                highlightthickness=1,
                padx=20,
                pady=16,
            )
            insights_box.pack(fill=tk.X, pady=(0, 32))

            tk.Label(
                insights_box,
                text="WELLNESS PERSPECTIVE",
                font=theme_mgr.font_caption,
                fg=t["accent"],
                bg=t["surface"],
                anchor="w",
            ).pack(anchor="w", pady=(0, 6))

            for insight in insights:
                tk.Label(
                    insights_box,
                    text=f"•  {insight}",
                    font=theme_mgr.font_body,
                    fg=t["text_primary"],
                    bg=t["surface"],
                    anchor="w",
                    justify=tk.LEFT,
                ).pack(anchor="w", pady=(1, 1))

        # -------------------------------------------------------------
        # 4. Two-Column Lower Canvas: Recent Measurements | Unboxed Chart
        # -------------------------------------------------------------
        lower_row = tk.Frame(pad_frame, bg=t["bg"])
        lower_row.pack(fill=tk.BOTH, expand=True)

        # Left Column: Recent Measurements
        recent_col = tk.Frame(lower_row, bg=t["bg"], width=420)
        recent_col.pack(side=tk.LEFT, fill=tk.BOTH, padx=(0, 36))

        recent_header = tk.Frame(recent_col, bg=t["bg"])
        recent_header.pack(fill=tk.X, pady=(0, 12))

        tk.Label(
            recent_header,
            text="Recent Measurements",
            font=theme_mgr.font_subtitle,
            fg=t["text_primary"],
            bg=t["bg"],
        ).pack(side=tk.LEFT)

        btn_view_history = tk.Label(
            recent_header,
            text="View all history →",
            font=theme_mgr.font_small,
            fg=t["accent"],
            bg=t["bg"],
            cursor="hand2",
        )
        btn_view_history.pack(side=tk.RIGHT)
        btn_view_history.bind("<Button-1>", lambda e: app_state.request_navigation("history"))

        # Render recent rows (up to 5 entries)
        recent_list = records[:5]
        for idx, rec in enumerate(recent_list):
            row_frame = tk.Frame(recent_col, bg=t["surface"] if idx % 2 == 0 else t["bg"], padx=12, pady=10)
            row_frame.pack(fill=tk.X)

            # Date
            tk.Label(
                row_frame,
                text=format_display_date(rec["recorded_at"], include_time=False),
                font=theme_mgr.font_body,
                fg=t["text_primary"],
                bg=row_frame["bg"],
                width=12,
                anchor="w",
            ).pack(side=tk.LEFT)

            # Weight
            tk.Label(
                row_frame,
                text=f"{rec['weight']:.1f} kg",
                font=theme_mgr.font_small,
                fg=t["text_secondary"],
                bg=row_frame["bg"],
                width=10,
                anchor="w",
            ).pack(side=tk.LEFT)

            # Category Pill
            rec_cat = rec["category"]
            rec_color = theme_mgr.get_category_color(rec_cat)
            c_tag = tk.Label(
                row_frame,
                text=rec_cat,
                font=theme_mgr.font_caption,
                fg=rec_color,
                bg=row_frame["bg"],
                anchor="w",
            )
            c_tag.pack(side=tk.LEFT, expand=True)

            # BMI Value
            tk.Label(
                row_frame,
                text=f"{rec['bmi']:.2f}",
                font=theme_mgr.font_body_bold,
                fg=t["text_primary"],
                bg=row_frame["bg"],
            ).pack(side=tk.RIGHT)

        # Right Column: Trend Preview Chart
        chart_col = tk.Frame(lower_row, bg=t["bg"])
        chart_col.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        chart_header = tk.Frame(chart_col, bg=t["bg"])
        chart_header.pack(fill=tk.X, pady=(0, 8))

        tk.Label(
            chart_header,
            text="BMI Trajectory",
            font=theme_mgr.font_subtitle,
            fg=t["text_primary"],
            bg=t["bg"],
        ).pack(side=tk.LEFT)

        btn_view_trends = tk.Label(
            chart_header,
            text="Full analytics →",
            font=theme_mgr.font_small,
            fg=t["accent"],
            bg=t["bg"],
            cursor="hand2",
        )
        btn_view_trends.pack(side=tk.RIGHT)
        btn_view_trends.bind("<Button-1>", lambda e: app_state.request_navigation("trends"))

        # Render unboxed mini chart
        self._render_mini_chart(chart_col, records)

    def _render_onboarding_state(self, parent: tk.Widget) -> None:
        """Friendly, warm empty state for brand new users."""
        t = theme_mgr.theme

        onboarding = tk.Frame(parent, bg=t["bg"], pady=40)
        onboarding.pack(fill=tk.BOTH, expand=True)

        tk.Label(
            onboarding,
            text="Begin Your Wellness Journey",
            font=theme_mgr.font_title,
            fg=t["text_primary"],
            bg=t["bg"],
            anchor="w",
        ).pack(anchor="w", pady=(0, 8))

        tk.Label(
            onboarding,
            text=(
                "No measurements have been recorded yet for this profile.\n"
                "Record your current height and weight to track Body Mass Index, "
                "observe directional changes over time, and gain personal health perspective."
            ),
            font=theme_mgr.font_body,
            fg=t["text_secondary"],
            bg=t["bg"],
            justify=tk.LEFT,
        ).pack(anchor="w", pady=(0, 24))

        btn_start = tk.Button(
            onboarding,
            text="Calculate Your First Measurement →",
            command=lambda: app_state.request_navigation("calculator"),
            font=theme_mgr.font_body_bold,
            bg=t["accent"],
            fg=t["text_on_accent"],
            activebackground=t["accent_hover"],
            activeforeground=t["text_on_accent"],
            relief=tk.FLAT,
            bd=0,
            padx=24,
            pady=12,
            cursor="hand2",
        )
        btn_start.pack(anchor="w")

    def _render_mini_chart(self, parent: tk.Widget, records: List[Dict[str, Any]]) -> None:
        """Render unboxed, theme-styled Matplotlib trend chart."""
        t = theme_mgr.theme

        # Reverse records to chronological order for plotting
        chrono = sorted(records, key=lambda r: r["recorded_at"])

        dates = []
        bmis = []
        for r in chrono:
            try:
                dt = datetime.strptime(r["recorded_at"].split(".")[0], "%Y-%m-%d %H:%M:%S")
            except Exception:
                dt = datetime.now()
            dates.append(dt)
            bmis.append(r["bmi"])

        # Create Matplotlib Figure
        fig = Figure(figsize=(5.5, 3.0), dpi=100, facecolor=t["chart_bg"])
        ax = fig.add_subplot(111)
        ax.set_facecolor(t["chart_plot_bg"])

        # Reference healthy band (18.5 - 24.9)
        ax.axhspan(18.5, 24.9, color=t["chart_normal_band"], alpha=0.5, label="Normal zone", zorder=1)

        # Plot BMI points & line
        if len(chrono) == 1:
            # Single measurement: plot distinct point
            ax.scatter(dates, bmis, color=t["chart_line"], s=70, zorder=4)
            ax.set_xlim(dates[0], dates[0])
        else:
            ax.plot(
                dates,
                bmis,
                color=t["chart_line"],
                linewidth=2.2,
                marker="o",
                markersize=6,
                markerfacecolor=t["chart_dot"],
                markeredgecolor=t["chart_line"],
                markeredgewidth=1.5,
                zorder=4,
            )

        # Style Spines & Grid
        for spine in ["top", "right"]:
            ax.spines[spine].set_visible(False)
        ax.spines["left"].set_color(t["chart_spine"])
        ax.spines["bottom"].set_color(t["chart_spine"])

        ax.grid(True, linestyle="--", alpha=0.6, color=t["chart_grid"])
        ax.tick_params(colors=t["chart_subtext"], labelsize=8)

        # Date formatting on X axis
        if len(dates) > 1:
            ax.xaxis.set_major_formatter(mdates.DateFormatter("%d %b"))
            fig.autofmt_xdate(rotation=20)

        # Set sensible Y limits around data with margin
        y_min = min(bmis) - 2.0
        y_max = max(bmis) + 2.0
        ax.set_ylim(max(10.0, y_min), min(45.0, y_max))

        fig.tight_layout()

        # Embed into Tkinter
        canvas_widget = FigureCanvasTkAgg(fig, master=parent)
        canvas_widget.draw()
        canvas_widget.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def _on_user_changed(self, user: Dict[str, Any]) -> None:
        """Re-render dashboard when user profile switches."""
        self.refresh_data()

    def _on_theme_changed(self, theme: Dict[str, Any]) -> None:
        """Re-render entire dashboard on theme toggle."""
        self.config(bg=theme["bg"])
        self.canvas.config(bg=theme["bg"])
        self.scroll_content.config(bg=theme["bg"])
        self.refresh_data()
