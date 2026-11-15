"""
Database Backup & Disaster Recovery Service
Performs hot SQLite backups, deep structure and integrity validation, and safe restorations.
"""

import sqlite3
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, Tuple

from config import DB_PATH, DATA_DIR
from utils.logger import logger


class BackupService:
    """Provides hot SQLite database backups and verified disaster recovery."""

    def __init__(self, current_db_path: Optional[Path] = None):
        self.db_path = Path(current_db_path) if current_db_path else DB_PATH

    def create_backup(self, target_path: Optional[Path] = None) -> Dict[str, Any]:
        """
        Create a consistent, safe backup of the current database using SQLite's online backup API.
        """
        if not self.db_path.exists():
            return {
                "success": False,
                "error": "Current database does not exist on disk yet.",
                "backup_path": None,
            }

        if target_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"bmi_records_backup_{timestamp}.sqlite"
            backup_dir = DATA_DIR / "backups"
            backup_dir.mkdir(parents=True, exist_ok=True)
            target_path = backup_dir / backup_filename
        else:
            target_path = Path(target_path)

        target_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            # Use SQLite online backup API for ACID safety even while app is active
            src_conn = sqlite3.connect(str(self.db_path))
            dst_conn = sqlite3.connect(str(target_path))

            with dst_conn:
                src_conn.backup(dst_conn, pages=100)

            dst_conn.close()
            src_conn.close()

            logger.info(f"Database successfully backed up to: {target_path}")
            return {
                "success": True,
                "error": None,
                "backup_path": str(target_path),
            }

        except Exception as e:
            logger.error(f"Backup failed: {e}")
            return {
                "success": False,
                "error": f"Failed to create backup: {e}",
                "backup_path": None,
            }

    def validate_backup_file(self, backup_file_path: Path) -> Tuple[bool, str]:
        """
        Thoroughly validate whether a candidate file is a valid, readable BMI database backup.
        Checks:
        1. File existence and non-zero size
        2. SQLite header magic bytes ('SQLite format 3\\0')
        3. PRAGMA integrity_check passes
        4. Contains required tables ('users', 'bmi_records')
        """
        p = Path(backup_file_path)
        if not p.exists():
            return False, "File does not exist."

        if p.stat().st_size < 100:
            return False, "File is too small to be a valid SQLite database."

        # Check SQLite magic header
        try:
            with open(p, "rb") as f:
                header = f.read(16)
                if not header.startswith(b"SQLite format 3\x00"):
                    return False, "Selected file is not a valid SQLite database (invalid header)."
        except Exception as e:
            return False, f"Could not read file header: {e}"

        # Connect and check internal schema
        try:
            conn = sqlite3.connect(str(p))
            cursor = conn.cursor()

            # Integrity check
            cursor.execute("PRAGMA integrity_check;")
            integrity_row = cursor.fetchone()
            if not integrity_row or integrity_row[0].lower() != "ok":
                conn.close()
                return False, "Database file failed SQLite integrity check (corrupted)."

            # Check table existence
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name IN ('users', 'bmi_records');"
            )
            tables = {row[0] for row in cursor.fetchall()}
            conn.close()

            if "users" not in tables or "bmi_records" not in tables:
                return False, "Database lacks required application tables ('users' or 'bmi_records')."

            return True, "Backup file is valid and verified."

        except Exception as e:
            return False, f"Failed to inspect backup database: {e}"

    def restore_backup(self, backup_file_path: Path) -> Dict[str, Any]:
        """
        Safely restore the active database from a verified backup file.
        Before overwriting, creates a temporary safeguard copy of the current database.
        """
        backup_path = Path(backup_file_path)

        # Validate candidate backup file first
        is_valid, msg = self.validate_backup_file(backup_path)
        if not is_valid:
            return {"success": False, "error": f"Invalid backup file: {msg}"}

        safeguard_copy = None
        try:
            # 1. Create a safeguard backup of current DB if it exists
            if self.db_path.exists():
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                safeguard_copy = self.db_path.parent / f"pre_restore_safeguard_{timestamp}.bak"
                shutil.copy2(self.db_path, safeguard_copy)
                logger.info(f"Created pre-restore safeguard copy at: {safeguard_copy}")

            # 2. Perform restore by atomic file copy
            shutil.copy2(backup_path, self.db_path)
            logger.info(f"Successfully restored database from: {backup_path}")

            return {
                "success": True,
                "error": None,
                "message": "Database restored successfully.",
                "safeguard_path": str(safeguard_copy) if safeguard_copy else None,
            }

        except Exception as e:
            logger.error(f"Restoration failed: {e}")
            # If restoration failed and we have safeguard, roll back
            if safeguard_copy and safeguard_copy.exists():
                shutil.copy2(safeguard_copy, self.db_path)
                logger.info("Rolled back to pre-restore safeguard database.")

            return {
                "success": False,
                "error": f"Restoration failed: {e}",
                "message": "Database could not be restored.",
            }


# Global backup service instance
backup_service = BackupService()
