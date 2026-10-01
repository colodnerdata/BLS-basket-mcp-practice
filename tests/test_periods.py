from bls_escalation_mcp.models.enums import Periodicity
from bls_escalation_mcp.models.periods import EconomicPeriod


def test_valid_monthly_period() -> None:
    period = EconomicPeriod(
        year=2025,
        month=3,
        periodicity=Periodicity.MONTHLY,
    )
    assert str(period) == "2025-M03"


def test_valid_quarterly_period() -> None:
    period = EconomicPeriod(
        year=2025,
        quarter=2,
        periodicity=Periodicity.QUARTERLY,
    )
    assert str(period) == "2025-Q2"


def test_valid_annual_period() -> None:
    period = EconomicPeriod(year=2025, periodicity=Periodicity.ANNUAL)
    assert str(period) == "2025"


def test_invalid_period_combinations() -> None:
    try:
        EconomicPeriod(
            year=2025,
            month=3,
            quarter=2,
            periodicity=Periodicity.MONTHLY,
        )
    except ValueError:
        return
    raise AssertionError("month and quarter should not be both set")


def test_period_ordering() -> None:
    earlier = EconomicPeriod(
        year=2024,
        month=12,
        periodicity=Periodicity.MONTHLY,
    )
    later = EconomicPeriod(
        year=2025,
        month=1,
        periodicity=Periodicity.MONTHLY,
    )
    assert earlier < later
