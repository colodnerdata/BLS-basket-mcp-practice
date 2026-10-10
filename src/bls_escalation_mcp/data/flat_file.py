"""Parsers for BLS flat files under ``download.bls.gov/pub/time.series``.

Format facts verified 2026-10-10 against the owner-saved samples in
``docs/sample_data/``; the full findings live in ``docs/bulk_files.md``.
Only the PC and PD layouts are supported:

- tab-separated values, CRLF line endings, header row first;
- every field is space-padded and must be stripped before use;
- period codes are ``M01``-``M12`` plus ``M13`` — an annual *average*, not
  a thirteenth month, and never mixed into a monthly window;
- values are ``Decimal`` with a variable scale (one decimal through
  2021-M06 for PC, three after);
- ``pd.series`` rows have one more field than their header (a blank,
  space-filled column between ``bench_date`` and ``begin_year``);
- PC series titles live in ``pc.series``; PD has none — titles come from
  the ``pd.industry``/``pd.product`` mapping files.

Parsers never fabricate or substitute: unknown period codes are skipped
with a counted warning, and structural drift raises
:class:`FlatFileFormatError` loudly. Other programs (ECI ``ci``, OEWS
``oe``, commodities ``wp``) land with their own parsers when scheduled.
"""

from __future__ import annotations

import re
from collections import Counter
from collections.abc import Iterator
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from typing import Literal

FlatFileProgram = Literal["pc", "pd"]

PC_DIR_URL = "https://download.bls.gov/pub/time.series/pc/"
PD_DIR_URL = "https://download.bls.gov/pub/time.series/pd/"
PROGRAM_DIR_URLS: dict[str, str] = {"pc": PC_DIR_URL, "pd": PD_DIR_URL}

_MONTHLY_CODE = re.compile(r"^M(\d{2})$")
ANNUAL_AVERAGE_CODE = "M13"


class FlatFileFormatError(ValueError):
    """A flat file's structure drifted from the verified layout."""


@dataclass(frozen=True)
class ParsedSeries:
    """One row of an ``xx.series`` file, padding stripped."""

    series_id: str
    industry_code: str
    product_code: str
    seasonal_code: str
    base_or_bench_date: str
    title: str | None  # PC carries one; PD does not.
    begin_year: int
    begin_period: str
    end_year: int
    end_period: str


@dataclass(frozen=True)
class ParsedObservation:
    """One row of an ``xx.data.*`` file, padding stripped."""

    series_id: str
    year: int
    period_code: str
    month: int | None  # None exactly when the row is the M13 annual average
    value: Decimal
    footnote_codes: str  # raw, space-separated codes; "" when blank


@dataclass
class ParseOutcome:
    """Parsed rows plus non-fatal findings, for manifest accounting."""

    warnings: Counter[str] = field(default_factory=Counter)
    skipped_rows: int = 0


PC_SERIES_COLUMNS = (
    "series_id",
    "industry_code",
    "product_code",
    "seasonal",
    "base_date",
    "series_title",
    "footnote_codes",
    "begin_year",
    "begin_period",
    "end_year",
    "end_period",
)
# pd.series' header names 9 columns; its rows have 10 fields, the sixth a
# space-filled blank between bench_date and begin_year.
PD_BLANK_FIELD_INDEX = 5


def _tsv_rows(text: str) -> Iterator[list[str]]:
    for line in text.splitlines():
        if line.strip():
            yield line.split("\t")


def _header_and_rows(
    text: str, file_label: str
) -> tuple[list[str], list[list[str]]]:
    parts = list(_tsv_rows(text))
    if not parts:
        raise FlatFileFormatError(f"{file_label}: file has no header row")
    return [cell.strip() for cell in parts[0]], parts[1:]


def _require_int(value: str, field_name: str, file_label: str) -> int:
    try:
        return int(value.strip())
    except ValueError as exc:
        raise FlatFileFormatError(
            f"{file_label}: {field_name} is not an integer: {value!r}"
        ) from exc


def parse_series_file(
    text: str, program: FlatFileProgram, file_label: str = "series file"
) -> tuple[list[ParsedSeries], ParseOutcome]:
    """Parse an ``xx.series`` file (PC by header name; PD positionally).

    PD's extra blank column is handled explicitly; any other shape drift
    raises :class:`FlatFileFormatError` rather than misreading columns.
    """
    header, rows = _header_and_rows(text, file_label)
    outcome = ParseOutcome()
    parsed: list[ParsedSeries] = []
    if program == "pc":
        if sorted(header) != sorted(PC_SERIES_COLUMNS):
            raise FlatFileFormatError(
                f"{file_label}: pc series header {header!r} does not match "
                f"the verified columns {list(PC_SERIES_COLUMNS)!r}"
            )
        index = {name: header.index(name) for name in PC_SERIES_COLUMNS}
        for row_number, row in enumerate(rows, start=2):
            if len(row) != len(header):
                raise FlatFileFormatError(
                    f"{file_label} row {row_number}: {len(row)} fields, "
                    f"expected {len(header)}"
                )
            cell = [value.strip() for value in row]
            parsed.append(
                ParsedSeries(
                    series_id=cell[index["series_id"]],
                    industry_code=cell[index["industry_code"]],
                    product_code=cell[index["product_code"]],
                    seasonal_code=cell[index["seasonal"]],
                    base_or_bench_date=cell[index["base_date"]],
                    title=cell[index["series_title"]] or None,
                    begin_year=_require_int(
                        cell[index["begin_year"]], "begin_year", file_label
                    ),
                    begin_period=cell[index["begin_period"]],
                    end_year=_require_int(
                        cell[index["end_year"]], "end_year", file_label
                    ),
                    end_period=cell[index["end_period"]],
                )
            )
    else:  # pd
        expected = (
            "series_id",
            "industry_code",
            "product_code",
            "seasonal",
            "bench_date",
            "begin_year",
            "begin_period",
            "end_year",
            "end_period",
        )
        if list(header) != list(expected):
            raise FlatFileFormatError(
                f"{file_label}: pd series header {header!r} does not match "
                f"the verified columns {list(expected)!r}"
            )
        for row_number, row in enumerate(rows, start=2):
            if not (
                len(row) == len(header) + 1
                and not row[PD_BLANK_FIELD_INDEX].strip()
            ):
                raise FlatFileFormatError(
                    f"{file_label} row {row_number}: pd rows must have "
                    f"{len(header) + 1} fields with a blank column at index "
                    f"{PD_BLANK_FIELD_INDEX}; got {len(row)} fields"
                )
            cell = [
                value.strip()
                for position, value in enumerate(row)
                if position != PD_BLANK_FIELD_INDEX
            ]
            parsed.append(
                ParsedSeries(
                    series_id=cell[0],
                    industry_code=cell[1],
                    product_code=cell[2],
                    seasonal_code=cell[3],
                    base_or_bench_date=cell[4],
                    title=None,
                    begin_year=_require_int(cell[5], "begin_year", file_label),
                    begin_period=cell[6],
                    end_year=_require_int(cell[7], "end_year", file_label),
                    end_period=cell[8],
                )
            )
    return parsed, outcome


def parse_data_file(
    text: str, file_label: str = "data file"
) -> tuple[list[ParsedObservation], ParseOutcome]:
    """Parse an ``xx.data.*`` partition.

    ``M13`` rows are kept with ``month=None`` and never misfiled as a
    month; any other unknown period code is skipped with a counted
    warning (surfaced to the manifest) rather than silently dropped.
    Header-only (empty) partitions are valid and yield zero rows.
    """
    header, rows = _header_and_rows(text, file_label)
    expected = ("series_id", "year", "period", "value", "footnote_codes")
    if list(header) != list(expected):
        raise FlatFileFormatError(
            f"{file_label}: data header {header!r} does not match the "
            f"verified columns {list(expected)!r}"
        )
    outcome = ParseOutcome()
    parsed: list[ParsedObservation] = []
    for row_number, row in enumerate(rows, start=2):
        if len(row) != len(header):
            raise FlatFileFormatError(
                f"{file_label} row {row_number}: {len(row)} fields, "
                f"expected {len(header)}"
            )
        series_id, year_text, period, value_text, footnotes = (
            value.strip() for value in row
        )
        match = _MONTHLY_CODE.match(period)
        if match is None:
            outcome.warnings[period] += 1
            outcome.skipped_rows += 1
            continue
        month = int(match.group(1))
        if not 1 <= month <= 13:
            outcome.warnings[period] += 1
            outcome.skipped_rows += 1
            continue
        try:
            value = Decimal(value_text)
        except InvalidOperation as exc:
            raise FlatFileFormatError(
                f"{file_label} row {row_number}: value {value_text!r} is "
                f"not a decimal for {series_id} {year_text}-{period}"
            ) from exc
        if not value.is_finite():
            raise FlatFileFormatError(
                f"{file_label} row {row_number}: non-finite value "
                f"{value_text!r} for {series_id} {year_text}-{period}"
            )
        parsed.append(
            ParsedObservation(
                series_id=series_id,
                year=_require_int(year_text, "year", file_label),
                period_code=period,
                month=None if month == 13 else month,
                value=value,
                footnote_codes=footnotes,
            )
        )
    return parsed, outcome


def parse_code_mapping(
    text: str, file_label: str = "mapping file", key_columns: int = 1
) -> tuple[dict[str, str], int]:
    """Parse a code mapping into ``{"code\t...": "name"}`` plus a row count.

    The key is the first ``key_columns`` fields (2 for ``xx.product`` files,
    which are keyed by ``(industry_code, product_code)``) and the name is
    the **last** field: ``pd.product`` has rows with extra tab fields where
    the name sits at the end (see ``docs/bulk_files.md``), so a fixed name
    position would misparse them. Rows with a blank key or name are skipped
    without failing; blank cells inside the key are kept as empty segments.
    """
    header, rows = _header_and_rows(text, file_label)
    if len(header) < key_columns + 1:
        raise FlatFileFormatError(
            f"{file_label}: mapping header needs at least "
            f"{key_columns + 1} columns, got {header!r}"
        )
    mapping: dict[str, str] = {}
    for row_number, row in enumerate(rows, start=2):
        if len(row) < key_columns + 1:
            raise FlatFileFormatError(
                f"{file_label} row {row_number}: {len(row)} fields, "
                f"expected at least {key_columns + 1}"
            )
        key = "\t".join(value.strip() for value in row[:key_columns])
        name = row[-1].strip()
        if name and any(key.split("\t")):
            mapping.setdefault(key, name)
    return mapping, len(rows)
