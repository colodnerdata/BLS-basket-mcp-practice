"""Parser unit tests over hand-checked fixture slices of real BLS files."""

from __future__ import annotations

from decimal import Decimal

import pytest

from bls_escalation_mcp.data.flat_file import (
    FlatFileFormatError,
    eci_is_index,
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
    assert len(rows) == 4
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


def test_wp_series_file_parse(flat_fixtures) -> None:
    rows, _ = parse_series_file(_read(flat_fixtures, "wp.series.slice"), "wp")
    assert len(rows) == 6
    lumber = rows[0]
    assert lumber.series_id == "WPS0811"  # padding stripped
    assert lumber.industry_code == "08"  # Lumber and wood products
    assert lumber.product_code == "11"  # Softwood lumber
    assert lumber.seasonal_code == "S"
    assert lumber.base_or_bench_date == "198200"  # YYMM
    assert "Softwood lumber" in (lumber.title or "")
    assert (lumber.begin_year, lumber.begin_period) == (1975, "M01")
    assert (lumber.end_year, lumber.end_period) == (2026, "M08")
    # Ended series are in the file (WP->WD migration); identity kept.
    retired = {row.series_id for row in rows}
    assert "WPS00000000" in retired  # All commodities ended 1974-M12
    assert "WPS1371" in retired  # gypsum item ended 2019
    # The undocumented 11th column (footnote_codes) is handled, and its
    # absence (wp.txt §4 lists 10 fields) fails loudly:
    doc_layout = (
        "series_id\tgroup_code\titem_code\tseasonal\tbase_date\t"
        "series_title\tbegin_year\tbegin_period\tend_year\tend_period\n"
        "WPS000\t01\t11\tS\t198200\tx\t1975\tM01\t2026\tM08\n"
    )
    with pytest.raises(FlatFileFormatError, match="header"):
        parse_series_file(doc_layout, "wp")


def test_wp_mappings(flat_fixtures) -> None:
    items, _ = parse_code_mapping(
        _read(flat_fixtures, "wp.item.slice"), key_columns=2
    )
    assert items["08\t11"] == "Softwood lumber"
    assert items["10\t17"] == "Steel mill products"
    groups, _ = parse_code_mapping(_read(flat_fixtures, "wp.group.slice"))
    assert groups["08"] == "Lumber and wood products"
    assert groups["13"] == "Nonmetallic mineral products"


def test_ci_series_file_parse(flat_fixtures) -> None:
    rows, _ = parse_series_file(_read(flat_fixtures, "ci.series.slice"), "ci")
    assert len(rows) == 4
    construction = rows[3]
    assert construction.series_id == "CIS2022300000000I"
    assert construction.owner_code == "2"  # private industry
    assert construction.industry_code == "230000"  # construction
    assert construction.periodicity_code == "I"
    assert construction.estimate_code == "02"  # wages and salaries
    assert "Wages and salaries" in (construction.title or "")
    assert (construction.begin_year, construction.begin_period) == (
        2001,
        "Q01",
    )
    assert (construction.end_year, construction.end_period) == (2026, "Q02")


def test_ci_index_eligibility_gate(flat_fixtures) -> None:
    rows, _ = parse_series_file(_read(flat_fixtures, "ci.series.slice"), "ci")
    eligible = [row.series_id for row in rows if eci_is_index(row)]
    assert eligible == [
        "CIS1010000000000I",
        "CIS2012300000000I",
        "CIS2022300000000I",
    ]
    # The 3-month percent-change twin must never reach the catalog.
    assert "CIS1010000000000Q" not in eligible


def test_ci_mappings(flat_fixtures) -> None:
    # CI mapping files keep the name in column 2 with trailing display
    # metadata, so callers pass name_column=1 (last-field would grab
    # sort_sequence).
    periodicity, _ = parse_code_mapping(
        _read(flat_fixtures, "ci.periodicity.slice"), name_column=1
    )
    assert periodicity["I"] == "Current dollar index number"
    assert periodicity["Q"].startswith("3-month percent change")
    estimate, _ = parse_code_mapping(
        _read(flat_fixtures, "ci.estimate.slice"), name_column=1
    )
    assert estimate["01"] == "Total compensation"
    owner, _ = parse_code_mapping(
        _read(flat_fixtures, "ci.owner.slice"), name_column=1
    )
    assert owner["2"] == "Private industry workers"


def test_data_file_quarterly_periods() -> None:
    text = (
        "series_id\tyear\tperiod\tvalue\tfootnote_codes\n"
        "CIS2022300000000I\t2001\tQ01\t135.0\t\n"
        "CIS2022300000000I\t2001\tQ05\t135.0\t\n"
    )
    rows, outcome = parse_data_file(text)
    assert len(rows) == 1
    assert rows[0].quarter == 1
    assert rows[0].month is None
    # Q05 (and every other out-of-range code) is skipped with a count.
    assert outcome.skipped_rows == 1
    assert outcome.warnings["Q05"] == 1


def test_data_file_missing_dash_is_recorded() -> None:
    text = (
        "series_id\tyear\tperiod\tvalue\tfootnote_codes\n"
        "CIS2022300000000I\t2001\tQ01\t-\tA\n"
        "CIS2022300000000I\t2001\tQ02\t135.0\t\n"
    )
    rows, outcome = parse_data_file(text)
    # The dash sentinel (CI footnote A) is not an observation: skipped and
    # counted, never fabricated; the period simply resolves as missing in
    # any later calculation.
    assert len(rows) == 1
    assert outcome.missing_rows == 1
    # A genuinely malformed value (not the sentinel) still raises.
    with pytest.raises(FlatFileFormatError, match="not a decimal"):
        parse_data_file(
            "series_id\tyear\tperiod\tvalue\tfootnote_codes\n"
            "CIS2022300000000I\t2001\tQ01\tabc\t\n"
        )


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
        ("ci.series", ("ci", "series", "ci.series")),
        ("ci.periodicity.slice", ("ci", "mapping", "ci.periodicity")),
        ("ci.data.0.Current", ("ci", "data", "ci.data.0.Current")),
        ("wp.series", ("wp", "series", "wp.series")),
        ("wp.item.slice", ("wp", "mapping", "wp.item")),
        ("wp.group", ("wp", "mapping", "wp.group")),
        ("wp.data.9.Lumber", ("wp", "data", "wp.data.9.Lumber")),
    ],
)
def test_classify_file(name: str, expected: tuple[str, str, str]) -> None:
    assert classify_file(name) == expected


@pytest.mark.parametrize(
    "name",
    [
        "pc.txt",
        "pc.contacts",
        "overview.txt",
        "README.MD",
        "x.series",
        "ci.aspect",
        "pc_headers_probe.json",
    ],
)
def test_classify_file_skips_unrecognized(name: str) -> None:
    assert classify_file(name) is None
