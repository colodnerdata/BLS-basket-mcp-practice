"""Parsers for BLS flat files under ``download.bls.gov/pub/time.series``.

Format facts verified 2026-10-10 against the owner-saved samples in
``docs/sample_data/``; the full findings live in ``docs/bulk_files.md``.
Supported layouts, each verified against real files:

- **PC/PD (PPI):** tab-separated, CRLF, header row first; every field
  space-padded and stripped before use; periods ``M01``-``M12`` plus
  ``M13`` — an annual *average*, not a thirteenth month; ``Decimal``
  values with variable scale; ``pd.series`` rows carry one extra blank
  column (handled explicitly); PC series carry titles, PD needs the
  mapping files.
- **CI (ECI):** TSV, padded, 15-column series file with real titles;
  data periods ``Q01``-``Q04`` **only — no annual-average period code
  exists**; the series' ``periodicity_code`` (the `series_id`'s final
  character) picks the measure: ``I`` is a current-dollar index (base
  December 2005 = 100) and Q/A/B/C/D/P/R/S/T/X/Z are percent changes,
  constant-dollar indexes, or response rates — only ``I`` is a valid
  escalation input, so :func:`eci_is_index` gates ingestion eligibility
  and everything else is skipped with a recorded count.
- CI missing data is a dash (footnote code ``A``); a ``-`` value must
  raise rather than parse as a number.

Parsers never fabricate or substitute: unknown period codes are skipped
with a counted warning, and structural drift raises
:class:`FlatFileFormatError` loudly. Other programs (OEWS ``oe``,
commodities ``wp``) land with their own parsers when scheduled.
"""

from __future__ import annotations

import re
from collections import Counter
from collections.abc import Iterator
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from typing import Literal

FlatFileProgram = Literal["pc", "pd", "ci"]

PROGRAM_DIR_URLS: dict[str, str] = {
    program: f"https://download.bls.gov/pub/time.series/{program}/"
    for program in ("pc", "pd", "ci")
}

_MONTHLY_CODE = re.compile(r"^M(\d{2})$")
_QUARTERLY_CODE = re.compile(r"^Q(\d{2})$")


class FlatFileFormatError(ValueError):
    """A flat file's structure drifted from the verified layout."""


@dataclass(frozen=True)
class ParsedSeries:
    """One row of an ``xx.series`` file, padding stripped.

    The ECI dimension fields are ``None`` for PC/PD; PD has no ``title``.
    """

    series_id: str
    industry_code: str
    product_code: str
    seasonal_code: str
    base_or_bench_date: str  # PC YYYYMM base date; PD YYMM bench; CI ""
    title: str | None
    begin_year: int
    begin_period: str
    end_year: int
    end_period: str
    footnote_codes: str = ""
    owner_code: str | None = None
    occupation_code: str | None = None
    subcell_code: str | None = None
    area_code: str | None = None
    periodicity_code: str | None = None
    estimate_code: str | None = None


@dataclass(frozen=True)
class ParsedObservation:
    """One row of an ``xx.data.*`` file, padding stripped."""

    series_id: str
    year: int
    period_code: str
    month: int | None  # None for M13 (annual average) and quarterly rows
    quarter: int | None
    value: Decimal
    footnote_codes: str  # raw, space-separated codes; "" when blank


@dataclass
class ParseOutcome:
    """Parsed-row plus non-fatal findings, for manifest accounting."""

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

CI_SERIES_COLUMNS = (
    "series_id",
    "seasonal",
    "owner_code",
    "industry_code",
    "occupation_code",
    "subcell_code",
    "area_code",
    "periodicity_code",
    "estimate_code",
    "series_title",
    "footnote_codes",
    "begin_year",
    "begin_period",
    "end_year",
    "end_period",
)


def eci_is_index(series: ParsedSeries) -> bool:
    """ECI ingestion eligibility: only current-dollar index levels.

    Every other periodicity code is a percent change, a constant-dollar
    index, or a response rate — none are ratio-scale escalation inputs
    (see the CI section of docs/bulk_files.md and the M3 conventions).
    """
    return series.periodicity_code == "I"


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
    """Parse an ``xx.series`` file for PC, PD, or CI.

    PC and CI are read by header name (header drift fails loudly); PD's
    extra blank column is handled explicitly and any other shape raises.
    Eligibility filtering (e.g. ECI index-only) is the caller's job; the
    parser returns every row.
    """
    header, rows = _header_and_rows(text, file_label)
    outcome = ParseOutcome()
    parsed: list[ParsedSeries] = []
    if program == "pc":
        if sorted(header) != sorted(PC_SERIES_COLUMNS):
            raise FlatFileFormatError(
                f"{file_label}: pc series header {header!r} does not "
                f"match the verified columns {list(PC_SERIES_COLUMNS)!r}"
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
                    footnote_codes=cell[index["footnote_codes"]],
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
    elif program == "ci":
        if sorted(header) != sorted(CI_SERIES_COLUMNS):
            raise FlatFileFormatError(
                f"{file_label}: ci series header {header!r} does not "
                f"match the verified columns {list(CI_SERIES_COLUMNS)!r}"
            )
        index = {name: header.index(name) for name in CI_SERIES_COLUMNS}
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
                    product_code="",
                    seasonal_code=cell[index["seasonal"]],
                    base_or_bench_date="",
                    title=cell[index["series_title"]] or None,
                    footnote_codes=cell[index["footnote_codes"]],
                    begin_year=_require_int(
                        cell[index["begin_year"]], "begin_year", file_label
                    ),
                    begin_period=cell[index["begin_period"]],
                    end_year=_require_int(
                        cell[index["end_year"]], "end_year", file_label
                    ),
                    end_period=cell[index["end_period"]],
                    owner_code=cell[index["owner_code"]],
                    occupation_code=cell[index["occupation_code"]],
                    subcell_code=cell[index["subcell_code"]],
                    area_code=cell[index["area_code"]],
                    periodicity_code=cell[index["periodicity_code"]],
                    estimate_code=cell[index["estimate_code"]],
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
                f"{file_label}: pd series header {header!r} does not "
                f"match the verified columns {list(expected)!r}"
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
    """Parse an ``xx.data.*`` partition (monthly ``M01``-``M13`` or
    quarterly ``Q01``-``Q04``).

    ``M13`` rows keep the annual-average identity (``month=None``);
    quarterly rows carry ``quarter`` with ``month=None``; any other code
    is skipped with a counted warning (surfaced to the manifest) rather
    than silently dropped. Header-only (empty) partitions are valid and
    yield zero rows. A missing (dash) or non-decimal value raises.
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
        month: int | None = None
        quarter: int | None = None
        if match := _MONTHLY_CODE.match(period):
            number = int(match.group(1))
            if 1 <= number <= 12:
                month = number
            elif number == 13:
                pass  # annual average: month stays None
            else:
                outcome.warnings[period] += 1
                outcome.skipped_rows += 1
                continue
        elif match := _QUARTERLY_CODE.match(period):
            number = int(match.group(1))
            if 1 <= number <= 4:
                quarter = number
            else:
                outcome.warnings[period] += 1
                outcome.skipped_rows += 1
                continue
        else:
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
                month=month,
                quarter=quarter,
                value=value,
                footnote_codes=footnotes,
            )
        )
    return parsed, outcome


def parse_code_mapping(
    text: str,
    file_label: str = "mapping file",
    key_columns: int = 1,
    name_column: int | None = None,
) -> tuple[dict[str, str], int]:
    """Parse a code mapping into ``{"code\t...": "name"}`` plus a row count.

    The key is the first ``key_columns`` fields (2 for ``xx.product`` files,
    which are keyed by ``(industry_code, product_code)``). The name column
    differs by program's verified layout: CI mapping files keep the name in
    the **second** column followed by display metadata (pass
    ``name_column=1``), while ``pd.product`` has rows with extra tab fields
    whose name sits at the end (the default last-field rule).
    Rows with a blank key or name are skipped without failing.
    """
    header, rows = _header_and_rows(text, file_label)
    name_index = -1 if name_column is None else name_column
    needed = max(key_columns + 1, 2 if name_index == -1 else name_index + 1)
    if len(header) < needed:
        raise FlatFileFormatError(
            f"{file_label}: mapping header needs at least {needed} "
            f"columns, got {header!r}"
        )
    mapping: dict[str, str] = {}
    for row_number, row in enumerate(rows, start=2):
        if len(row) < needed:
            raise FlatFileFormatError(
                f"{file_label} row {row_number}: {len(row)} fields, "
                f"expected at least {needed}"
            )
        key = "\t".join(value.strip() for value in row[:key_columns])
        name = row[name_index].strip()
        if name and any(key.split("\t")):
            mapping.setdefault(key, name)
    return mapping, len(rows)
