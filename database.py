"""
Database Engine & Persistence Layer
Manages SQLite connection lifecycle, schema initialization, migrations, foreign key enforcement,
and transactional safety.
"""

import sqlite3
from pathlib import Path
from typing import Optional, Generator
from contextlib import contextmanager
from datetime import datetime

from config import DB_PATH, SCHEMA_VERSION
from utils.logger import logger


class DatabaseManager:
    """Handles SQLite database initialization, schema versioning, and connections."""

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = Path(db_path) if db_path else DB_PATH
        # Ensure parent directory exists for file-based DBs
        if str(self.db_path) != ":memory:":
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.init_database()

    def get_connection(self) -> sqlite3.Connection:
        """Create and configure a fresh SQLite connection with foreign keys enabled."""
        try:
            conn = sqlite3.connect(
                str(self.db_path),
                detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES,
                timeout=20.0,
            )
            # Enable foreign key constraint enforcement
            conn.execute("PRAGMA foreign_keys = ON;")
            conn.row_factory = sqlite3.Row
            return conn
        except sqlite3.Error as e:
            logger.error(f"Failed to connect to database at {self.db_path}: {e}")
            raise

    @contextmanager
    def transaction(self) -> Generator[sqlite3.Connection, None, None]:
        """Context manager providing automatic transaction commit and rollback."""
        conn = self.get_connection()
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Transaction failed and was rolled back: {e}")
            raise
        finally:
            conn.close()

    def init_database(self) -> None:
        """Initialize database schema, indices, version tracking, and initial seed user."""
        logger.info(f"Initializing database at: {self.db_path}")
        with self.transaction() as conn:
            cursor = conn.cursor()

            # Schema versioning table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS schema_version (
                    version INTEGER PRIMARY KEY,
                    applied_at TEXT NOT NULL,
                    notes TEXT
                );
            """)

            # Users table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    created_at TEXT NOT NULL
                );
            """)

            # BMI Records table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS bmi_records (
                    record_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    weight REAL NOT NULL,
                    height REAL NOT NULL,
                    bmi REAL NOT NULL,
                    category TEXT NOT NULL,
                    recorded_at TEXT NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE
                );
            """)

            # Performance indices
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_records_user_date
                ON bmi_records (user_id, recorded_at);
            """)

            # Verify and record schema version
            cursor.execute("SELECT MAX(version) FROM schema_version;")
            row = cursor.fetchone()
            current_version = row[0] if row and row[0] is not None else 0

            if current_version < SCHEMA_VERSION:
                cursor.execute(
                    "INSERT INTO schema_version (version, applied_at, notes) VALUES (?, ?, ?);",
                    (SCHEMA_VERSION, datetime.now().isoformat(), "Initial baseline schema"),
                )
                logger.info(f"Applied database schema version {SCHEMA_VERSION}")

            # Ensure at least one default user profile exists on first run
            cursor.execute("SELECT COUNT(*) FROM users;")
            if cursor.fetchone()[0] == 0:
                cursor.execute(
                    "INSERT INTO users (username, created_at) VALUES (?, ?);",
                    ("Primary User", datetime.now().isoformat()),
                )
                logger.info("Initialized default profile: 'Primary User'")


# Global default database instance
db = DatabaseManager()
