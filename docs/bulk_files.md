# BLS flat-file cache plan

Status: **plan only**. Nothing here is implemented. Fetching
`download.bls.gov` was not possible when this was drafted, so facts below come
from BLS search snippets and must be confirmed against `overview.txt` and each
program's `xx.txt` before coding (see [Verify first](#verify-first)).

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
| PPI industry | `pc` | **Yes (requested)** | Industry output prices; `pc.series` ~0.85 MB, `pc.data.0.Current` ~64 MB |
| PPI commodity | `pd` | **Yes (requested)** | Commodity prices; mappings `pd.industry`, `pd.product`, `pd.period`, `pd.footnote` |
| ECI | `ci` | **Yes** | Labor escalation; already a project data source (`data_sources.md`) |
| OEWS | `oe` | **Yes, later** | Locality wage ratios; already a project data source; annual, large |
| PPI commodity (legacy) | `wp` | Decide | Overlaps `pd`; confirm whether `pd` supersedes it before mirroring both |
| CPI | `cu` | Optional | Only if baskets need consumer-price components; not in current scope |

Start with `pc`, `pd`, `ci`. Add `oe` when locality mapping is scheduled.

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
| `pc`, `pd` (PPI) | Monthly, mid-month (`pc.data.0.Current` was last modified July 15) | Daily conditional check on days ~10-20 of each month; weekly otherwise |
| `ci` (ECI) | Quarterly (about end of Jan/Apr/Jul/Oct) | Daily during the release week; monthly otherwise |
| `oe` (OEWS) | Annual (spring) | Monthly |

Every check is a conditional request (`If-None-Match` / `If-Modified-Since`, or
`HEAD` and compare `Last-Modified`/`Content-Length`). Download only on change.

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
   curated seed, ROADMAP M4 successor).
4. `pc.data.0.Current` and `pd.data.0.Current` into the observation store with
   vintage; freshness reporting.
5. `ci`, then `oe`.

Live validation needs network access to `download.bls.gov`; mocked tests do not
establish numerical or format correctness.

## Verify first

- [ ] `overview.txt` and each `xx.txt` read in full; field layouts confirmed.
- [ ] Exact `pd` vs `wp` relationship and which to mirror.
- [ ] Whether the server returns `ETag`/`Last-Modified` and honors conditional
      requests; BLS's current User-Agent and rate expectations.
- [ ] `pc`/`pd` period codes (including annual averages `M13`) and the footnote
      code meanings.
- [ ] Partition list for `pc` and `pd` and which a basket needs.
