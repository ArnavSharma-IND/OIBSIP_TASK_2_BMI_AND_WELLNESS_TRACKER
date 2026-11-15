"""
BMI Trend Analytics & Visualisation Module
Integrates Matplotlib directly into Tkinter with unboxed editorial aesthetics,
date-range filtering, summary analytics, and live database synchronization.
"""

import tkinter as tk
from tkinter import ttk
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

import matplotlib
matplotlib.use("TkAgg")
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.dates as mdates

from themes.manager import theme_mgr
from services.app_state import app_state
from services.database_service import db_service
from utils.helpers import format_display_date, format_delta_bmi
from utils.logger import logger


class TrendsView(tk.Frame):
    """Deep analytics screen with unboxed Matplotlib chart and summary statistics."""

    def __init__(self, parent: tk.Widget):
        super().__init__(parent, bg=theme_mgr.get("bg"))

        self._timeframe_filter = "All Time"
        self._canvas_widget: Optional[FigureCanvasTkAgg] = None

        self._build_ui()
        self.render_analytics()

        # Observers
        theme_mgr.subscribe(self._on_theme_changed)
        app_state.subscribe_user_changed(self._on_user_changed)
        app_state.subscribe_data_modified(self.render_analytics)

    def _build_ui(self) -> None:
        """Construct page layout with header, filter toolbar, statistics strip, and chart canvas."""
        t = theme_mgr.theme

        self.container = tk.Frame(self, bg=t["bg"])
        self.container.pack(fill=tk.BOTH, expand=True, padx=48, pady=36)

        # -------------------------------------------------------------
        # Header: Title & Timeframe Filters
        # -------------------------------------------------------------
        header_row = tk.Frame(self.container, bg=t["bg"])
        header_row.pack(fill=tk.X, pady=(0, 20))

        title_sub = tk.Frame(header_row, bg=t["bg"])
        title_sub.pack(side=tk.LEFT)

        self.lbl_eyebrow = tk.Label(
            title_sub,
            text="ANALYTICAL TRAJECTORY",
            font=theme_mgr.font_caption,
            fg=t["accent"],
            bg=t["bg"],
            anchor="w",
        )
        self.lbl_eyebrow.pack(anchor="w")

        self.lbl_title = tk.Label(
            title_sub,
            text="BMI Trends & Dynamics",
            font=theme_mgr.font_title,
            fg=t["text_primary"],
            bg=t["bg"],
            anchor="w",
        )
        self.lbl_title.pack(anchor="w", pady=(2, 0))

        # Timeframe Filter Buttons (Right Aligned)
        self.filter_frame = tk.Frame(header_row, bg=t["bg"])
        self.filter_frame.pack(side=tk.RIGHT, anchor="center")

        self.filter_buttons: Dict[str, tk.Button] = {}
        timeframes = ["1 Month", "3 Months", "6 Months", "1 Year", "All Time"]
        for tf in timeframes:
            btn = tk.Button(
                self.filter_frame,
                text=tf,
                command=lambda t_val=tf: self._on_filter_changed(t_val),
                font=theme_mgr.font_small,
                bg=t["accent"] if tf == self._timeframe_filter else t["surface_secondary"],
                fg=t["text_on_accent"] if tf == self._timeframe_filter else t["text_primary"],
                relief=tk.FLAT,
                bd=0,
                padx=12,
                pady=6,
                cursor="hand2",
            )
            btn.pack(side=tk.LEFT, padx=(0, 6))
            self.filter_buttons[tf] = btn

        # Divider
        self.sep = tk.Frame(self.container, height=1, bg=t["border"])
        self.sep.pack(fill=tk.X, pady=(0, 24))

        # -------------------------------------------------------------
        # Floating Statistics Strip (Clean open layout, no card grids)
        # -------------------------------------------------------------
        self.stats_row = tk.Frame(self.container, bg=t["bg"])
        self.stats_row.pack(fill=tk.X, pady=(0, 24))

        # -------------------------------------------------------------
        # Unboxed Chart Canvas Container
        # -------------------------------------------------------------
        self.chart_container = tk.Frame(self.container, bg=t["surface"], highlightbackground=t["border"], highlightthickness=1)
        self.chart_container.pack(fill=tk.BOTH, expand=True)

    def render_analytics(self) -> None:
        """Fetch records according to active timeframe and re-render stats and chart."""
        t = theme_mgr.theme
        user_id = app_state.active_user_id

        # Determine date bounds
        start_date = None
        now = datetime.now()
        if self._timeframe_filter == "1 Month":
            start_date = (now - timedelta(days=30)).strftime("%Y-%m-%d")
        elif self._timeframe_filter == "3 Months":
            start_date = (now - timedelta(days=90)).strftime("%Y-%m-%d")
        elif self._timeframe_filter == "6 Months":
            start_date = (now - timedelta(days=180)).strftime("%Y-%m-%d")
        elif self._timeframe_filter == "1 Year":
            start_date = (now - timedelta(days=365)).strftime("%Y-%m-%d")

        records = db_service.get_records_by_user(
            user_id=user_id,
            start_date=start_date,
            order="ASC",  # Chronological for visualization
        ) if user_id else []

        self._render_statistics_strip(records)
        self._render_matplotlib_chart(records)

    def _render_statistics_strip(self, records: List[Dict[str, Any]]) -> None:
        """Render floating summary metric values without card boxes."""
        for child in self.stats_row.winfo_children():
            child.destroy()

        t = theme_mgr.theme

        if not records:
            return

        bmis = [r["bmi"] for r in records]
        start_bmi = bmis[0]
        current_bmi = bmis[-1]
        min_bmi = min(bmis)
        max_bmi = max(bmis)
        avg_bmi = sum(bmis) / len(bmis)
        net_delta = current_bmi - start_bmi

        stat_items = [
            ("STARTING BMI", f"{start_bmi:.2f}", format_display_date(records[0]["recorded_at"], False)),
            ("CURRENT BMI", f"{current_bmi:.2f}", format_display_date(records[-1]["recorded_at"], False)),
            ("AVERAGE BMI", f"{avg_bmi:.2f}", f"Across {len(records)} measurements"),
            ("LOWEST RECORDED", f"{min_bmi:.2f}", "Period minimum"),
            ("HIGHEST RECORDED", f"{max_bmi:.2f}", "Period maximum"),
            ("NET CHANGE", f"{'+' if net_delta > 0 else ''}{net_delta:.2f}", "Since first entry"),
        ]

        for label, val_text, sub_text in stat_items:
            f = tk.Frame(self.stats_row, bg=t["bg"])
            f.pack(side=tk.LEFT, padx=(0, 36))

            tk.Label(f, text=label, font=theme_mgr.font_caption, fg=t["text_secondary"], bg=t["bg"]).pack(anchor="w")
            tk.Label(f, text=val_text, font=theme_mgr.font_subtitle, fg=t["text_primary"], bg=t["bg"]).pack(anchor="w", pady=(3, 1))
            tk.Label(f, text=sub_text, font=theme_mgr.font_small, fg=t["text_muted"], bg=t["bg"]).pack(anchor="w")

    def _render_matplotlib_chart(self, records: List[Dict[str, Any]]) -> None:
        """Construct the full-sized Matplotlib chart directly in the Tkinter canvas."""
        for child in self.chart_container.winfo_children():
            child.destroy()

        t = theme_mgr.theme

        if not records:
            # Informative empty state
            empty_frame = tk.Frame(self.chart_container, bg=t["surface"], pady=60)
            empty_frame.pack(fill=tk.BOTH, expand=True)

            tk.Label(
                empty_frame,
                text="No Measurement Records in this Timeframe",
                font=theme_mgr.font_subtitle,
                fg=t["text_primary"],
                bg=t["surface"],
            ).pack(pady=(0, 8))

            tk.Label(
                empty_frame,
                text="Calculate and save measurements to populate this trend graph with your actual personal data.",
                font=theme_mgr.font_body,
                fg=t["text_secondary"],
                bg=t["surface"],
            ).pack()
            return

        dates = []
        bmis = []
        weights = []
        for r in records:
            try:
                dt = datetime.strptime(r["recorded_at"].split(".")[0], "%Y-%m-%d %H:%M:%S")
            except Exception:
                dt = datetime.now()
            dates.append(dt)
            bmis.append(r["bmi"])
            weights.append(r["weight"])

        # Create Matplotlib Figure
        fig = Figure(figsize=(8.0, 4.2), dpi=100, facecolor=t["chart_bg"])
        ax = fig.add_subplot(111)
        ax.set_facecolor(t["chart_plot_bg"])

        # Reference Healthy Band
        ax.axhspan(18.5, 24.9, color=t["chart_normal_band"], alpha=0.5, label="Normal reference range (18.5–24.9)", zorder=1)

        # Plot data
        if len(records) == 1:
            # Single measurement point
            ax.scatter(dates, bmis, color=t["chart_line"], s=100, zorder=5, label=f"Measurement: {bmis[0]:.2f}")
            ax.annotate(
                f"{bmis[0]:.2f} ({records[0]['category']})",
                (dates[0], bmis[0]),
                textcoords="offset points",
                xytext=(0, 14),
                ha="center",
                fontsize=9,
                color=t["chart_text"],
                fontweight="bold",
            )
        else:
            ax.plot(
                dates,
                bmis,
                color=t["chart_line"],
                linewidth=2.5,
                marker="o",
                markersize=7,
                markerfacecolor=t["chart_dot"],
                markeredgecolor=t["chart_line"],
                markeredgewidth=2,
                label="Recorded BMI",
                zorder=4,
            )

            # Annotate latest point
            last_date, last_bmi = dates[-1], bmis[-1]
            ax.annotate(
                f"{last_bmi:.2f}",
                (last_date, last_bmi),
                textcoords="offset points",
                xytext=(0, 12),
                ha="center",
                fontsize=9,
                color=t["chart_text"],
                fontweight="bold",
            )

        # Spines & Grid
        for spine in ["top", "right"]:
            ax.spines[spine].set_visible(False)
        ax.spines["left"].set_color(t["chart_spine"])
        ax.spines["bottom"].set_color(t["chart_spine"])

        ax.grid(True, linestyle="--", alpha=0.5, color=t["chart_grid"])
        ax.tick_params(colors=t["chart_subtext"], labelsize=9)

        # X-Axis date format
        if len(dates) > 1:
            ax.xaxis.set_major_formatter(mdates.DateFormatter("%d %b %Y"))
            fig.autofmt_xdate(rotation=22)

        # Y-Axis Range & Labels
        y_min = min(bmis) - 2.5
        y_max = max(bmis) + 2.5
        ax.set_ylim(max(10.0, y_min), min(45.0, y_max))
        ax.set_ylabel("BMI (kg/m²)", fontsize=9, color=t["chart_subtext"], labelpad=8)

        # Legend
        leg = ax.legend(loc="upper left", frameon=False, fontsize=8)
        for text in leg.get_texts():
            text.set_color(t["chart_subtext"])

        fig.tight_layout()

        # Canvas Widget
        self._canvas_widget = FigureCanvasTkAgg(fig, master=self.chart_container)
        self._canvas_widget.draw()
        self._canvas_widget.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def _on_filter_changed(self, timeframe: str) -> None:
        """Handle timeframe selection."""
        self._timeframe_filter = timeframe
        t = theme_mgr.theme

        for name, btn in self.filter_buttons.items():
            if name == timeframe:
                btn.config(bg=t["accent"], fg=t["text_on_accent"])
            else:
                btn.config(bg=t["surface_secondary"], fg=t["text_primary"])

        self.render_analytics()

    def _on_user_changed(self, user: Dict[str, Any]) -> None:
        """Re-render when user switches."""
        self.render_analytics()

    def _on_theme_changed(self, theme: Dict[str, Any]) -> None:
        """Update colors and re-plot chart with new theme palette."""
        self.config(bg=theme["bg"])
        self.container.config(bg=theme["bg"])
        self.lbl_eyebrow.config(fg=theme["accent"], bg=theme["bg"])
        self.lbl_title.config(fg=theme["text_primary"], bg=theme["bg"])
        self.sep.config(bg=theme["border"])
        self.stats_row.config(bg=theme["bg"])
        self.chart_container.config(bg=theme["surface"], highlightbackground=theme["border"])

        for name, btn in self.filter_buttons.items():
            if name == self._timeframe_filter:
                btn.config(bg=theme["accent"], fg=theme["text_on_accent"])
            else:
                btn.config(bg=theme["surface_secondary"], fg=theme["text_primary"])

        self.render_analytics()
