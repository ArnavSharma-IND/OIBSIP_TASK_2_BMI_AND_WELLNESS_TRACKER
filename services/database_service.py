"""
Database Service Layer
Encapsulates CRUD operations for users and historical BMI measurements,
enforcing domain rules, parameterized queries, and referential integrity.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from database import DatabaseManager, db
from utils.logger import logger
from utils.validators import validate_username, ValidationError


class DatabaseService:
    """Service providing safe database interactions for users and records."""

    def __init__(self, db_manager: Optional[DatabaseManager] = None):
        self.db = db_manager if db_manager is not None else db

    # ---------------------------------------------------------
    # USER MANAGEMENT
    # ---------------------------------------------------------

    def create_user(self, username: str) -> int:
        """Create a new user profile with unique name."""
        clean_name = validate_username(username)
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        with self.db.transaction() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT user_id FROM users WHERE LOWER(username) = LOWER(?);", (clean_name,))
            if cursor.fetchone():
                raise ValidationError(f"A profile named '{clean_name}' already exists.")

            cursor.execute(
                "INSERT INTO users (username, created_at) VALUES (?, ?);",
                (clean_name, now),
            )
            user_id = cursor.lastrowid
            logger.info(f"Created new user profile: ID {user_id} ('{clean_name}')")
            return user_id

    def get_user_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Retrieve user profile by primary key."""
        conn = self.db.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE user_id = ?;", (user_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    def get_user_by_name(self, username: str) -> Optional[Dict[str, Any]]:
        """Retrieve user profile by name (case-insensitive)."""
        conn = self.db.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE LOWER(username) = LOWER(?);", (username.strip(),))
            row = cursor.fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    def get_all_users(self) -> List[Dict[str, Any]]:
        """Retrieve all registered user profiles with measurement count."""
        conn = self.db.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT u.user_id, u.username, u.created_at,
                       COUNT(r.record_id) as record_count,
                       MAX(r.recorded_at) as last_recorded_at
                FROM users u
                LEFT JOIN bmi_records r ON u.user_id = r.user_id
                GROUP BY u.user_id, u.username, u.created_at
                ORDER BY u.user_id ASC;
            """)
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()

    def update_username(self, user_id: int, new_username: str) -> bool:
        """Rename an existing user profile."""
        clean_name = validate_username(new_username)
        with self.db.transaction() as conn:
            cursor = conn.cursor()
            # Verify target user exists
            cursor.execute("SELECT user_id FROM users WHERE user_id = ?;", (user_id,))
            if not cursor.fetchone():
                raise ValidationError("Profile not found.")

            # Check if name is taken by another user
            cursor.execute(
                "SELECT user_id FROM users WHERE LOWER(username) = LOWER(?) AND user_id != ?;",
                (clean_name, user_id),
            )
            if cursor.fetchone():
                raise ValidationError(f"A profile named '{clean_name}' already exists.")

            cursor.execute(
                "UPDATE users SET username = ? WHERE user_id = ?;",
                (clean_name, user_id),
            )
            logger.info(f"Updated user ID {user_id} to '{clean_name}'")
            return True

    def delete_user(self, user_id: int) -> bool:
        """Delete a user profile and all associated records."""
        with self.db.transaction() as conn:
            cursor = conn.cursor()
            # Ensure at least one profile remains
            cursor.execute("SELECT COUNT(*) FROM users;")
            if cursor.fetchone()[0] <= 1:
                raise ValidationError("Cannot delete the only remaining profile. Create another profile first.")

            cursor.execute("DELETE FROM users WHERE user_id = ?;", (user_id,))
            logger.info(f"Deleted user ID {user_id} and all cascaded records")
            return True

    # ---------------------------------------------------------
    # BMI RECORD MANAGEMENT
    # ---------------------------------------------------------

    def add_record(
        self,
        user_id: int,
        weight: float,
        height: float,
        bmi: float,
        category: str,
        recorded_at: Optional[str] = None,
    ) -> int:
        """Insert a new validated BMI measurement record."""
        timestamp = recorded_at or datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        with self.db.transaction() as conn:
            cursor = conn.cursor()
            # Verify user exists
            cursor.execute("SELECT user_id FROM users WHERE user_id = ?;", (user_id,))
            if not cursor.fetchone():
                raise ValidationError(f"User ID {user_id} does not exist.")

            cursor.execute(
                """
                INSERT INTO bmi_records (user_id, weight, height, bmi, category, recorded_at)
                VALUES (?, ?, ?, ?, ?, ?);
                """,
                (user_id, round(float(weight), 2), round(float(height), 3), round(float(bmi), 2), category, timestamp),
            )
            record_id = cursor.lastrowid
            logger.info(f"Saved BMI record #{record_id} for user ID {user_id} (BMI: {bmi:.2f})")
            return record_id

    def get_records_by_user(
        self,
        user_id: int,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        order: str = "DESC",
    ) -> List[Dict[str, Any]]:
        """Retrieve historical records for a user with optional date filtering."""
        sort_order = "ASC" if order.upper() == "ASC" else "DESC"
        query = "SELECT * FROM bmi_records WHERE user_id = ?"
        params: List[Any] = [user_id]

        if start_date:
            query += " AND recorded_at >= ?"
            params.append(f"{start_date} 00:00:00" if len(start_date) == 10 else start_date)

        if end_date:
            query += " AND recorded_at <= ?"
            params.append(f"{end_date} 23:59:59" if len(end_date) == 10 else end_date)

        query += f" ORDER BY recorded_at {sort_order}, record_id {sort_order};"

        conn = self.db.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(query, tuple(params))
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()

    def get_record_by_id(self, record_id: int) -> Optional[Dict[str, Any]]:
        """Retrieve a specific record by primary key."""
        conn = self.db.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM bmi_records WHERE record_id = ?;", (record_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    def delete_record(self, record_id: int) -> bool:
        """Delete an individual measurement record."""
        with self.db.transaction() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM bmi_records WHERE record_id = ?;", (record_id,))
            affected = cursor.rowcount > 0
            if affected:
                logger.info(f"Deleted BMI record #{record_id}")
            return affected

    def get_record_count(self, user_id: int) -> int:
        """Return total measurements count for a user."""
        conn = self.db.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM bmi_records WHERE user_id = ?;", (user_id,))
            return cursor.fetchone()[0]
        finally:
            conn.close()

    def get_latest_record(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Retrieve the most recent measurement for a user."""
        conn = self.db.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM bmi_records WHERE user_id = ? ORDER BY recorded_at DESC, record_id DESC LIMIT 1;",
                (user_id,),
            )
            row = cursor.fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    def get_previous_record(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Retrieve the second most recent measurement for a user (for delta comparison)."""
        conn = self.db.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM bmi_records WHERE user_id = ? ORDER BY recorded_at DESC, record_id DESC LIMIT 1 OFFSET 1;",
                (user_id,),
            )
            row = cursor.fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    def get_user_statistics(self, user_id: int) -> Dict[str, Any]:
        """Aggregate statistical summary for a user."""
        conn = self.db.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT
                    COUNT(*) as total_count,
                    MIN(bmi) as min_bmi,
                    MAX(bmi) as max_bmi,
                    AVG(bmi) as avg_bmi,
                    MIN(weight) as min_weight,
                    MAX(weight) as max_weight,
                    AVG(weight) as avg_weight
                FROM bmi_records
                WHERE user_id = ?;
                """,
                (user_id,),
            )
            row = cursor.fetchone()
            stats = dict(row) if row else {}

            latest = self.get_latest_record(user_id)
            prev = self.get_previous_record(user_id)

            stats["latest"] = latest
            stats["previous"] = prev
            return stats
        finally:
            conn.close()


# Global database service instance
db_service = DatabaseService()
