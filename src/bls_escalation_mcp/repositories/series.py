from __future__ import annotations

import json
import sqlite3

from bls_escalation_mcp.db.connection import db_connection
from bls_escalation_mcp.models.enums import BLSProgram
from bls_escalation_mcp.models.series import (
    SeriesMetadata,
    SeriesSearchRequest,
)


class SeriesRepository:
    """SQLite-backed repository for BLS metadata."""

    def __init__(self, database_path: str | None = None) -> None:
        self.database_path = database_path

    def _row_to_series(self, row: sqlite3.Row) -> SeriesMetadata:
        return SeriesMetadata(**json.loads(row["payload"]))

    def get(self, series_id: str) -> SeriesMetadata | None:
        with db_connection(self.database_path) as conn:
            row = conn.execute(
                "SELECT payload FROM series WHERE series_id = ?",
                (series_id,),
            ).fetchone()
        if row is None:
            return None
        return self._row_to_series(row)

    def search(self, request: SeriesSearchRequest) -> list[SeriesMetadata]:
        query = request.query.strip()
        clauses = ["1 = 1"]
        params: list[str | int] = []

        if query:
            clauses.append(
                "(title LIKE ? OR description LIKE ? "
                "OR classification_code LIKE ?)"
            )
            like = f"%{query}%"
            params.extend([like, like, like])

        if request.programs:
            placeholder = ", ".join("?" for _ in request.programs)
            clauses.append(f"program IN ({placeholder})")
            params.extend([program.value for program in request.programs])

        if request.active_only:
            clauses.append("active = 1")

        sql = (
            "SELECT payload FROM series WHERE "
            + " AND ".join(clauses)
            + " ORDER BY title LIMIT ?"
        )
        params.append(request.limit)

        with db_connection(self.database_path) as conn:
            rows = conn.execute(sql, tuple(params)).fetchall()

        return [self._row_to_series(row) for row in rows]

    def upsert(self, series: SeriesMetadata) -> SeriesMetadata:
        self.upsert_many([series])
        return series

    @staticmethod
    def _to_row(series: SeriesMetadata) -> tuple[object, ...]:
        payload = json.dumps(series.model_dump(mode="json"))
        return (
            series.series_id,
            series.program.value,
            series.title,
            series.description,
            series.classification_system,
            series.classification_code,
            series.parent_code,
            series.industry_code,
            series.commodity_code,
            series.occupation_code,
            series.geography,
            series.area_code,
            series.periodicity.value if series.periodicity else None,
            int(series.seasonal_adjustment)
            if series.seasonal_adjustment is not None
            else None,
            series.units,
            series.first_period.model_dump_json()
            if series.first_period
            else None,
            series.latest_period.model_dump_json()
            if series.latest_period
            else None,
            int(series.active) if series.active is not None else None,
            series.source_url,
            payload,
        )

    def list_by_program(self, program: BLSProgram) -> list[SeriesMetadata]:
        with db_connection(self.database_path) as conn:
            rows = conn.execute(
                "SELECT payload FROM series WHERE program = ? ORDER BY title",
                (program.value,),
            ).fetchall()
        return [self._row_to_series(row) for row in rows]

    def upsert_many(self, series_list: list[SeriesMetadata]) -> None:
        """Bulk upsert in one transaction (used by catalog ingestion)."""
        rows = [self._to_row(series) for series in series_list]
        with db_connection(self.database_path) as conn:
            conn.executemany(
                """
                INSERT INTO series (
                    series_id, program, title, description,
                    classification_system, classification_code, parent_code,
                    industry_code, commodity_code, occupation_code,
                    geography, area_code, periodicity, seasonal_adjustment,
                    units, first_period, latest_period, active, source_url,
                    payload
                ) VALUES (
                    ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
                )
                ON CONFLICT(series_id) DO UPDATE SET
                    program = excluded.program,
                    title = excluded.title,
                    description = excluded.description,
                    classification_system = excluded.classification_system,
                    classification_code = excluded.classification_code,
                    parent_code = excluded.parent_code,
                    industry_code = excluded.industry_code,
                    commodity_code = excluded.commodity_code,
                    occupation_code = excluded.occupation_code,
                    geography = excluded.geography,
                    area_code = excluded.area_code,
                    periodicity = excluded.periodicity,
                    seasonal_adjustment = excluded.seasonal_adjustment,
                    units = excluded.units,
                    first_period = excluded.first_period,
                    latest_period = excluded.latest_period,
                    active = excluded.active,
                    source_url = excluded.source_url,
                    payload = excluded.payload
                """,
                rows,
            )
            conn.commit()
