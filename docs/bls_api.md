# BLS access, setup, and request planning

> Planning note (2026-10-10): the hackathon MVP data path is an ingested
> flat-file snapshot with no user keys (see [ROADMAP.md](ROADMAP.md) and the
> 2026-10-10 [DECISIONS.md](DECISIONS.md) entry). This document remains the
> reference for the optional, deferred live-API path described there.

## Current behavior

The MCP server is local and single-user. `get_bls_access_status` reports missing
or configured-but-unverified credentials without HTTP. `setup://bls-api` guides
registration and configuration. A configured key is not proof of validity;
explicit verification and remaining-quota tracking are not implemented.
Server instructions coach callers, but the observation service enforces setup
and per-request series/year bounds before making HTTP requests.

Live MCP retrieval requires `BLS_API_KEY`. There is no anonymous v1 fallback.
The lower-level BLS client is a transport/parser, not an access-policy boundary;
standalone client calls do not receive the MCP service's preflight protections.
Catalogue searches and calculations using supplied values need no key.

## Requesting and configuring a key

1. Visit [BLS registration](https://data.bls.gov/registrationEngine/).
2. Enter your email address and organization name; complete the CAPTCHA.
3. Find the registration-key email from `labstat@bls.gov`.
4. Set `BLS_API_KEY` in the server process's launch environment or in the MCP
   host's protected environment configuration. Never paste it into chat or
   tool arguments, log it, or commit it to the repository.
5. Restart the server, reconnect the client, and check access status again.

Changing another terminal's environment does not update a running server.
`.env.example` documents settings; automatic `.env` loading is not configured.
Renew BLS registration at least annually.

For hosted multi-user use, add authenticated HTTPS setup and per-user secret
storage tied to verified identity. Never share this process-global key among
unrelated users. Optional URL elicitation must be capability-negotiated;
form elicitation must not collect API keys. BLS registration issues the key;
it does not send it back to this server automatically.

## Published limits

Checked **2026-10-01** against the [BLS FAQ](https://www.bls.gov/developers/api_faqs.htm)
and [v2 signatures](https://www.bls.gov/developers/api_signature_v2.htm).
These are published ceilings, not remaining quota or a guarantee of coverage.

| Limit or feature | Registered v2 | Unregistered v1 (not implemented) |
| --- | --- | --- |
| Queries per day | 500 | 25 |
| Series per query | 50 | 25 |
| Calendar years per query | 20 | 10 |
| Request rate | 50 per 10 seconds | 50 per 10 seconds |
| Optional annual averages | Yes | No |
| Net/percent changes | Yes | No |
| Series descriptions (`catalog`) | Yes | No |

Count years inclusively: `end_year - start_year + 1`. For example, 2000–2019
is 20 years; 2000–2020 is 21. The API's default three-year window is not its
maximum; this server supplies explicit start/end years. Source coverage may
be shorter than the requested window. Optional v2 features are not all exposed
by this scaffold. Recheck official limits before changing policy.

## Planned splitting and combining (not implemented)

Implement planning in the observation service so callers request a logical
dataset once and receive consolidated results. Keep HTTP mechanics in the
client. Do not force the LLM to reconstruct the dataset from separate calls.

1. Deduplicate series IDs, preserve requested identity, and group compatible
   requests by credential owner, endpoint, time range, and API options.
2. Split IDs into chunks of at most 50. Split years into nonoverlapping windows
   of at most 20 inclusive years (`next_start = previous_end + 1`). Execute the
   Cartesian product of series chunks and year windows.
3. For a shared range with S unique series and Y inclusive years, the basic
   plan uses `ceil(S/50) * ceil(Y/20)` requests. For example, 75 series over
   1980–2024 uses 2 series chunks and 3 year windows: **6 requests**. Windows
   are 1980–1999, 2000–2019, and 2020–2024.
4. Combine compatible series in each query to avoid one-query-per-series
   waste. Coalesce overlapping logical requests only when it reduces calls
   without excessive overfetch or changing options/semantics. For widely
   separated base/target dates, two small windows may be preferable to fetching
   every intervening observation; expose the plan and its rationale.
5. Estimate request cost before execution. Account for attempts and retries;
   do not claim authoritative remaining quota from process-local counts.
   Coordinate the published rate ceiling across concurrent calls/processes,
   respect 429/Retry-After, and define backoff and daily-reset semantics after
   confirming BLS behavior. Never rotate keys to evade limits.
6. Merge by `(series_id, complete economic period identity)`; preserve units,
   footnotes, retrieval time, and batch provenance. Sort deterministically.
   Distinguish conflicting duplicates from identical duplicates; never silently
   overwrite a revision. Validate response status and requested series/window
   coverage before presenting a result as complete. Missing observations are
   not zero and sparse/discontinued series are not automatically errors.
7. Return a typed envelope containing observations, planned/completed/failed
   requests, warnings, and an explicit completion state. On failure, either
   fail the logical request or return clearly marked partial results under an
   explicit caller policy. Never return an ordinary list that hides a failed
   batch. Large results may need result pagination independent of BLS batching.
8. Add a cache only with explicit freshness/vintage policy and provenance;
   historical BLS observations can be revised.

Acceptance cases: exactly 50/51 series; exactly 20/21 inclusive years; 75 series
over 45 years; repeated IDs; a final short window; compatible coalescing;
conflicting duplicate observations; partial/missing series; failed middle batch;
429/backoff; concurrent quota use; revised observations; and secret-free output.
Use mocked HTTP tests plus a separately opt-in live validation command.

Until implemented, `get_series_data` rejects calls over 50 series or 20 years.
There is no automatic batching, retrying, throttling, caching, or quota ledger.

## Protocol references

- [FastMCP server instructions](https://gofastmcp.com/servers/server)
- [MCP elicitation](https://modelcontextprotocol.io/specification/2025-11-25/client/elicitation)
