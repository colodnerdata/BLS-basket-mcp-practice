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
and no per-call quota, and they also give the full series catalogue and code
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
| ECI | `ci` | **Yes** | Labor escalation; already a project data source (`data_sources.md`) |
| OEWS | `oe` | **Yes, later** | Locality wage ratios; already a project data source; annual, large |
| PPI commodities | `wp` | **Decide; likely wanted** | `overview.txt` lists `WP` (commodities) separately from `PC`/`PD`. Materials and equipment escalation may need it. `WD`/`ND` are its/NAICS discontinued sets |
| CPI | `cu` | Optional | Only if baskets need consumer-price components; not in current scope |

Start with `pc`, `pd`, `ci`; evaluate `wp` next. Add `oe` when locality mapping is scheduled.

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
  - PD has **no series title**. Names come from `pd.industry` (and `pd.product`,
    not yet sampled). PC titles are in `pc.series`.
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
3. `pc`/`pd` series + mapping ingestion into the catalogue (replaces the
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
- [ ] **Unverified:** whether the server returns `ETag`/`Last-Modified` and
      honors conditional requests; BLS's current User-Agent and rate rules.
      Needs one `curl -I` per file from a networked machine.
- [ ] **Unverified:** `pc.product` and `pd.product` (not yet sampled) and their
      row counts; whether `pc.series.product_code` always joins to them.
- [ ] **Unverified:** a data-file sample (`head -n 50` of `pc.data.0.Current`
      and `pd.data.0.Current`) for real footnote placement and value formats;
      only the first row layout has been seen.
- [ ] **Unverified:** current partition sizes and dates from the `pc/`/`pd/`
      directory listings.
- [ ] Decide on `wp` (and `ci`, `oe`) and sample their `xx.txt` and `xx.series`.
