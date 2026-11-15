"""
Unit and Integration Tests for Services Layer
Tests BMIService calculations, multi-user isolation, CSV export formatting,
and database backup and restoration safety.
"""

import tempfile
import csv
from pathlib import Path
import pytest

from database import DatabaseManager
from services.database_service import DatabaseService
from services.bmi_service import BMIService
from services.export_service import ExportService
from services.backup_service import BackupService


@pytest.fixture
def service_bundle():
    """Create an isolated test suite bundle with temporary database."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "suite_test.db"
        manager = DatabaseManager(db_path=db_path)
        db_svc = DatabaseService(db_manager=manager)
        bmi_svc = BMIService(database_service=db_svc)
        exp_svc = ExportService(database_service=db_svc)
        bup_svc = BackupService(current_db_path=db_path)

        yield {
            "tmpdir": Path(tmpdir),
            "db_path": db_path,
            "manager": manager,
            "db_svc": db_svc,
            "bmi_svc": bmi_svc,
            "exp_svc": exp_svc,
            "bup_svc": bup_svc,
        }


class TestBMIService:
    """Verifies BMI processing and smart non-clinical insights."""

    def test_process_calculation(self, service_bundle):
        bmi_svc = service_bundle["bmi_svc"]
        result = bmi_svc.process_calculation("75.0", "1.80")

        assert result["weight"] == 75.0
        assert result["height"] == 1.80
        assert result["category"] == "Normal"
        assert result["display_bmi"] == "23.15"
        assert "healthy_weight_range" in result

    def test_multi_user_isolation(self, service_bundle):
        db_svc = service_bundle["db_svc"]

        user_alice = db_svc.create_user("Alice")
        user_bob = db_svc.create_user("Bob")

        # Alice records 2 measurements
        db_svc.add_record(user_alice, 60.0, 1.65, 22.04, "Normal")
        db_svc.add_record(user_alice, 61.0, 1.65, 22.41, "Normal")

        # Bob records 1 measurement
        db_svc.add_record(user_bob, 90.0, 1.85, 26.30, "Overweight")

        alice_records = db_svc.get_records_by_user(user_alice)
        bob_records = db_svc.get_records_by_user(user_bob)

        assert len(alice_records) == 2
        assert len(bob_records) == 1
        assert alice_records[0]["user_id"] == user_alice
        assert bob_records[0]["user_id"] == user_bob

    def test_insights_generation(self, service_bundle):
        db_svc = service_bundle["db_svc"]
        bmi_svc = service_bundle["bmi_svc"]

        user = db_svc.create_user("Charlie")

        # Onboarding insight when 0 records
        insights_0 = bmi_svc.generate_insights(user)
        assert len(insights_0) >= 1
        assert "Welcome" in insights_0[0]

        # 1 record
        db_svc.add_record(user, 70.0, 1.75, 22.86, "Normal", "2026-11-01 10:00:00")
        insights_1 = bmi_svc.generate_insights(user)
        assert any("healthy reference range" in i for i in insights_1)

        # 2 records: delta comparison
        db_svc.add_record(user, 72.0, 1.75, 23.51, "Normal", "2026-11-10 10:00:00")
        insights_2 = bmi_svc.generate_insights(user)
        assert any("increased" in i for i in insights_2)


class TestExportService:
    """Verifies CSV generation and structured file headers."""

    def test_csv_export(self, service_bundle):
        db_svc = service_bundle["db_svc"]
        exp_svc = service_bundle["exp_svc"]
        tmpdir = service_bundle["tmpdir"]

        user_id = db_svc.create_user("Diana")
        db_svc.add_record(user_id, 65.0, 1.70, 22.49, "Normal", "2026-11-05 08:30:00")
        db_svc.add_record(user_id, 66.0, 1.70, 22.84, "Normal", "2026-11-12 08:30:00")

        export_path = tmpdir / "diana_export.csv"
        result = exp_svc.export_user_history_to_csv(user_id, target_path=export_path)

        assert result["success"] is True
        assert result["rows_exported"] == 2
        assert export_path.exists()

        # Read back CSV
        with open(export_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
            assert any("Profile: Diana" in line for line in lines)
            assert any("Date & Time" in line for line in lines)
            assert any("22.49" in line for line in lines)


class TestBackupService:
    """Verifies SQLite hot backups, validation checks, and restorations."""

    def test_backup_and_restore(self, service_bundle):
        db_svc = service_bundle["db_svc"]
        bup_svc = service_bundle["bup_svc"]
        tmpdir = service_bundle["tmpdir"]

        user_id = db_svc.create_user("Ethan")
        db_svc.add_record(user_id, 80.0, 1.82, 24.15, "Normal")

        # 1. Create backup
        backup_file = tmpdir / "test_backup.sqlite"
        res_backup = bup_svc.create_backup(target_path=backup_file)
        assert res_backup["success"] is True
        assert backup_file.exists()

        # 2. Validate backup
        is_valid, msg = bup_svc.validate_backup_file(backup_file)
        assert is_valid is True

        # 3. Modify active database (add record)
        db_svc.add_record(user_id, 82.0, 1.82, 24.75, "Normal")
        assert db_svc.get_record_count(user_id) == 2

        # 4. Restore backup
        res_restore = bup_svc.restore_backup(backup_file)
        assert res_restore["success"] is True

        # Reopen and verify count is rolled back to 1
        new_manager = DatabaseManager(db_path=service_bundle["db_path"])
        new_db_svc = DatabaseService(db_manager=new_manager)
        assert new_db_svc.get_record_count(user_id) == 1

    def test_invalid_backup_rejected(self, service_bundle):
        bup_svc = service_bundle["bup_svc"]
        tmpdir = service_bundle["tmpdir"]

        # 1. Test too-small file
        fake_small = tmpdir / "small.sqlite"
        fake_small.write_text("Too small")
        is_valid, msg = bup_svc.validate_backup_file(fake_small)
        assert is_valid is False
        assert "too small" in msg.lower()

        # 2. Test large enough file without valid SQLite header
        fake_file = tmpdir / "fake.sqlite"
        fake_file.write_text("X" * 200)

        is_valid, msg = bup_svc.validate_backup_file(fake_file)
        assert is_valid is False
        assert "not a valid sqlite database" in msg.lower()
