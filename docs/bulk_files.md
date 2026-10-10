# BLS flat-file cache plan

Status: **plan only**. Nothing here is implemented. `download.bls.gov` was not
reachable from the drafting session. The PC/PD facts below are now checked
against the BLS files the owner saved in [`sample_data/`](sample_data/)
(`overview.txt`, `pc.txt`, `pd.txt`, series and mapping files). Items marked
**unverified** still need a live look (see [Verify first](#verify-first)).

## Why cache flat files rather than API configuration

The BLS API v2 is capped at 50 series and 20 years per call and needs a key
(see [bls_api.md](bls_api.md)). The flat files at
<https://download.bls.gov/pub/time.series/> carry the same series with no key
and no per-call quota, and they also give the full series catalog and code
mappings that `search_series` needs. A local mirror makes calculations
reproducible: every result can cite the exact file, its retrieval time and its
validators (`ETag` / `Last-Modified` / hash).

## Layout BLS uses (per `overview.txt` summary)

One directory per survey (two-letter code). Each holds:

| File | Role |
| --- | --- |
| `xx.txt` | Documentation: field definitions for series, data and mapping files |
| `xx.series` | One row per series: ID, dimension codes, title, begin/end period |
| `xx.data.*` | Observations (`series_id, year, period, value, footnote_codes`), split into partitions (`0.Current` = current year; others by sector/period) |
| `xx.<dimension>` | Mapping files translating codes to names (`xx.period`, `xx.footnote`, `xx.industry`, ...) |

## Programs to include

| Program | Dir | Include | Why |
| --- | --- | --- | --- |
| PPI industry, current (NAICS) | `pc` | **Yes (requested)** | Live monthly series: 4,510 series, 3,454 ending 2026-M08. `pc.data.0.Current` ~64 MB (search snippet, unverified) |
| PPI industry, discontinued (SIC) | `pd` | **Yes (requested), static** | Frozen history: 17,439 series, latest end year 2003 in the sample. Useful for pre-2004 SIC history, not for current escalation |
| ECI | `ci` | **Yes — baseline labor (owner decision 2026-10-10)** | Labor escalation for the vertical-construction archetype; quarterly program; format research and parser land in M2' |
| OEWS | `oe` | **Yes, later** | Locality wage ratios; already a project data source; annual, large |
| PPI commodities | `wp` | **Yes — the materials layer (2026-10-10)** | Commodity price of the material itself, organized by end use/material composition — the basket's unit of account. All series are price indexes (no percent-change families). Partitions include Lumber (08), Metals (10/10x + steel-mill indexes), Nonmetallic minerals (13), Construction services (80), Inputs to construction industries (80i/IP23). Hazard: discontinued series migrate WP → WD |
| CPI | `cu` | Optional | Only if baskets need consumer-price components; not in current scope |

Start with `pc` and `pd`; `ci` follows for MVP labor (owner decision
2026-10-10). `wp` is the materials layer (2026-10-10). `oe` (locality) is
the deferred program.

## Confirmed file facts (WP — PPI commodities, from wp.txt 2026-10-10)

`wp.txt` reviewed; `wp.series`/`wp.item`/data bytes are **pending fetch** —
the padding/byte-level claims below are from the doc, to be re-verified
against real files before parsing (the PC/PD/CI pattern).

- `wp.series`: 10 columns (`series_id`, `group_code`, `item_code`,
  `seasonal`, `YYMM` base_date, `series_title` (real titles),
  begin/end year+period). Series id = `WP` + seasonal + group + item.
- Data files share the 5-column shape; monthly periods plus `M13` annual
  averages; §3 notes `Q05`/`S03` as annual-average codes for quarterly and
  semiannual series (matters for other programs, not WP itself).
- Mappings: `wp.group` (group→text), `wp.item` (group+item→text),
  `wp.period`, `wp.footnote`, `wp.contacts`.
- Revisions: `P` preliminary, values revise for four months after first
  publication (same as PC/PD). Data scale change mid-2021 matches PC
  (one decimal before, three after).
- **WP → WD migration:** discontinued commodity series leave the WP
  database for WD between releases; refresh and basket validation must
  treat a series ending as explicit information, never silent absence.

## What to fetch per program

1. `xx.txt` and all mapping files (small): fetch weekly; they change rarely.
2. `xx.series`: fetch with the data refresh; diff against the prior copy.
3. `xx.data.0.Current`: the only data file refreshed routinely.
4. Historical partitions / `AllData`: **on demand only**, once per release
   cycle at most, and only for partitions a selected basket needs. Do not mirror
   by default (`pc` history is large).

## Cadence

Refresh follows the release calendar, not a blind timer.

| Program | Release rhythm | Check |
| --- | --- | --- |
| `pc` | Monthly, "on or before the 15th" for the prior month (`pc.txt`) | Daily conditional check on days ~10-16; weekly otherwise |
| `pd` | Static; updated only each January and July for newly discontinued series (`pd.txt`) | Check twice a year (Jan, Jul) plus a monthly cheap `HEAD` |
| `ci` (ECI) | Quarterly (about end of Jan/Apr/Jul/Oct) | Daily during the release week; monthly otherwise |
| `oe` (OEWS) | Annual (spring) | Monthly |

Every check is a conditional request (`If-None-Match` / `If-Modified-Since`, or
`HEAD` and compare `Last-Modified`/`Content-Length`). Download only on change.

## Confirmed file formats (PC and PD)

From `pc.txt`, `pd.txt` and the saved files. All files are ASCII with CRLF line
endings, tab separated, header row first (the `.txt` docs say "spaces"; the
files themselves use tabs).

- **Data files** (`series_id, year, period, value, footnote_codes`): `series_id`
  is **space-padded** (30 chars for PC, 17 for PD) and must be stripped. Value
  is an index; PC has one decimal through June 2021, three after. Parse values
  as `Decimal`, not float.
- **Series files:** parse by header name, never by position.
  - `pc.series` has 11 columns, including an undocumented `footnote_codes`
    (blank in all 4,510 rows) between `series_title` and `begin_year`; `pc.txt`
    documents only 10. PC uses `base_date` as `YYYYMM`.
  - `pd.series` header has **9** names but every one of 17,439 rows has **10**
    fields: a blank, space-filled column sits between `bench_date` and
    `begin_year`. A header-name `DictReader` would misread `begin_year` as the
    blank column and shift the rest. The loader must handle this explicitly
    (and fail loudly if the shape changes). PD `bench_date` is `YYMM`.
  - PD has **no series title**. Names come from `pd.industry` and `pd.product` (see
    "Product mapping" below). PC titles are in `pc.series`.
- **Data file sample** (`sample_data/pd.data.20.FabricatedMetal.head`, first 40
  lines of the full file; the full file is 208,929 rows, 10.4 MB, and was
  profiled but not committed). Profile of the full PD partition:
  - 1,263 series, all present in `pd.series`; every series' last observation
    matches its `end_year`/`end_period`; no duplicate `(series, year, period)`.
  - Years 1947-2003. Months `M01`-`M12` plus `M13` (annual average) rows,
    15,378 of them, so PD *does* carry annual averages despite `pd.txt`.
    `M13` follows `M12` in each year (`33.2` for Dec 1967, `32.8` for the
    annual average), so it must never be read as a thirteenth month.
  - `value` is a **left-padded 12-character field** (`        32.7`), one decimal
    in every row. Strip, then parse with `Decimal`.
  - `footnote_codes` is blank for all rows (PD history is final). The column is
    still space-padded, so a blank is `""` after stripping, not missing.
  - Every row had exactly 5 fields. This is one PD partition only; PC behavior is in the next item.
- **PC data sample** (`sample_data/pc.data.20.ComputerProduct.sample`: header,
  first 14 rows and last 20 rows of the partition; the full file is 53,255 rows,
  2.8 MB, profiled but not committed). Findings for NAICS 334:
  - 145 series, all in `pc.series`; each series' first and last observation
    matches `begin_year/period` and `end_year/period`; no duplicate keys; rows
    sorted by `(series_id, year, period)`; every row has exactly 5 fields.
  - Years 1947-2026. `M13` annual averages appear (3,933 rows) and are
    interleaved with months, as in PD.
  - Value precision matches `pc.txt` exactly: one decimal through 2021-M06 (46,864
    rows), three decimals from 2021-M07 (6,391 rows). Both are present in one
    series history, so parse as `Decimal` and never assume a fixed scale.
  - Footnote `P` appears on 375 rows, all in 2026-M05 to 2026-M08: the latest
    four months, which matches "revised up to four months after original
    publication". No `C` (correction) rows in this partition. Footnote cells
    are space-padded like the other columns.
  - Because `P` rows are rewritten when revised, a cached observation needs the
    file vintage and footnote at retrieval, and a later refresh must overwrite
    (not append to) the last four months.
  - Series IDs can end in a letter that is part of the product code
    (`PCU334519334519S`); the seasonal code is the third character (`U`), so
    do not read a trailing letter as the seasonal flag.
- **Product mapping:** `pc.product` (4,510 rows) and `pd.product` (17,439) each
  join one-to-one to their series file on `(industry_code, product_code)`;
  all 4,510 PC and 17,439 PD series match. Codes are space-padded in PD
  (`#        `), so strip before joining. `pd.product` line 3392 has 6 tab
  fields instead of 3 (`2384`, `#SS`, then empty fields, then
  `Secondary products`): the name is in the last field. Parse mapping files
  defensively (take the last field as the name, or reject and report), never
  assume a fixed column count.
- **Series ID structure:** `PCU` + industry code + product code, space-padded.
  PC industry codes are 6 characters and use `-` padding (`1133--`, `OMIN--`);
  PD codes are 4 characters and use `#` and `_` (`PDU1011#`, `PDUWINE#`). Codes
  are opaque strings; do not parse them numerically. Seasonal is `U` in every
  sampled row of both files (no seasonally adjusted series seen).
- **Periods:** `M01`-`M12` and `M13` (Annual Average). PC docs say annual
  averages exist; PD docs say they do not, yet PD series end with `M13` (11,156
  of 17,439), so the PD doc is wrong or stale. Annual averages must be kept
  distinct from months, never mixed into a monthly window.
- **Footnotes:** PC has `P` (preliminary; revisable up to four months after
  publication) and `C` (correction). PD has `P` only. The roadmap's
  "preliminary stays unknown until a flag mapping exists" rule can now be
  satisfied for PC/PD by this mapping.
- **Partitions:** PC data is split by NAICS subsector (`pc.data.0.Current`,
  `.01.aggregates`, `.1.OilAndGas` ... `.77.Recreation`); PD by SIC major group
  (`pd.data.0.Current`, `.1.MetalMining` ... `.31.Other`). The subsector in the
  partition name tells which file a given industry code lives in.
- **Series coverage ends differ:** many PC series have ended before the latest
  month. `end_year`/`end_period` must be checked per series; a missing latest
  month is an error under the roadmap's missing-data rule, not something to
  fill.

## Confirmed file facts (CI — ECI, verified 2026-10-10)

From the owner-saved `ci.txt` (the authoritative file list) and the checked-in
`ci.series`, `ci.industry`, `ci.subcell`, `ci.footnote`, `ci.seasonal`.

- **Files that exist:** `ci.series`, `ci.data.0.Current`, `ci.data.1.AllData`,
  `ci.aspect`, mappings `ci.area`/`ci.estimate`/`ci.footnote`/`ci.industry`/
  `ci.occupation`/`ci.owner`/`ci.periodicity`/`ci.seasonal`/`ci.subcell`,
  plus `ci.contacts`, `ci.txt`. **`ci.period` and `ci.datatype` do *not*
  exist** (an earlier guess fetched 404 pages — deleted, not committed).
- **Periods:** data-period codes are `Q01`-`Q04` only (reference months
  Mar/Jun/Sep/Dec, ci.txt §1). There is **no annual-average period code** —
  no `Q05` or `S01` in these files.
- **periodicity_code picks the measure, and it is the `series_id`'s final
  character:** `I` = index (levels; every current index shares base
  *December 2005 = 100*, ci.txt §1), `Q` = 3-month percent change, `A` =
  12-month percent change. **Only `I` series are valid temporal-factor
  inputs;** `Q`/`A` are percent changes and must be refused per the M3
  units rule. Example pair proving the encoding: `CIS...00I` ("current
  dollar index") vs `CIS...00Q` ("3-month percent change").
- **estimate_code** selects the cost concept (total compensation, wages and
  salaries, total benefits) — needed for basket selection; its mapping
  (`ci.estimate`) was not yet fetched.
- **Series layout:** TSV, padded fields, 15 columns, real `series_title`
  (`CIS1010000000000I` = "Total compensation for all civilian workers,
  current dollar index"), begin/end year+period; 2,471 series in this
  snapshot. Construction industry code is `230000` (`ci.industry`).
- **CI mapping files keep the name in the *second* column** followed by
  display metadata (`display_level`, `selectable`, `sort_sequence`) — so
  the generic last-field rule would grab `sort_sequence`; CI mappings use
  `name_column=1` in `parse_code_mapping`. (Found during implementation,
  2026-10-10; applies to `ci.industry`, `ci.occupation`, `ci.area`,
  `ci.estimate`, `ci.owner`, `ci.periodicity`, `ci.subcell`.)
- **Data layout:** `ci.data.0.Current`/`AllData` share the PC/PD 5-column
  shape. `ci.aspect` is standard errors with an extra `aspect_type` column —
  **never ingest it as observations.**
- **Missing data:** footnote `A` = "Dashes indicate data not available" — a
  data row may carry `-`; missing stays an error, never zero or
  interpolated, and `-` must not parse as a number (existing convention).

## Etiquette and safety

- Send a descriptive `User-Agent` with a contact address; BLS has rejected
  anonymous clients. Contact value comes from typed settings, not tool args.
- Keep one request in flight, back off on 403/429/5xx, and never retry in a
  tight loop.
- Download to a temp file, verify size and header row, then atomically rename.
  A failed or partial refresh must leave the previous good copy in place.
- Treat files as untrusted input: parse with the stdlib `csv` module on
  tab-separated data, never execute or evaluate content.
- Keep the last good copy plus the previous one so a bad release can be rolled
  back and diffed.

## Methodology rules that carry over

- Cache stores observations **as published**, with `footnote_codes` retained.
  Preliminary (`P` for PPI) stays "unknown" until the per-program flag mapping
  is confirmed (existing decision).
- No interpolation, series substitution or weight normalization at the cache
  layer. Revisions: PPI values are revised for ~4 months after first
  publication, so each stored observation needs the file vintage it came from.
- Provenance per file: URL, retrieved-at (UTC), `ETag`/`Last-Modified`,
  SHA-256, row count. Calculation results cite these.

## Suggested design (follows AGENTS.md boundaries)

- `clients/`: a small async HTTP fetcher (conditional GET, UA, temp-file
  download). No SQL, no economics.
- `repositories/`: a SQLite file-manifest table and loaders that fill the
  existing series/observation tables. Connections stay scoped per operation.
- `services/`: refresh service deciding what is due from the cadence table.
  Domain exceptions independent of FastMCP.
- Settings in `.env.example`: cache directory, contact User-Agent, enabled
  programs. A refresh runs from a CLI task (`poe refresh-bls`) or scheduler,
  **not** from an MCP tool handler; tools read the cache and report its age.
- Optionally one read-only tool reporting cache freshness per program.

## Milestones

1. Verify-first checklist (below); record outcomes in `DECISIONS.md`.
2. Fetcher plus manifest with mocked-HTTP tests (conditional GET, partial
   download, 304, 403 backoff).
3. `pc`/`pd` series + mapping ingestion into the catalog (replaces the
   curated seed, ROADMAP M4 successor), with the PD column-shape handling
   and fixture tests built from `sample_data/` rows.
4. `pc.data.0.Current` and `pd.data.0.Current` into the observation store with
   vintage; freshness reporting.
5. `ci`, then `oe`.

Live validation needs network access to `download.bls.gov`; mocked tests do not
establish numerical or format correctness.

## Verify first

- [x] `overview.txt`, `pc.txt`, `pd.txt` read; field layouts confirmed (above).
- [x] `pd` is the discontinued SIC set, **not** commodity data (earlier draft of
      this plan was wrong); `wp` is the commodities program.
- [x] Period codes (`M13` annual average) and footnote codes (`P`, `C`) for PC/PD.
- [x] **Verified 2026-10-10**, owner-run per `docs/bls_etiquette.md`
      (HEAD-only, sequential, 1 s delay, 160 requests, no failures;
      results in `sample_data/pc_headers_probe.json`): every `pc/` file
      returns `Content-Length`, `Last-Modified`, `ETag`, and answers
      conditional requests (`If-None-Match`/`If-Modified-Since`) with
      `304`. Caveats: the ETag is a per-release timestamp stamp shared by
      all files of a release — not per-file content identity — so
      `Last-Modified`/`Content-Length` are the cheap change signals and
      the manifest sha256 is the revision detector; and header-only
      partitions exist (`pc.data.61.EducationalServices`, 72 bytes).
- [x] `pc.product` / `pd.product` join one-to-one to their series files (above).
- [x] PD data-file layout and value format (one partition profiled).
- [x] PC data layout, 3-decimal values and `P` footnotes (one partition profiled).
- [ ] **Unverified:** current partition sizes and dates from the `pc/`/`pd/`
      directory listings — superseded for `pc/` by the 2026-10-10 probe
      JSON; repeat for `pd/` when its download is scheduled.
- [x] `ci` (ECI, in MVP scope since 2026-10-10): sampled, verified, and
      ingested 2026-10-10 — formats above; quarterly `Q01`-`Q04` only, no
      annual-average period code; `I`/`Q`/`A` periodicity encodes index vs
      percent change (only `I` is escalation-eligible; 506 index series
      loaded of 2,471 rows, skips recorded in the manifest).
      `ci.data.0.Current` (latest quarter, all series) remains to fetch
      when observation downloads start.
- [ ] `wp` (decided 2026-10-10: it is the materials layer): `wp.txt`
      reviewed; fetch `wp.series`, `wp.group`, `wp.item`, `wp.footnote`,
      `wp.period`, `wp.contacts` before the parser, and re-verify the
      doc-stated layout against the bytes.
- [ ] `oe` (locality) deferred past the MVP.
