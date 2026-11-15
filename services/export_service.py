"""
CSV Export Service
Exports user-specific BMI histories into standard, well-structured CSV spreadsheets.
"""

import csv
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List

from services.database_service import DatabaseService, db_service
from utils.logger import logger


class ExportService:
    """Handles structured data export of BMI records to standard CSV format."""

    def __init__(self, database_service: Optional[DatabaseService] = None):
        self.db_svc = database_service if database_service is not None else db_service

    def export_user_history_to_csv(
        self,
        user_id: int,
        target_path: Optional[Path] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Export all or filtered measurement records for a specific user to a CSV file.

        Returns a dictionary with status, message, row count, and path.
        """
        user = self.db_svc.get_user_by_id(user_id)
        if not user:
            return {
                "success": False,
                "error": f"User ID {user_id} was not found.",
                "rows_exported": 0,
                "file_path": None,
            }

        username = user["username"]
        records = self.db_svc.get_records_by_user(
            user_id=user_id,
            start_date=start_date,
            end_date=end_date,
            order="ASC",  # Chronological order in export
        )

        if not records:
            return {
                "success": False,
                "error": f"No records found to export for '{username}'.",
                "rows_exported": 0,
                "file_path": None,
            }

        # Resolve destination path
        if target_path is None:
            clean_username = "".join(c for c in username if c.isalnum() or c in (" ", "_", "-")).strip().replace(" ", "_")
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"bmi_history_{clean_username}_{timestamp}.csv"
            # Default export directory is user's desktop or data directory
            desktop_dir = Path.home() / "Desktop"
            target_path = (desktop_dir if desktop_dir.exists() else Path.cwd()) / filename
        else:
            target_path = Path(target_path)

        target_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            with open(target_path, "w", newline="", encoding="utf-8") as csvfile:
                writer = csv.writer(csvfile)

                # Header with metadata
                writer.writerow(["# BMI & Wellness Tracker - Historical Data Export"])
                writer.writerow([f"# Profile: {username} (ID: {user_id})"])
                writer.writerow([f"# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"])
                writer.writerow([f"# Total Records: {len(records)}"])
                writer.writerow([])  # Blank separator

                # Column headers
                headers = [
                    "Record ID",
                    "Date & Time",
                    "Weight (kg)",
                    "Height (m)",
                    "BMI",
                    "Category",
                ]
                writer.writerow(headers)

                # Data rows
                for r in records:
                    writer.writerow([
                        r["record_id"],
                        r["recorded_at"],
                        f"{r['weight']:.2f}",
                        f"{r['height']:.3f}",
                        f"{r['bmi']:.2f}",
                        r["category"],
                    ])

            logger.info(f"Exported {len(records)} records for '{username}' to {target_path}")
            return {
                "success": True,
                "error": None,
                "rows_exported": len(records),
                "file_path": str(target_path),
            }

        except Exception as e:
            logger.error(f"Failed to export records to CSV: {e}")
            return {
                "success": False,
                "error": f"Failed to write CSV file: {e}",
                "rows_exported": 0,
                "file_path": None,
            }


# Global export service instance
export_service = ExportService()
