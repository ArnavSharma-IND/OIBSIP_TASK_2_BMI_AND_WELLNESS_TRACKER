"""
Application State Manager
Coordinates shared global state: active user profile, theme synchronization,
cross-view change notifications, and navigation triggers.
"""

from typing import Optional, Dict, Any, List, Callable
from services.database_service import db_service
from config import load_settings, save_settings
from utils.logger import logger


class AppState:
    """Manages active session context and dispatches state change events."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AppState, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if getattr(self, "_initialized", False):
            return

        self._active_user: Optional[Dict[str, Any]] = None
        self._user_listeners: List[Callable[[Dict[str, Any]], None]] = []
        self._data_listeners: List[Callable[[], None]] = []
        self._nav_listeners: List[Callable[[str], None]] = []

        # Load persisted active user ID or default to first available user
        settings = load_settings()
        saved_user_id = settings.get("active_user_id")

        if saved_user_id:
            user = db_service.get_user_by_id(saved_user_id)
            if user:
                self._active_user = user

        if not self._active_user:
            users = db_service.get_all_users()
            if users:
                self._active_user = users[0]
                self._persist_active_user()

        self._initialized = True

    @property
    def active_user(self) -> Optional[Dict[str, Any]]:
        return self._active_user

    @property
    def active_user_id(self) -> Optional[int]:
        return self._active_user["user_id"] if self._active_user else None

    @property
    def active_username(self) -> str:
        return self._active_user["username"] if self._active_user else "Guest"

    def set_active_user(self, user_id: int) -> bool:
        """Switch active user profile by ID and notify subscribers."""
        user = db_service.get_user_by_id(user_id)
        if not user:
            logger.warning(f"Failed to switch to non-existent user ID {user_id}")
            return False

        self._active_user = user
        self._persist_active_user()
        logger.info(f"Active profile switched to: '{user['username']}' (ID {user_id})")

        # Notify user change subscribers
        for callback in list(self._user_listeners):
            try:
                callback(user)
            except Exception as e:
                logger.error(f"Error in user_changed subscriber: {e}")

        # Also trigger data refresh
        self.notify_data_modified()
        return True

    def refresh_active_user(self) -> None:
        """Reload active user details from database (e.g. after rename)."""
        if self._active_user:
            updated = db_service.get_user_by_id(self._active_user["user_id"])
            if updated:
                self._active_user = updated
                for callback in list(self._user_listeners):
                    try:
                        callback(updated)
                    except Exception:
                        pass

    def _persist_active_user(self) -> None:
        """Save active user ID to settings.json."""
        if self._active_user:
            settings = load_settings()
            settings["active_user_id"] = self._active_user["user_id"]
            save_settings(settings)

    def subscribe_user_changed(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        """Subscribe to active user profile changes."""
        if callback not in self._user_listeners:
            self._user_listeners.append(callback)

    def subscribe_data_modified(self, callback: Callable[[], None]) -> None:
        """Subscribe to database modification events (new record, deleted record)."""
        if callback not in self._data_listeners:
            self._data_listeners.append(callback)

    def subscribe_nav_requested(self, callback: Callable[[str], None]) -> None:
        """Subscribe to section navigation requests."""
        if callback not in self._nav_listeners:
            self._nav_listeners.append(callback)

    def notify_data_modified(self) -> None:
        """Broadcast database update event to all active views."""
        for callback in list(self._data_listeners):
            try:
                callback()
            except Exception as e:
                logger.error(f"Error in data_modified subscriber: {e}")

    def request_navigation(self, section_name: str) -> None:
        """Request the main application shell to navigate to a target section."""
        for callback in list(self._nav_listeners):
            try:
                callback(section_name)
            except Exception as e:
                logger.error(f"Error in navigation subscriber: {e}")


# Global Application State instance
app_state = AppState()
