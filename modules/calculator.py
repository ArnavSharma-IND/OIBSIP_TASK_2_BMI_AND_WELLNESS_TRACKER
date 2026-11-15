"""
BMI Calculator Module
Editorial-style calculation interface with real-time validation, floating numerical typography,
interactive classification scale, and direct persistence.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional, Dict, Any

from themes.manager import theme_mgr
from services.app_state import app_state
from services.bmi_service import bmi_service
from services.database_service import db_service
from utils.validators import ValidationError
from utils.logger import logger


class CalculatorView(tk.Frame):
    """Minimalist, typography-led BMI calculation screen."""

    def __init__(self, parent: tk.Widget):
        super().__init__(parent, bg=theme_mgr.get("bg"))
        self._current_result: Optional[Dict[str, Any]] = None

        # Build UI
        self._build_ui()

        # Subscribe to theme and app state updates
        theme_mgr.subscribe(self._on_theme_changed)
        app_state.subscribe_user_changed(self._on_user_changed)

    def _build_ui(self) -> None:
        """Construct the open-canvas layout with generous whitespace."""
        t = theme_mgr.theme

        # Outer scrollable canvas or padded frame
        self.container = tk.Frame(self, bg=t["bg"])
        self.container.pack(fill=tk.BOTH, expand=True, padx=48, pady=36)

        # -------------------------------------------------------------
        # Section Header: Editorial Title & Active Profile
        # -------------------------------------------------------------
        header_frame = tk.Frame(self.container, bg=t["bg"])
        header_frame.pack(fill=tk.X, pady=(0, 24))

        title_subframe = tk.Frame(header_frame, bg=t["bg"])
        title_subframe.pack(side=tk.LEFT)

        self.lbl_section_eyebrow = tk.Label(
            title_subframe,
            text="MEASUREMENT & SCREENING",
            font=theme_mgr.font_caption,
            fg=t["accent"],
            bg=t["bg"],
            anchor="w",
        )
        self.lbl_section_eyebrow.pack(anchor="w")

        self.lbl_section_title = tk.Label(
            title_subframe,
            text="BMI Calculator",
            font=theme_mgr.font_title,
            fg=t["text_primary"],
            bg=t["bg"],
            anchor="w",
        )
        self.lbl_section_title.pack(anchor="w", pady=(2, 0))

        # Active Profile Pill
        self.profile_pill = tk.Frame(header_frame, bg=t["surface_secondary"], padx=14, pady=6)
        self.profile_pill.pack(side=tk.RIGHT)

        self.lbl_profile_tag = tk.Label(
            self.profile_pill,
            text=f"Active Profile:  {app_state.active_username}",
            font=theme_mgr.font_small,
            fg=t["text_primary"],
            bg=t["surface_secondary"],
        )
        self.lbl_profile_tag.pack()

        # Hairline separator
        self.sep_header = tk.Frame(self.container, height=1, bg=t["border"])
        self.sep_header.pack(fill=tk.X, pady=(0, 28))

        # -------------------------------------------------------------
        # Two-Column Layout: Form Inputs (Left) | Visual Result (Right)
        # -------------------------------------------------------------
        self.content_row = tk.Frame(self.container, bg=t["bg"])
        self.content_row.pack(fill=tk.BOTH, expand=True)

        # Left: Clean Input Form
        self.form_col = tk.Frame(self.content_row, bg=t["bg"], width=380)
        self.form_col.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 48))

        self.lbl_form_heading = tk.Label(
            self.form_col,
            text="Enter Body Metrics",
            font=theme_mgr.font_subtitle,
            fg=t["text_primary"],
            bg=t["bg"],
            anchor="w",
        )
        self.lbl_form_heading.pack(fill=tk.X, pady=(0, 16))

        # Weight Input
        self.lbl_weight = tk.Label(
            self.form_col,
            text="BODY WEIGHT (KG)",
            font=theme_mgr.font_caption,
            fg=t["text_secondary"],
            bg=t["bg"],
            anchor="w",
        )
        self.lbl_weight.pack(fill=tk.X, pady=(0, 4))

        self.entry_weight_frame = tk.Frame(self.form_col, bg=t["surface"], highlightbackground=t["border"], highlightthickness=1)
        self.entry_weight_frame.pack(fill=tk.X, pady=(0, 16))

        self.entry_weight = tk.Entry(
            self.entry_weight_frame,
            font=theme_mgr.font_subtitle,
            bg=t["surface"],
            fg=t["text_primary"],
            insertbackground=t["accent"],
            relief=tk.FLAT,
            bd=8,
        )
        self.entry_weight.pack(fill=tk.X)
        self.entry_weight.bind("<Return>", lambda e: self._on_calculate())

        # Height Input
        self.lbl_height = tk.Label(
            self.form_col,
            text="HEIGHT (METRES)",
            font=theme_mgr.font_caption,
            fg=t["text_secondary"],
            bg=t["bg"],
            anchor="w",
        )
        self.lbl_height.pack(fill=tk.X, pady=(0, 4))

        self.entry_height_frame = tk.Frame(self.form_col, bg=t["surface"], highlightbackground=t["border"], highlightthickness=1)
        self.entry_height_frame.pack(fill=tk.X, pady=(0, 6))

        self.entry_height = tk.Entry(
            self.entry_height_frame,
            font=theme_mgr.font_subtitle,
            bg=t["surface"],
            fg=t["text_primary"],
            insertbackground=t["accent"],
            relief=tk.FLAT,
            bd=8,
        )
        self.entry_height.pack(fill=tk.X)
        self.entry_height.bind("<Return>", lambda e: self._on_calculate())

        self.lbl_height_hint = tk.Label(
            self.form_col,
            text="e.g. 1.75 for 175 cm • 1.82 for 182 cm",
            font=theme_mgr.font_small,
            fg=t["text_muted"],
            bg=t["bg"],
            anchor="w",
        )
        self.lbl_height_hint.pack(fill=tk.X, pady=(0, 24))

        # Floating Action Buttons
        btn_row = tk.Frame(self.form_col, bg=t["bg"])
        btn_row.pack(fill=tk.X, pady=(0, 14))

        self.btn_calculate = tk.Button(
            btn_row,
            text="Calculate BMI",
            command=self._on_calculate,
            font=theme_mgr.font_body_bold,
            bg=t["accent"],
            fg=t["text_on_accent"],
            activebackground=t["accent_hover"],
            activeforeground=t["text_on_accent"],
            relief=tk.FLAT,
            bd=0,
            padx=20,
            pady=10,
            cursor="hand2",
        )
        self.btn_calculate.pack(side=tk.LEFT, padx=(0, 12))

        self.btn_clear = tk.Button(
            btn_row,
            text="Clear",
            command=self._on_clear,
            font=theme_mgr.font_body,
            bg=t["surface_secondary"],
            fg=t["text_primary"],
            activebackground=t["surface_active"],
            activeforeground=t["text_primary"],
            relief=tk.FLAT,
            bd=0,
            padx=16,
            pady=10,
            cursor="hand2",
        )
        self.btn_clear.pack(side=tk.LEFT)

        # Inline Feedback / Error Message Label
        self.lbl_error = tk.Label(
            self.form_col,
            text="",
            font=theme_mgr.font_small,
            fg="#D9534F",
            bg=t["bg"],
            wraplength=340,
            justify=tk.LEFT,
            anchor="w",
        )
        self.lbl_error.pack(fill=tk.X, pady=(6, 0))

        # Right Column: Visual Result Canvas (Floating Hero Typography & Scale)
        self.result_col = tk.Frame(self.content_row, bg=t["bg"])
        self.result_col.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Initial Empty State or Calculated State
        self._build_result_subview()

    def _build_result_subview(self) -> None:
        """Render either the empty prompt state or the calculated result view."""
        for child in self.result_col.winfo_children():
            child.destroy()

        t = theme_mgr.theme

        if self._current_result is None:
            # Clean floating placeholder
            empty_frame = tk.Frame(self.result_col, bg=t["bg"])
            empty_frame.pack(fill=tk.BOTH, expand=True, pady=30)

            lbl_empty_num = tk.Label(
                empty_frame,
                text="--.-",
                font=theme_mgr.font_hero,
                fg=t["border"],
                bg=t["bg"],
            )
            lbl_empty_num.pack(anchor="w")

            lbl_empty_text = tk.Label(
                empty_frame,
                text="Enter weight and height, then click 'Calculate BMI'.\nYour calculated index, category, and health metrics will appear here.",
                font=theme_mgr.font_body,
                fg=t["text_secondary"],
                bg=t["bg"],
                justify=tk.LEFT,
            )
            lbl_empty_text.pack(anchor="w", pady=(8, 0))
            return

        res = self._current_result
        cat = res["category"]
        cat_color = theme_mgr.get_category_color(cat)

        # Result Details Container
        res_frame = tk.Frame(self.result_col, bg=t["bg"])
        res_frame.pack(fill=tk.BOTH, expand=True)

        # Eyebrow
        tk.Label(
            res_frame,
            text="BODY MASS INDEX",
            font=theme_mgr.font_caption,
            fg=t["text_secondary"],
            bg=t["bg"],
            anchor="w",
        ).pack(anchor="w")

        # Hero Number + Category Pill Row
        hero_row = tk.Frame(res_frame, bg=t["bg"])
        hero_row.pack(anchor="w", pady=(2, 6))

        tk.Label(
            hero_row,
            text=res["display_bmi"],
            font=theme_mgr.font_hero,
            fg=t["text_primary"],
            bg=t["bg"],
        ).pack(side=tk.LEFT, anchor="s")

        # Category Badge
        badge_frame = tk.Frame(hero_row, bg=cat_color, padx=12, pady=4)
        badge_frame.pack(side=tk.LEFT, padx=(20, 0), anchor="center")

        tk.Label(
            badge_frame,
            text=cat.upper(),
            font=theme_mgr.font_caption,
            fg="#FFFFFF",
            bg=cat_color,
        ).pack()

        # Measurement Metadata Line
        meta_line = tk.Label(
            res_frame,
            text=f"Weight: {res['weight']:.1f} kg   •   Height: {res['height']:.2f} m   •   Healthy Target: {res['healthy_weight_range'][0]:.1f} – {res['healthy_weight_range'][1]:.1f} kg",
            font=theme_mgr.font_small,
            fg=t["text_secondary"],
            bg=t["bg"],
            anchor="w",
        )
        meta_line.pack(anchor="w", pady=(0, 20))

        # Visual Scale Indicator Bar
        scale_frame = tk.Frame(res_frame, bg=t["bg"])
        scale_frame.pack(fill=tk.X, pady=(0, 24))

        self._draw_scale_bar(scale_frame, res["raw_bmi"])

        # Editorial Insights & Guidance
        guidance_frame = tk.Frame(
            res_frame,
            bg=t["surface"],
            highlightbackground=t["border"],
            highlightthickness=1,
            padx=18,
            pady=16,
        )
        guidance_frame.pack(fill=tk.X, pady=(0, 20))

        tk.Label(
            guidance_frame,
            text=res["editorial"]["summary"],
            font=theme_mgr.font_subtitle,
            fg=cat_color,
            bg=t["surface"],
            anchor="w",
        ).pack(anchor="w", pady=(0, 6))

        tk.Label(
            guidance_frame,
            text=res["editorial"]["guidance"],
            font=theme_mgr.font_body,
            fg=t["text_primary"],
            bg=t["surface"],
            wraplength=480,
            justify=tk.LEFT,
        ).pack(anchor="w")

        # Save Action & Status Bar
        action_row = tk.Frame(res_frame, bg=t["bg"])
        action_row.pack(fill=tk.X, pady=(4, 0))

        self.btn_save = tk.Button(
            action_row,
            text="Save to Measurement History",
            command=self._on_save,
            font=theme_mgr.font_body_bold,
            bg=t["primary"] if "primary" in t else t["accent"],
            fg=t["text_on_accent"],
            activebackground=t["accent_hover"],
            activeforeground=t["text_on_accent"],
            relief=tk.FLAT,
            bd=0,
            padx=18,
            pady=9,
            cursor="hand2",
        )
        self.btn_save.pack(side=tk.LEFT)

        self.lbl_save_status = tk.Label(
            action_row,
            text="",
            font=theme_mgr.font_small,
            fg=theme_mgr.get("category_normal"),
            bg=t["bg"],
            padx=14,
        )
        self.lbl_save_status.pack(side=tk.LEFT)

    def _draw_scale_bar(self, parent: tk.Widget, current_bmi: float) -> None:
        """Draw a subtle, minimalist multi-segment scale bar with pointer."""
        t = theme_mgr.theme

        # Canvas for custom rendering
        canvas = tk.Canvas(parent, height=44, bg=t["bg"], highlightthickness=0)
        canvas.pack(fill=tk.X)

        # Scale segments: [label, min_bmi, max_bmi, color]
        segments = [
            ("Underweight (<18.5)", 10.0, 18.5, t["category_underweight"]),
            ("Normal (18.5–24.9)", 18.5, 25.0, t["category_normal"]),
            ("Overweight (25–29.9)", 25.0, 30.0, t["category_overweight"]),
            ("Obese (≥30)", 30.0, 42.0, t["category_obese"]),
        ]

        def render_canvas(event=None):
            canvas.delete("all")
            w = canvas.winfo_width()
            if w <= 10:
                return

            bar_y = 10
            bar_height = 8

            total_range = 42.0 - 10.0  # 32.0 BMI units

            # Draw colored segments
            for label, b_min, b_max, color in segments:
                x1 = int(((b_min - 10.0) / total_range) * w)
                x2 = int(((b_max - 10.0) / total_range) * w)
                canvas.create_rectangle(x1, bar_y, x2, bar_y + bar_height, fill=color, outline="")

            # Draw current marker
            clamped_bmi = max(10.0, min(42.0, current_bmi))
            marker_x = int(((clamped_bmi - 10.0) / total_range) * w)

            # Triangle indicator pointing down to bar
            canvas.create_polygon(
                marker_x, bar_y + bar_height + 1,
                marker_x - 6, bar_y + bar_height + 9,
                marker_x + 6, bar_y + bar_height + 9,
                fill=t["text_primary"],
                outline="",
            )
            # Label
            canvas.create_text(
                marker_x,
                bar_y + bar_height + 18,
                text=f"▲ {current_bmi:.1f}",
                font=(theme_mgr.font_family, 8, "bold"),
                fill=t["text_primary"],
            )

        canvas.bind("<Configure>", render_canvas)

    def _on_calculate(self) -> None:
        """Handle calculation request with comprehensive input validation."""
        self.lbl_error.config(text="")
        weight_text = self.entry_weight.get()
        height_text = self.entry_height.get()

        try:
            result = bmi_service.process_calculation(weight_text, height_text)
            self._current_result = result
            self._build_result_subview()
        except ValidationError as e:
            self.lbl_error.config(text=str(e))
        except Exception as e:
            logger.error(f"Unexpected error in calculation: {e}")
            self.lbl_error.config(text="An unexpected error occurred. Please check your inputs.")

    def _on_save(self) -> None:
        """Persist current measurement to database under the active profile."""
        if not self._current_result:
            return

        user_id = app_state.active_user_id
        if not user_id:
            messagebox.showwarning("No Active Profile", "Please select or create a user profile first.")
            return

        res = self._current_result
        try:
            rec_id = bmi_service.save_measurement(
                user_id=user_id,
                weight=res["weight"],
                height=res["height"],
                bmi=res["bmi"],
                category=res["category"],
            )
            self.lbl_save_status.config(text="✓ Saved to history")
            self.btn_save.config(state=tk.DISABLED)
            app_state.notify_data_modified()
            logger.info(f"Measurement #{rec_id} saved from calculator.")
        except Exception as e:
            logger.error(f"Failed to save measurement: {e}")
            messagebox.showerror("Save Error", f"Could not save record: {e}")

    def _on_clear(self) -> None:
        """Clear form entries and reset result view."""
        self.entry_weight.delete(0, tk.END)
        self.entry_height.delete(0, tk.END)
        self.lbl_error.config(text="")
        self._current_result = None
        self._build_result_subview()

    def _on_user_changed(self, user: Dict[str, Any]) -> None:
        """Update active profile badge."""
        self.lbl_profile_tag.config(text=f"Active Profile:  {user['username']}")

    def _on_theme_changed(self, theme: Dict[str, Any]) -> None:
        """Refresh colors for light/dark theme switch."""
        self.config(bg=theme["bg"])
        self.container.config(bg=theme["bg"])
        self.lbl_section_eyebrow.config(fg=theme["accent"], bg=theme["bg"])
        self.lbl_section_title.config(fg=theme["text_primary"], bg=theme["bg"])
        self.profile_pill.config(bg=theme["surface_secondary"])
        self.lbl_profile_tag.config(fg=theme["text_primary"], bg=theme["surface_secondary"])
        self.sep_header.config(bg=theme["border"])
        self.content_row.config(bg=theme["bg"])
        self.form_col.config(bg=theme["bg"])
        self.lbl_form_heading.config(fg=theme["text_primary"], bg=theme["bg"])
        self.lbl_weight.config(fg=theme["text_secondary"], bg=theme["bg"])
        self.entry_weight_frame.config(bg=theme["surface"], highlightbackground=theme["border"])
        self.entry_weight.config(bg=theme["surface"], fg=theme["text_primary"], insertbackground=theme["accent"])
        self.lbl_height.config(fg=theme["text_secondary"], bg=theme["bg"])
        self.entry_height_frame.config(bg=theme["surface"], highlightbackground=theme["border"])
        self.entry_height.config(bg=theme["surface"], fg=theme["text_primary"], insertbackground=theme["accent"])
        self.lbl_height_hint.config(fg=theme["text_muted"], bg=theme["bg"])
        self.btn_calculate.config(
            bg=theme["accent"],
            fg=theme["text_on_accent"],
            activebackground=theme["accent_hover"],
            activeforeground=theme["text_on_accent"],
        )
        self.btn_clear.config(
            bg=theme["surface_secondary"],
            fg=theme["text_primary"],
            activebackground=theme["surface_active"],
            activeforeground=theme["text_primary"],
        )
        self.lbl_error.config(bg=theme["bg"])
        self.result_col.config(bg=theme["bg"])
        self._build_result_subview()
