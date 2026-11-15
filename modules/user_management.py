"""
User Management Module
Handles multi-user profile creation, switching, renaming, and safe deletion with confirmation.
"""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from typing import Dict, Any, List

from themes.manager import theme_mgr
from services.app_state import app_state
from services.database_service import db_service
from utils.validators import validate_username, ValidationError
from utils.helpers import format_display_date
from utils.logger import logger


class UserManagementView(tk.Frame):
    """Profile administration screen with multi-user isolation and CRUD controls."""

    def __init__(self, parent: tk.Widget):
        super().__init__(parent, bg=theme_mgr.get("bg"))

        self._build_ui()
        self.load_users()

        # Observers
        theme_mgr.subscribe(self._on_theme_changed)
        app_state.subscribe_user_changed(self._on_user_changed)
        app_state.subscribe_data_modified(self.load_users)

    def _build_ui(self) -> None:
        """Construct user management view."""
        t = theme_mgr.theme

        self.container = tk.Frame(self, bg=t["bg"])
        self.container.pack(fill=tk.BOTH, expand=True, padx=48, pady=36)

        # -------------------------------------------------------------
        # Header: Title & New User Action
        # -------------------------------------------------------------
        header_row = tk.Frame(self.container, bg=t["bg"])
        header_row.pack(fill=tk.X, pady=(0, 20))

        title_sub = tk.Frame(header_row, bg=t["bg"])
        title_sub.pack(side=tk.LEFT)

        self.lbl_eyebrow = tk.Label(
            title_sub,
            text="ACCOUNT & PROFILES",
            font=theme_mgr.font_caption,
            fg=t["accent"],
            bg=t["bg"],
            anchor="w",
        )
        self.lbl_eyebrow.pack(anchor="w")

        self.lbl_title = tk.Label(
            title_sub,
            text="User Profiles",
            font=theme_mgr.font_title,
            fg=t["text_primary"],
            bg=t["bg"],
            anchor="w",
        )
        self.lbl_title.pack(anchor="w", pady=(2, 0))

        # Action: Add Profile Button
        self.btn_add_user = tk.Button(
            header_row,
            text="+ Add New Profile",
            command=self._on_create_user,
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
        self.btn_add_user.pack(side=tk.RIGHT, anchor="center")

        # Divider
        self.sep = tk.Frame(self.container, height=1, bg=t["border"])
        self.sep.pack(fill=tk.X, pady=(0, 24))

        # -------------------------------------------------------------
        # User Profiles Table
        # -------------------------------------------------------------
        table_container = tk.Frame(self.container, bg=t["surface"], highlightbackground=t["border"], highlightthickness=1)
        table_container.pack(fill=tk.BOTH, expand=True, pady=(0, 20))

        columns = ("id", "username", "created", "count", "status")
        self.tree = ttk.Treeview(
            table_container,
            columns=columns,
            show="headings",
            selectmode="browse",
        )

        self.tree.heading("id", text="USER ID", anchor="w")
        self.tree.heading("username", text="PROFILE NAME", anchor="w")
        self.tree.heading("created", text="CREATED ON", anchor="w")
        self.tree.heading("count", text="MEASUREMENTS", anchor="center")
        self.tree.heading("status", text="STATUS", anchor="e")

        self.tree.column("id", width=90, anchor="w")
        self.tree.column("username", width=220, anchor="w")
        self.tree.column("created", width=180, anchor="w")
        self.tree.column("count", width=140, anchor="center")
        self.tree.column("status", width=140, anchor="e")

        scroll = ttk.Scrollbar(table_container, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)

        # -------------------------------------------------------------
        # Action Toolbar (Switch, Rename, Delete)
        # -------------------------------------------------------------
        action_bar = tk.Frame(self.container, bg=t["bg"])
        action_bar.pack(fill=tk.X)

        self.btn_switch = tk.Button(
            action_bar,
            text="Switch to Selected Profile",
            command=self._on_switch_user,
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
        self.btn_switch.pack(side=tk.LEFT, padx=(0, 10))

        self.btn_rename = tk.Button(
            action_bar,
            text="Rename Profile",
            command=self._on_rename_user,
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
        self.btn_rename.pack(side=tk.LEFT, padx=(0, 10))

        self.btn_delete = tk.Button(
            action_bar,
            text="Delete Profile",
            command=self._on_delete_user,
            font=theme_mgr.font_body,
            bg=t["surface_secondary"],
            fg="#C94A4A",
            activebackground=t["surface_active"],
            activeforeground="#C94A4A",
            relief=tk.FLAT,
            bd=0,
            padx=14,
            pady=8,
            cursor="hand2",
        )
        self.btn_delete.pack(side=tk.RIGHT)

    def load_users(self) -> None:
        """Fetch all users and populate table."""
        for item in self.tree.get_children():
            self.tree.delete(item)

        users = db_service.get_all_users()
        active_id = app_state.active_user_id

        for u in users:
            uid = u["user_id"]
            is_active = (uid == active_id)
            created_str = format_display_date(u["created_at"], include_time=False)
            status_str = "● ACTIVE" if is_active else ""

            self.tree.insert(
                "",
                tk.END,
                iid=str(uid),
                values=(
                    f"#{uid}",
                    u["username"],
                    created_str,
                    f"{u['record_count']} entries",
                    status_str,
                ),
            )

    def _on_switch_user(self) -> None:
        """Switch active profile to selected table row."""
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo("Select Profile", "Please select a profile to activate.")
            return

        user_id = int(selected[0])
        app_state.set_active_user(user_id)
        self.load_users()
        messagebox.showinfo("Profile Switched", f"Now viewing records for {app_state.active_username}.")

    def _on_create_user(self) -> None:
        """Prompt dialog for creating a new user."""
        name = simpledialog.askstring("New Profile", "Enter a name for the new profile:", parent=self)
        if name is None:
            return

        try:
            new_id = db_service.create_user(name)
            app_state.set_active_user(new_id)
            self.load_users()
            messagebox.showinfo("Success", f"Profile '{name.strip()}' created and activated.")
        except ValidationError as e:
            messagebox.showerror("Validation Error", str(e))
        except Exception as e:
            logger.error(f"Error creating user: {e}")
            messagebox.showerror("Error", f"Failed to create user: {e}")

    def _on_rename_user(self) -> None:
        """Rename selected user profile."""
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo("Select Profile", "Please select a profile to rename.")
            return

        user_id = int(selected[0])
        user = db_service.get_user_by_id(user_id)
        if not user:
            return

        new_name = simpledialog.askstring(
            "Rename Profile",
            f"Enter new name for '{user['username']}':",
            initialvalue=user["username"],
            parent=self,
        )
        if new_name is None:
            return

        try:
            db_service.update_username(user_id, new_name)
            app_state.refresh_active_user()
            self.load_users()
            messagebox.showinfo("Renamed", f"Profile renamed to '{new_name.strip()}'.")
        except ValidationError as e:
            messagebox.showerror("Validation Error", str(e))
        except Exception as e:
            logger.error(f"Error renaming user: {e}")
            messagebox.showerror("Error", f"Failed to rename profile: {e}")

    def _on_delete_user(self) -> None:
        """Delete user profile with strict confirmation dialog."""
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo("Select Profile", "Please select a profile to delete.")
            return

        user_id = int(selected[0])
        user = db_service.get_user_by_id(user_id)
        if not user:
            return

        records_count = db_service.get_record_count(user_id)
        confirm = messagebox.askyesno(
            "Delete Profile",
            f"Are you sure you want to delete profile '{user['username']}'?\n\n"
            f"• All {records_count} BMI measurement records will be permanently removed.\n"
            f"• This action cannot be reversed.",
            icon=messagebox.WARNING,
        )

        if confirm:
            try:
                db_service.delete_user(user_id)
                # If deleted user was active, switch to first available user
                if app_state.active_user_id == user_id:
                    remaining = db_service.get_all_users()
                    if remaining:
                        app_state.set_active_user(remaining[0]["user_id"])

                self.load_users()
                messagebox.showinfo("Deleted", f"Profile '{user['username']}' deleted.")
            except ValidationError as e:
                messagebox.showwarning("Cannot Delete", str(e))
            except Exception as e:
                logger.error(f"Error deleting user: {e}")
                messagebox.showerror("Error", f"Could not delete profile: {e}")

    def _on_user_changed(self, user: Dict[str, Any]) -> None:
        self.load_users()

    def _on_theme_changed(self, theme: Dict[str, Any]) -> None:
        self.config(bg=theme["bg"])
        self.container.config(bg=theme["bg"])
        self.lbl_eyebrow.config(fg=theme["accent"], bg=theme["bg"])
        self.lbl_title.config(fg=theme["text_primary"], bg=theme["bg"])
        self.sep.config(bg=theme["border"])
        self.btn_add_user.config(
            bg=theme["accent"],
            fg=theme["text_on_accent"],
            activebackground=theme["accent_hover"],
            activeforeground=theme["text_on_accent"],
        )
        self.btn_switch.config(
            bg=theme["accent"],
            fg=theme["text_on_accent"],
            activebackground=theme["accent_hover"],
            activeforeground=theme["text_on_accent"],
        )
        self.btn_rename.config(bg=theme["surface_secondary"], fg=theme["text_primary"])
        self.btn_delete.config(bg=theme["surface_secondary"])
        self.load_users()
