from __future__ import annotations

from bls_escalation_mcp.repositories.series import SeriesRepository


def get_series_resource(series_id: str):
    """Return a minimal series metadata resource."""
    return SeriesRepository().get(series_id)
