"""
Unit Tests for Database Engine & SQLite Operations
Tests isolation using temporary database files, transactional safety, schema versions,
foreign key cascades, and record integrity.
"""

import tempfile
from pathlib import Path
import pytest
import sqlite3

from database import DatabaseManager
from services.database_service import DatabaseService
from utils.validators import ValidationError


@pytest.fixture
def temp_db_service():
    """Create a temporary DatabaseService backed by an isolated SQLite file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test_bmi.db"
        manager = DatabaseManager(db_path=db_path)
        service = DatabaseService(db_manager=manager)
        yield service


class TestDatabaseManager:
    """Verifies low-level database manager behaviors."""

    def test_schema_initialization(self, temp_db_service):
        conn = temp_db_service.db.get_connection()
        cursor = conn.cursor()

        # Check tables exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = {row["name"] for row in cursor.fetchall()}
        assert "users" in tables
        assert "bmi_records" in tables
        assert "schema_version" in tables

        # Verify foreign keys are enabled
        cursor.execute("PRAGMA foreign_keys;")
        assert cursor.fetchone()[0] == 1
        conn.close()


class TestUserManagement:
    """Verifies multi-user profile operations."""

    def test_default_seed_user_created(self, temp_db_service):
        users = temp_db_service.get_all_users()
        assert len(users) >= 1
        assert users[0]["username"] == "Primary User"

    def test_create_user(self, temp_db_service):
        user_id = temp_db_service.create_user("Arnav")
        assert user_id > 0

        user = temp_db_service.get_user_by_id(user_id)
        assert user is not None
        assert user["username"] == "Arnav"

    def test_duplicate_user_rejected(self, temp_db_service):
        temp_db_service.create_user("UniqueUser")
        with pytest.raises(ValidationError, match="already exists"):
            temp_db_service.create_user("uniqueuser")  # Case insensitive check

    def test_update_username(self, temp_db_service):
        user_id = temp_db_service.create_user("OriginalName")
        success = temp_db_service.update_username(user_id, "RenamedProfile")
        assert success is True

        user = temp_db_service.get_user_by_id(user_id)
        assert user["username"] == "RenamedProfile"

    def test_delete_user_cascades_records(self, temp_db_service):
        user_a = temp_db_service.create_user("UserA")
        temp_db_service.add_record(user_a, 70.0, 1.75, 22.86, "Normal")
        temp_db_service.add_record(user_a, 71.0, 1.75, 23.18, "Normal")

        assert temp_db_service.get_record_count(user_a) == 2

        # Delete user
        temp_db_service.delete_user(user_a)

        # Profile should be gone
        assert temp_db_service.get_user_by_id(user_a) is None
        # Records should be cleanly cascaded and gone
        records = temp_db_service.get_records_by_user(user_a)
        assert len(records) == 0

    def test_prevent_deleting_only_user(self, temp_db_service):
        users = temp_db_service.get_all_users()
        # Delete down to 1 user
        while len(users) > 1:
            temp_db_service.delete_user(users.pop()["user_id"])

        # Attempting to delete the last remaining user must fail
        with pytest.raises(ValidationError, match="Cannot delete the only remaining profile"):
            temp_db_service.delete_user(users[0]["user_id"])


class TestRecordManagement:
    """Verifies BMI record insertions, queries, and filters."""

    def test_add_and_retrieve_record(self, temp_db_service):
        users = temp_db_service.get_all_users()
        user_id = users[0]["user_id"]

        rec_id = temp_db_service.add_record(
            user_id=user_id,
            weight=72.5,
            height=1.75,
            bmi=23.67,
            category="Normal",
            recorded_at="2026-11-10 10:00:00",
        )
        assert rec_id > 0

        rec = temp_db_service.get_record_by_id(rec_id)
        assert rec["weight"] == 72.5
        assert rec["height"] == 1.75
        assert rec["bmi"] == 23.67
        assert rec["category"] == "Normal"

    def test_foreign_key_violation_for_nonexistent_user(self, temp_db_service):
        with pytest.raises(ValidationError):
            temp_db_service.add_record(
                user_id=99999,
                weight=70.0,
                height=1.75,
                bmi=22.86,
                category="Normal",
            )

    def test_date_range_filtering(self, temp_db_service):
        users = temp_db_service.get_all_users()
        user_id = users[0]["user_id"]

        temp_db_service.add_record(user_id, 70, 1.75, 22.86, "Normal", "2026-01-01 12:00:00")
        temp_db_service.add_record(user_id, 71, 1.75, 23.18, "Normal", "2026-02-15 12:00:00")
        temp_db_service.add_record(user_id, 72, 1.75, 23.51, "Normal", "2026-03-30 12:00:00")

        # Query records in February only
        feb_records = temp_db_service.get_records_by_user(
            user_id,
            start_date="2026-02-01",
            end_date="2026-02-28",
        )
        assert len(feb_records) == 1
        assert feb_records[0]["weight"] == 71.0

    def test_delete_individual_record(self, temp_db_service):
        users = temp_db_service.get_all_users()
        user_id = users[0]["user_id"]

        rec_id = temp_db_service.add_record(user_id, 75.0, 1.80, 23.15, "Normal")
        assert temp_db_service.delete_record(rec_id) is True
        assert temp_db_service.get_record_by_id(rec_id) is None
