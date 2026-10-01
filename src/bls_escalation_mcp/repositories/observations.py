from __future__ import annotations

from bls_escalation_mcp.db.connection import db_connection
from bls_escalation_mcp.models.observations import Observation
from bls_escalation_mcp.models.periods import EconomicPeriod


class ObservationRepository:
    """Simple observation cache for known BLS series IDs."""

    def __init__(self, database_path: str | None = None) -> None:
        self.database_path = database_path

    def save_many(self, observations: list[Observation]) -> None:
        with db_connection(self.database_path) as conn:
            for observation in observations:
                conn.execute(
                    """
                    INSERT INTO observations (
                        series_id, period, value, units, retrieved_at, source,
                        is_preliminary, footnotes
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(series_id, period) DO UPDATE SET
                        value = excluded.value,
                        units = excluded.units,
                        retrieved_at = excluded.retrieved_at,
                        source = excluded.source,
                        is_preliminary = excluded.is_preliminary,
                        footnotes = excluded.footnotes
                    """,
                    (
                        observation.series_id,
                        str(observation.period),
                        str(observation.value),
                        observation.units,
                        observation.retrieved_at.isoformat(),
                        observation.source,
                        int(observation.is_preliminary)
                        if observation.is_preliminary is not None
                        else None,
                        "|".join(observation.footnotes),
                    ),
                )
            conn.commit()

    def get_series_observations(
        self,
        series_id: str,
        start_period: EconomicPeriod | None = None,
        end_period: EconomicPeriod | None = None,
    ) -> list[Observation]:
        # TODO: add explicit vintage management.
        with db_connection(self.database_path) as conn:
            rows = conn.execute(
                "SELECT series_id, period, value, units, "
                "retrieved_at, source, is_preliminary, footnotes "
                "FROM observations WHERE series_id = ? ORDER BY period",
                (series_id,),
            ).fetchall()

        observations: list[Observation] = []
        for row in rows:
            observations.append(
                Observation(
                    series_id=row["series_id"],
                    period=EconomicPeriod.from_storage(row["period"]),
                    value=row["value"],
                    units=row["units"],
                    retrieved_at=row["retrieved_at"],
                    source=row["source"],
                    is_preliminary=bool(row["is_preliminary"])
                    if row["is_preliminary"] is not None
                    else None,
                    footnotes=[]
                    if not row["footnotes"]
                    else row["footnotes"].split("|"),
                )
            )
        return [
            observation
            for observation in observations
            if (start_period is None or not observation.period < start_period)
            and (end_period is None or not end_period < observation.period)
        ]
