"""Regression cases for the actionable findings on PR #1."""

from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

import pytest

from bls_escalation_mcp.clients.bls import BLSClient
from bls_escalation_mcp.data.loaders.eci import ECILoader
from bls_escalation_mcp.data.loaders.oews import OEWSLoader
from bls_escalation_mcp.data.loaders.ppi import PPILoader
from bls_escalation_mcp.db.connection import initialize_database
from bls_escalation_mcp.exceptions import BLSAPIError
from bls_escalation_mcp.models.enums import Periodicity
from bls_escalation_mcp.models.observations import Observation
from bls_escalation_mcp.models.periods import EconomicPeriod
from bls_escalation_mcp.repositories.observations import ObservationRepository


@pytest.mark.parametrize("value", [None, "", "-", "NaN", "Infinity"])
def test_missing_observations_are_rejected(value: str | None) -> None:
    with pytest.raises(BLSAPIError, match="Missing or non-numeric"):
        BLSClient.parse_response(
            {
                "Results": {
                    "series": [
                        {
                            "seriesID": "FIXTURE",
                            "data": [
                                {
                                    "year": "2024",
                                    "period": "M01",
                                    "value": value,
                                }
                            ],
                        }
                    ]
                }
            }
        )


def test_actual_zero_is_preserved() -> None:
    observations = BLSClient.parse_response(
        {
            "Results": {
                "series": [
                    {
                        "seriesID": "FIXTURE",
                        "data": [
                            {
                                "year": "2024",
                                "period": "M01",
                                "value": "0",
                            }
                        ],
                    }
                ]
            }
        }
    )
    assert observations[0].value == Decimal(0)


@pytest.mark.parametrize("loader", [PPILoader, ECILoader, OEWSLoader])
def test_deferred_loaders_return_no_fabricated_metadata(loader: type) -> None:
    assert loader().parse_metadata([]) == []
    assert loader().parse_metadata([{"unmapped": "value"}]) == []


@pytest.mark.parametrize(
    "period",
    [
        EconomicPeriod(year=2024, month=1, periodicity=Periodicity.MONTHLY),
        EconomicPeriod(
            year=2024, quarter=3, periodicity=Periodicity.QUARTERLY
        ),
        EconomicPeriod(year=2024, periodicity=Periodicity.ANNUAL),
        EconomicPeriod(year=2024, periodicity=Periodicity.ANNUAL_AVERAGE),
    ],
)
def test_observation_cache_preserves_period_identity(
    tmp_path: Path,
    period: EconomicPeriod,
) -> None:
    path = str(tmp_path / "observations.db")
    initialize_database(path)
    repository = ObservationRepository(path)
    observation = Observation(
        series_id="FIXTURE",
        period=period,
        value=Decimal("123.45"),
        units="index",
        retrieved_at=datetime.now(UTC),
        source="fixture",
        footnotes=["Test note"],
        is_preliminary=None,
    )
    repository.save_many([observation])
    restored = repository.get_series_observations("FIXTURE")
    assert restored == [observation]


def test_annual_and_annual_average_do_not_overwrite(tmp_path: Path) -> None:
    path = str(tmp_path / "observations.db")
    initialize_database(path)
    repository = ObservationRepository(path)
    periods = [
        EconomicPeriod(year=2024, periodicity=p)
        for p in (
            Periodicity.ANNUAL,
            Periodicity.ANNUAL_AVERAGE,
        )
    ]
    repository.save_many(
        [
            Observation(
                series_id="FIXTURE",
                period=period,
                value=Decimal(100),
                retrieved_at=datetime.now(UTC),
                source="fixture",
            )
            for period in periods
        ]
    )
    assert [
        o.period for o in repository.get_series_observations("FIXTURE")
    ] == periods


def test_observation_decimal_text_is_exact() -> None:
    text = "123.45678901234567890123456789"
    observations = BLSClient.parse_response(
        {
            "Results": {
                "series": [
                    {
                        "seriesID": "FIXTURE",
                        "data": [
                            {
                                "year": "2024",
                                "period": "M01",
                                "value": text,
                            }
                        ],
                    }
                ]
            }
        }
    )
    assert observations[0].value == Decimal(text)
    assert observations[0].model_dump(mode="json")["value"] == text
