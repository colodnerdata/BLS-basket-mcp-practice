"""Parser unit tests over hand-checked fixture slices of real BLS files."""

from __future__ import annotations

from decimal import Decimal

import pytest

from bls_escalation_mcp.data.flat_file import (
    FlatFileFormatError,
    parse_code_mapping,
    parse_data_file,
    parse_series_file,
)
from bls_escalation_mcp.data.ingest import classify_file


@pytest.fixture
def flat_fixtures():
    from pathlib import Path

    return Path(__file__).parent / "fixtures" / "bls" / "flatfile"


def _read(flat_fixtures, name: str) -> str:
    return flat_fixtures.joinpath(name).read_text(encoding="utf-8")


def test_pc_series_padding_and_fields(flat_fixtures) -> None:
    rows, _ = parse_series_file(_read(flat_fixtures, "pc.series.slice"), "pc")
    assert len(rows) == 2
    first = rows[0]
    assert first.series_id == "PCU1133--1133--"  # padding stripped
    assert first.industry_code == "1133--"
    assert first.seasonal_code == "U"
    assert first.base_or_bench_date == "198112"
    assert first.title == (
        "PPI industry group data for Logging, not seasonally adjusted"
    )
    assert (first.begin_year, first.begin_period) == (1981, "M12")
    assert (first.end_year, first.end_period) == (2026, "M08")


def test_pd_series_blank_extra_column(flat_fixtures) -> None:
    rows, _ = parse_series_file(_read(flat_fixtures, "pd.series.slice"), "pd")
    assert len(rows) == 2
    first = rows[0]
    assert first.series_id == "PDU1011#"
    assert first.industry_code == "1011"
    assert first.product_code == "#"
    assert first.base_or_bench_date == "8412"  # YYMM bench date
    assert first.title is None  # PD carries no titles
    assert (first.end_year, first.end_period) == (2003, "M13")


def test_pd_series_shape_drift_fails_loudly() -> None:
    pc_layout = (
        "series_id\tindustry_code\tproduct_code\tseasonal\tbench_date\t"
        "begin_year\tbegin_period\tend_year\tend_period\n"
        # pc-style row: 9 fields, no blank sixth column
        "PDU1011#\t1011\t#\tU\t8412\t1984\tM12\t2003\tM13\n"
    )
    with pytest.raises(FlatFileFormatError, match="row 2"):
        parse_series_file(pc_layout, "pd")


def test_data_file_period_identity_and_precision(flat_fixtures) -> None:
    rows, outcome = parse_data_file(
        _read(flat_fixtures, "pc.data.20.ComputerProduct.slice")
    )
    assert len(rows) == 5
    assert outcome.skipped_rows == 0
    annual = rows[1]
    assert annual.period_code == "M13"
    assert annual.month is None  # annual average, never a 13th month
    assert annual.value == Decimal("99.0")
    assert annual.year == 2004
    precise = rows[2]
    assert precise.value == Decimal("234.780")  # scale preserved exactly
    preliminary = rows[3]
    assert preliminary.footnote_codes == "P"


def test_data_file_unknown_period_is_warned_not_dropped() -> None:
    text = (
        "series_id\tyear\tperiod\tvalue\tfootnote_codes\n"
        "PCUX\t2004\tQ05\t100.0\t\n"
        "PCUX\t2004\tM01\t99.9\t\n"
    )
    rows, outcome = parse_data_file(text)
    assert [row.period_code for row in rows] == ["M01"]
    assert outcome.skipped_rows == 1
    assert outcome.warnings["Q05"] == 1  # counted for the manifest


def test_data_file_header_only_partition_is_empty_not_error() -> None:
    rows, outcome = parse_data_file(
        "series_id\tyear\tperiod\tvalue\tfootnote_codes\n"
    )
    assert rows == []
    assert outcome.skipped_rows == 0


def test_data_file_field_drift_fails_loudly() -> None:
    text = (
        "series_id\tyear\tperiod\tvalue\tfootnote_codes\n"
        "PCUX\t2004\tM01\t100.0\t\textra\n"
    )
    with pytest.raises(FlatFileFormatError, match="fields"):
        parse_data_file(text)


def test_pd_product_quirk_name_in_last_field(flat_fixtures) -> None:
    mapping, rows = parse_code_mapping(
        _read(flat_fixtures, "pd.product.slice"), key_columns=2
    )
    assert mapping["10__\t#"] == "Metal mining"
    assert mapping["2384\t#SS"] == "Secondary products"
    assert rows == 2  # header + Metal mining + the quirk row


def test_simple_mappings(flat_fixtures) -> None:
    industry, _ = parse_code_mapping(_read(flat_fixtures, "pd.industry.slice"))
    assert industry["10__"] == "Metal mining"
    footnotes, _ = parse_code_mapping(
        _read(flat_fixtures, "pc.footnote.slice")
    )
    assert footnotes["C"] == "Correction"
    assert footnotes["P"].startswith("Preliminary")


@pytest.mark.parametrize(
    "name, expected",
    [
        ("pc.series", ("pc", "series", "pc.series")),
        ("pd.series", ("pd", "series", "pd.series")),
        ("pc.industry.txt", ("pc", "mapping", "pc.industry")),
        ("pd.product", ("pd", "mapping", "pd.product")),
        (
            "pc.data.20.ComputerProduct.sample",
            ("pc", "data", "pc.data.20.ComputerProduct"),
        ),
        (
            "pd.data.20.FabricatedMetal.head",
            ("pd", "data", "pd.data.20.FabricatedMetal"),
        ),
        (
            "pc.data.20.ComputerProduct.slice",
            ("pc", "data", "pc.data.20.ComputerProduct"),
        ),
        ("pd.series.slice", ("pd", "series", "pd.series")),
    ],
)
def test_classify_file(name: str, expected: tuple[str, str, str]) -> None:
    assert classify_file(name) == expected


@pytest.mark.parametrize(
    "name", ["pc.txt", "pc.contacts", "overview.txt", "README.MD", "x.series"]
)
def test_classify_file_skips_unrecognized(name: str) -> None:
    assert classify_file(name) is None
