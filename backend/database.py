import os
import sqlite3
from pathlib import Path

from dotenv import load_dotenv


BACKEND_DIRECTORY = Path(__file__).resolve().parent
DATABASE_PATH = BACKEND_DIRECTORY / "data" / "job_board.db"
load_dotenv(BACKEND_DIRECTORY / ".env")


class DatabaseRow(dict):
    """Support the existing row['column'] and row[0] access styles."""

    def __getitem__(self, key):
        if isinstance(key, int):
            return list(self.values())[key]
        return super().__getitem__(key)


class DatabaseCursor:
    def __init__(self, cursor):
        self.cursor = cursor

    def fetchone(self):
        row = self.cursor.fetchone()
        return DatabaseRow(row) if row is not None else None

    def fetchall(self):
        return [DatabaseRow(row) for row in self.cursor.fetchall()]

    def __iter__(self):
        return (DatabaseRow(row) for row in self.cursor)


class DatabaseConnection:
    def __init__(self, connection, is_postgres: bool):
        self.connection = connection
        self.is_postgres = is_postgres

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if exc_type is None:
            self.connection.commit()
        else:
            self.connection.rollback()
        self.connection.close()

    def _prepare_query(self, query: str) -> str:
        return query.replace("?", "%s") if self.is_postgres else query

    def execute(self, query: str, parameters=None) -> DatabaseCursor:
        cursor = self.connection.execute(self._prepare_query(query), parameters or [])
        return DatabaseCursor(cursor)

    def executemany(self, query: str, parameter_sets) -> DatabaseCursor:
        cursor = self.connection.cursor()
        cursor.executemany(self._prepare_query(query), parameter_sets)
        return DatabaseCursor(cursor)


def get_connection() -> DatabaseConnection:
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        import psycopg
        from psycopg.rows import dict_row

        connection = psycopg.connect(database_url, row_factory=dict_row)
        return DatabaseConnection(connection, is_postgres=True)

    DATABASE_PATH.parent.mkdir(exist_ok=True)
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    return DatabaseConnection(connection, is_postgres=False)


def initialize_database() -> None:
    with get_connection() as connection:
        if connection.is_postgres:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS jobs (
                    id BIGSERIAL PRIMARY KEY,
                    source_job_id TEXT,
                    title TEXT NOT NULL,
                    company TEXT NOT NULL,
                    source TEXT NOT NULL,
                    location TEXT NOT NULL,
                    category TEXT NOT NULL,
                    min_experience INTEGER,
                    max_experience INTEGER,
                    experience_label TEXT NOT NULL,
                    description TEXT NOT NULL,
                    posted_at TEXT,
                    skills_json TEXT NOT NULL,
                    ai_skills_json TEXT,
                    ai_category TEXT,
                    ai_domain TEXT,
                    ai_experience TEXT,
                    duplicate_key TEXT NOT NULL UNIQUE,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            for column_name in ("ai_skills_json", "ai_category", "ai_domain", "ai_experience"):
                connection.execute(f"ALTER TABLE jobs ADD COLUMN IF NOT EXISTS {column_name} TEXT")
        else:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS jobs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_job_id TEXT,
                    title TEXT NOT NULL,
                    company TEXT NOT NULL,
                    source TEXT NOT NULL,
                    location TEXT NOT NULL,
                    category TEXT NOT NULL,
                    min_experience INTEGER,
                    max_experience INTEGER,
                    experience_label TEXT NOT NULL,
                    description TEXT NOT NULL,
                    posted_at TEXT,
                    skills_json TEXT NOT NULL,
                    ai_skills_json TEXT,
                    ai_category TEXT,
                    ai_domain TEXT,
                    ai_experience TEXT,
                    duplicate_key TEXT NOT NULL UNIQUE,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            existing_columns = {
                row["name"] for row in connection.execute("PRAGMA table_info(jobs)")
            }
            for column_name in ("ai_skills_json", "ai_category", "ai_domain", "ai_experience"):
                if column_name not in existing_columns:
                    connection.execute(f"ALTER TABLE jobs ADD COLUMN {column_name} TEXT")

        connection.execute("CREATE INDEX IF NOT EXISTS idx_jobs_source ON jobs(source)")
        connection.execute("CREATE INDEX IF NOT EXISTS idx_jobs_category ON jobs(category)")
