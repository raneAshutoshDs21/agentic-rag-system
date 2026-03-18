"""Database package — exports SQLite manager."""

from database.sqlite_db import SQLiteDB, sqlite_db

__all__ = [
    "SQLiteDB",
    "sqlite_db",
]