from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path

from bls_escalation_mcp.config import get_settings


def get_database_path(database_path: str | None = None) -> str:
    if database_path:
        return database_path
    return get_settings().database_path


@contextmanager
def db_connection(database_path: str | None = None):
    path = get_database_path(database_path)
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def initialize_database(database_path: str | None = None) -> None:
    """Create the initial SQLite schema for the project."""
    from bls_escalation_mcp.db.schema import initialize_schema

    initialize_schema(database_path)
