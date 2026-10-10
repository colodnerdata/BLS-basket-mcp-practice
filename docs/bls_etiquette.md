# BLS site etiquette

Rules for any automated access to BLS servers from this repository — the
public API, `download.bls.gov` flat files, and any other `bls.gov` endpoint.
They bind humans and agents equally. Goal: never get the owner's IP
rate-limited or blocked, and never waste the daily API quota. A block lands
on the owner's whole network, not on the agent or process that caused it.

## What BLS publishes

- **API:** quotas and a request-rate ceiling, enforced with HTTP 429 ("too
  many requests"). The numbers and this server's pre-flight bounds live in
  [bls_api.md](bls_api.md); read them there rather than copying them here.
- **Flat files:** checked 2026-10-10, `download.bls.gov/pub/time.series/` and
  its `overview.txt` publish **no** volume, pacing, or courtesy policy. The
  flat-file rules below are self-imposed conservative norms, not BLS
  requirements.

## Hard rules

1. **Offline by default.** `poe check` and the test suite make no network
   calls; tests use mocked HTTP. Live access happens only when the owner
   deliberately runs a live command or a server session with a configured
   key, and any planned live-test command stays opt-in and out of default
   checks. An agent must never initiate live BLS calls or downloads on its
   own — ask the owner to run them (e.g. via `! <command>`).
2. **Stay inside the published bounds (API).** The server already rejects
   over-limit requests before any HTTP. Prefer fewer, larger requests over
   many small ones. Never rotate keys, identities, or IPs to evade a limit.
3. **Sequential and slow.** Send requests one at a time with a deliberate
   pause between them. Today's client makes sequential calls and has **no
   automatic retries** (a deferred seam; see [ROADMAP.md](ROADMAP.md)): a
   failure means stop and report, never wrap calls in retry loops. If a
   retry/backoff feature lands later, it must respect `429` and
   `Retry-After` and cap total attempts.
4. **Flat files: fetch once, reuse.** Download a given file at most once per
   logical need, keep it locally with its retrieval date, and reuse it for
   tests, evals, and inspection. Before any re-download, check freshness
   with a `HEAD` or conditional request rather than refetching wholesale.
   Do not crawl directory listings programmatically and do not mirror whole
   survey trees; fetch only the files the catalogue actually uses.
5. **Identify the traffic.** When live or download features land, send a
   descriptive `User-Agent` naming the project plus an owner-provided
   contact address from configuration — never a hardcoded address, and never
   the HTTP library's default in unattended bulk traffic. (The current
   client sends the httpx default; closing this gap is part of any live
   ingestion milestone.)
6. **Use published interfaces only.** The API endpoints or the flat files —
   never screen-scrape `bls.gov` HTML pages for series data, and respect
   `robots.txt` on any BLS host.
7. **Keys stay out of conversation.** Never paste a key into chat, prompts,
   tool arguments, logs, or commits; configuration lives in the client
   environment (see [bls_api.md](bls_api.md)).

## If throttled or blocked

A `429`, an HTML denial page where data was expected, or repeated failures
means **stop**: halt the whole run, do not probe to test whether the block
has lifted, and report to the owner what ran (command, request count,
wall-clock window). Resuming is the owner's decision. For any deliberate
live run, record the date, command, and request count as evidence — the same
record the planned live-validation command will require.

## Maintaining these rules

BLS policies change. Re-check the FAQ and the `download.bls.gov` overview
before editing this document or relaxing any rule, and note the check date
in the edit.

Sources:

- [BLS API FAQ](https://www.bls.gov/developers/api_faqs.htm)
- [/pub/time.series overview](https://download.bls.gov/pub/time.series/overview.txt)
- [bls_api.md](bls_api.md) — limits, setup, and request planning
- [DECISIONS.md](DECISIONS.md) — 2026-10-01 access-bounds entry
