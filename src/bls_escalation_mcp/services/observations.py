from __future__ import annotations

from bls_escalation_mcp.models.observations import (
    Observation,
    SeriesObservations,
)


class ObservationService:
    """Thin observation service for the initial scaffold."""

    def store_many(self, observations: list[Observation]) -> None:
        raise NotImplementedError(
            "Observation persistence is scaffolded but not yet fully "
            "implemented."
        )

    def get_series_observations(
        self,
        series_id: str,
        start_period=None,
        end_period=None,
    ) -> SeriesObservations:
        raise NotImplementedError(
            "Observation retrieval is scaffolded but not yet fully "
            "implemented."
        )
