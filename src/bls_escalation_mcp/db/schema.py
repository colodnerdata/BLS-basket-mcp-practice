from __future__ import annotations

from bls_escalation_mcp.db.connection import db_connection

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS series (
    series_id TEXT PRIMARY KEY,
    program TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    classification_system TEXT,
    classification_code TEXT,
    parent_code TEXT,
    industry_code TEXT,
    commodity_code TEXT,
    occupation_code TEXT,
    geography TEXT,
    area_code TEXT,
    periodicity TEXT,
    seasonal_adjustment INTEGER,
    units TEXT,
    first_period TEXT,
    latest_period TEXT,
    active INTEGER,
    source_url TEXT,
    payload TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS observations (
    series_id TEXT NOT NULL,
    period TEXT NOT NULL,
    value TEXT NOT NULL,
    units TEXT,
    retrieved_at TEXT,
    source TEXT,
    is_preliminary INTEGER,
    footnotes TEXT,
    PRIMARY KEY (series_id, period)
);

CREATE TABLE IF NOT EXISTS saved_index_specs (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    spec_json TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
"""


def initialize_schema(database_path: str | None = None) -> None:
    with db_connection(database_path) as conn:
        conn.executescript(SCHEMA_SQL)
        conn.commit()
