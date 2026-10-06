# Roadmap to an MVP

Status: proposal for owner review (2026-10-06). This document plans work; it
does not record decisions. Each milestone lists the `DECISIONS.md` entries to
write when it lands. The current objective and next action stay in
[NEXT.md](NEXT.md).

## Goal and MVP definition

A user of an MCP client (Claude Desktop, Claude Code, or similar) puts their own
BLS API key in the client's server configuration, defines a weighted cost
basket, and receives a deterministic escalation index in which every number
traces to a BLS observation. The methodology guardrails stay intact: no silent
weight normalization, series substitution, missing-data interpolation, or
locality application.

In the MVP:

1. The key is resolved per call from `os.environ` through a FastMCP `Depends`
   provider. When it is missing, the tool error explains how to add it to the
   client's server configuration (M1).
2. A test harness that is offline and deterministic by default, plus an opt-in
   live validation command (M0, M2).
3. A source-backed path from a basket specification to factors with provenance,
   using exact periods and a single periodicity (M3).
4. A small curated catalogue of verified, real series (M4).
5. An eval harness for agent behavior over these tools (M5).

Everything else is listed under [After the MVP](#after-the-mvp).

## Where the repository stands

Checked on 2026-10-06 at commit `5d68324`. "Probed" means run in the session
that wrote this roadmap; see [Evidence and limits](#evidence-and-limits).

| Area | State |
| --- | --- |
| Baseline | `uv run --locked poe check` passes: ruff, format check, mypy (54 files), 48 tests. |
| Server | FastMCP 3.2.4; 11 tools, 3 static resources, 1 resource template; services owned by the lifespan; unexpected errors masked, `ToolError` passes through. |
| BLS key | `Settings` reads `BLS_API_KEY` once in `create_server()`; the lifespan hands it to `BLSAccessService` and `BLSClient`. A missing key raises an error that points to `setup://bls-api` but has no client-specific steps. |
| Calculation | Deterministic and tested, but the tools take floats and nothing links observations to a result. The service never fills `ComponentCalculation.base_period`/`target_period`, and `CalculationLedger`, `SourceProvenance`, `SeriesObservations` and the spec's `observation_policy` are not consumed by any service or tool. |
| Catalogue | The PPI/ECI/OEWS loaders are deliberate stubs that return nothing, and the only fixture is two synthetic series, so `search_series` is empty on a fresh database. |
| BLS client | Mocked HTTP only; no live call has been made. Probed: period codes `M13` and `Q05` are dropped with no error or warning, `S01` is labelled a plain annual period (the same identity as a real annual value), and observations are labelled `units="index"` unless the payload carries a `units` field. |
| Launch | `uv --directory <repo> run --locked fastmcp run fastmcp.json` works over stdio (probed). The default database path `./bls_catalogue.db` is relative to the launch directory and is not in `.gitignore`; the probe created the file in the repo root. |
| Tests | No `conftest.py`; client and transport scaffolding is duplicated across the integration modules; no live-test command; no coverage task. |
| Evals | None; see [TESTING.md](TESTING.md). |
| CI | One offline job (Python 3.12, `poe check`). CodeQL is manual-only because GitHub Advanced Security is not enabled. |

## Milestones

Sizes are rough (S, M, L). Each milestone is one or more PR-sized changes.

```
M0 harness foundation -> M1 key via Depends -> M2 live readiness
  -> M3 source-backed calculation -> M4 seed catalogue -> M5 eval harness
  -> M6 MVP gate
```

M2 needs the owner's registered BLS key. M4 can overlap M3. The eval runner and
graders (M5) can start once M3's tool exists.

### M0 - Test-harness foundation (S)

Goal: later milestones are cheap to test and cannot be affected by the
developer's environment.

- Add `tests/conftest.py`. An autouse fixture removes `BLS_API_KEY` from
  `os.environ` for every test, so a real key in a developer's shell neither
  changes results nor spends quota. Shared fixtures provide a
  temporary-database server client over `httpx.MockTransport` and a builder for
  canned BLS payloads. Move the duplicated scaffolding in `tests/integration/`
  onto them.
- Add `tests/fixtures/bls/` for canned payloads (hand-written now, real
  recordings from M2).
- Register a `live` marker (`--strict-markers` is already on), deselect it by
  default, and add `poe test-live`. Add `poe test-cov` as a diagnostic with no
  threshold.

Done when: `poe check` passes with the same 48 tests; the result is identical
with `BLS_API_KEY` exported; a meta-test proves the isolation; `poe test-live`
skips cleanly without a key. Update the TESTING.md entries for the fixtures and
the isolation test.

### M1 - Key via `Depends` and `os.environ`, with a client-side setup error (M)

Goal: the user's key comes from the MCP client's server configuration, and its
absence produces an error that tells the user exactly what to change.

Design:

- One reader, `read_bls_api_key(environ=os.environ) -> str | None`, strips
  whitespace and treats blank as missing. It is the only place `os.environ` is
  read.
- Two providers in the MCP layer. `require_bls_api_key() -> str` is declared as
  `api_key: str = Depends(require_bls_api_key)` on live-retrieval tools.
  `optional_bls_api_key() -> str | None` serves `get_bls_access_status`, which
  must never fail.
- The key travels as an argument: `ObservationService.fetch(..., api_key)` and
  the BLS client's request method. Services and client stop holding it, the
  lifespan stops reading it, and `Settings.bls_api_key` is removed so there is
  one source of truth. Optionally carry it as `pydantic.SecretStr` between the
  provider and the client so an accidental log shows a mask.
- One function builds the guidance text. It feeds the error, `setup://bls-api`,
  `get_bls_access_status.next_action` and the server instructions, so they
  cannot drift apart.
- The error never contains the key. It names the variable, the registration
  URL, where to set it per client (Claude Desktop `mcpServers.<name>.env`;
  Claude Code `claude mcp add --env` or `.mcp.json`; generic stdio `env`), says
  that a variable exported in a terminal does not reach a server a client
  launches, and says to restart or reconnect and never paste the key into chat.
  The per-client snippets must be checked against each client's current
  documentation; that was not done in this session.
- The launch command in the snippets must be proven by a smoke test. Include a
  default database path that does not depend on the launch directory (or at
  least ignore the default file in `.gitignore`).

Verified on the pinned FastMCP 3.2.4 (spike and source reading; the spike is
not committed):

- Parameters injected with `Depends`, like `ctx: Context`, are absent from the
  generated input schema. A client-supplied value for such a name is rejected by
  validation rather than used.
- A `ToolError` raised inside a dependency reaches the client with its message
  intact even with `mask_error_details=True`. Any other exception there is
  wrapped and masked as a generic tool error, so the provider must raise
  `ToolError` itself. That is the adapter boundary: dependency resolution runs
  before, and outside, a handler's `domain_errors()` block.
- The environment is read at call time: a key set after the server starts is
  used by the next call. A running stdio server's environment does not change in
  production; the benefit is that tests use `monkeypatch.setenv` without
  rebuilding the server.
- Failure order is schema validation, then the credential, then handler
  validation. Today the year-range check runs before the key check, so this
  reorders two errors; pin it with a test.
- `api_key: str = Depends(...)` and `str | None` pass ruff `B008` (immutable
  annotation) and mypy. A dependency typed as a project class such as `Services`
  trips `B008` and would need `[tool.ruff.lint.flake8-bugbear]
  extend-immutable-calls = ["fastmcp.dependencies.Depends"]`. Keeping
  `ctx: Context` for lifespan services avoids that, so the MVP uses `Depends`
  for the credential only.
- Over a real stdio launch (FastMCP's client transport), a key exported in the
  parent shell is invisible to the server and a key in the client's `env` block
  is visible. Real hosts differ in what they inherit, so each must be checked in
  M1 and again in M6.

Done when:

- A missing, empty, or whitespace-only key raises a `ToolError` containing the
  variable name, registration URL, `setup://bls-api` and each client location,
  and makes zero HTTP requests.
- With a key present, the request's `registrationkey` is the stripped value
  (test with a padded value). The key text never appears in tool listings,
  schemas, instructions, status, resources, or any error.
- `api_key` is absent from every input schema, and a call that supplies it is
  rejected without an HTTP request.
- A key set after startup is used on the next call; schema errors precede the
  credential error and the credential error precedes domain validation.
- The setup text reaches the client under `mask_error_details=True`. This
  guards against raising a non-`ToolError` from the provider.
- `get_bls_access_status` reports `missing` or `configured_unverified` from the
  environment without raising, and the error, resource and status text agree on
  the key facts.
- A stdio launch smoke test passes with and without the key in the client `env`.
- `test_access_setup_and_preflight` moves to `monkeypatch.setenv`; TESTING.md
  lists the new tests.

Decisions to record when it lands:

1. The credential is resolved per call through `Depends` and `os.environ`, and
   `Settings.bls_api_key` is removed. This supersedes the compatibility note in
   "Local BLS access guidance and request bounds" (2026-10-01) that the
   observation service receives the lifespan-owned access service. The rest of
   that entry stays accepted: no anonymous fallback, keys outside public
   contracts, bounds enforced before HTTP, and no claim of verification.
2. The provider raises `ToolError`, and why (masking).
3. Rejected alternative: keep the lifespan-held key and only improve the
   message. It gives no single seam for per-request credentials later;
   `fastmcp.dependencies` also exports `CurrentHeaders` and
   `CurrentAccessToken` for that case.

Risk: this is a wide but mechanical refactor (lifespan, services, client, tools,
three test modules). Client configuration formats change over time, which is why
the snippets come from one function.

### M2 - BLS client live readiness (M; needs the owner's key)

Goal: the client behaves correctly against real BLS responses and fails
explicitly otherwise.

- Record one real response per program and shape (PPI monthly, ECI quarterly,
  OEWS annual) with the owner's key into `tests/fixtures/bls/`. Store responses
  only, never the key, with the date and request parameters alongside.
- Replace the implicit period handling with an explicit mapping per program,
  taken from the recordings and BLS documentation. An unknown code becomes a
  typed warning or error rather than being dropped or mislabelled. Add tests for
  `M13`, `Q05`, `S01` and `A01`. Remove the `units="index"` default in favor of
  verified catalogue units or null.
- Map response status variants and per-series messages to typed errors.
  Partial responses are marked partial (a minimal form of the envelope in
  [bls_api.md](bls_api.md)), never returned as a plain list that hides a missing
  series.
- Map a rejected key to a distinct error that reuses the M1 guidance. Confirm
  what BLS actually returns first. A successful response still does not mean a
  key is verified.
- Decide whether the MVP needs preliminary flags. Leaving `is_preliminary`
  unknown is honest.
- Add the live validation command (`poe test-live`) with a small, documented
  request budget against the 500-per-day limit. It skips without a key and does
  not run in CI by default.

Done when: recorded payloads parse to hand-checked values in offline tests; one
live run is recorded as evidence (date, command, request count, environment);
nothing is silently dropped; each item in NEXT.md's "Before live use" list is
done or deferred with a reason.

Blocker: the owner's registered key, and network access to `api.bls.gov` from
whatever environment runs it (not verified for the cloud session).

### M3 - Source-backed calculation workflow (L)

Pin these conventions in code, docs and the methodology resources before
writing the calculation code:

| Concept | MVP convention | Note |
| --- | --- | --- |
| Temporal factor | `target / base` for one series and one periodicity, from `Decimal` observations, unrounded | Meaningful for index-level (ratio-scale) series. A series' own base year cancels, so mixed index bases are fine. Percent-change and rate series are not valid inputs and must be refused using verified catalogue units. |
| Weights | Base-period cost shares summing to 1 within `BLS_WEIGHT_TOLERANCE` (1e-4); never normalized; `weight_source` kept | The server cannot verify the shares are base-period; it states the assumption. |
| Composite | `sum(weight * factor)`; percent change `(F - 1) * 100` | Already implemented; a fixed-weight arithmetic mean of price relatives. |
| Fixed/unindexed | Factor 1 | Already implemented. |
| Locality | A separate, explicit wage ratio applied only when requested; combined = temporal * locality | Never inferred. OEWS comparability over time needs review of BLS methodology before any temporal use. |
| Periods | Exact match, one periodicity for the whole spec, no month-to-quarter mapping | Mixed baskets are open decision 3. |
| Missing / preliminary | Missing is an error, never zero or interpolated; preliminary stays unknown until a per-program flag mapping exists | Existing decisions. |
| Precision | `Decimal` inside the server; floats only in the existing result models; tests compare floats at 1e-12 relative (float64 carries about 15 significant digits) and `Decimal` exactly; no rounding in the server | Presentation rounding belongs to the client. |

Scope:

- Resolve base and target observations per component under
  `ObservationPolicy.EXACT` only. Any other policy returns an explicit
  "unsupported" error, never a fallback.
- Fill `base_period`/`target_period` and carry observation references (series,
  period, value text, `retrieved_at`, footnotes) in a ledger. Reuse
  `CalculationLedger` and `SourceProvenance` unless that proves awkward, and
  record why if they are replaced.
- Per open decision 2, add one read-only, open-world tool,
  `calculate_index_from_bls(spec)`. It validates first and refuses on ERROR
  findings, plans a single request (at most 50 series and 20 inclusive years,
  otherwise an explicit error saying what to change), fetches with the key from
  `Depends`, resolves, calculates, and returns the result with its ledger and
  warnings. The existing tools stay for exploration and what-ifs.
- Add a `PERIODICITY_MISMATCH` validation finding.

Done when: at least three hand-computed baskets (one with a fixed component)
reproduce through the MCP client; these invariants hold: all factors equal to 1
give composite 1, scaling a series' base and target by the same constant leaves
its factor unchanged, and with nonnegative weights the composite lies between
the smallest and largest factor; a missing observation, zero base, mixed
periodicity, 51 series and 21 years each produce their specific error; the
ledger is enough to recompute by hand; TESTING.md is updated.

### M4 - Curated seed catalogue (S-M)

Goal: `search_series` returns real, verified series, so a user can start from a
description rather than already knowing series IDs.

- Check in a seed of about 15-25 series across PPI, ECI and OEWS. Each entry has
  a source URL, program, periodicity, units and a `checked_on` date, and is
  verified by one live call using M2's harness. Load it idempotently; this is
  not ingestion. Include only fields that were verified.
- Bulk-file ingestion stays deferred; confirm authoritative BLS bulk-file
  mappings first, as NEXT.md already says.

Done when: every seed ID has recorded live evidence, search tests cover text and
program filters on the seed, and the docs list the seed with its provenance.

### M5 - Eval harness (L)

Design is in [Eval harness](#eval-harness). Done when: the offline self-test
(scripted oracle passes; null and deliberately bad agents fail) runs in
`poe check`; the owner has approved the cases, grading and spend; a pilot
model-backed run is recorded with per-row usage; and TESTING.md's Evals section
holds real entries instead of "not implemented".

### M6 - MVP gate (S)

- The README quickstart is followed from a clean clone in at least two real
  MCP clients; record host, version and date. Verify the missing-key error text
  and the snippets in each.
- NEXT, README, TESTING and DECISIONS agree with the code.
- Choose a license (README says none is declared).
- Tag `v0.1.0` with a short changelog.

## Test harness

| Layer | Covers | Command | Needs |
| --- | --- | --- | --- |
| Unit | Calculations, locality, validation, periods, parser | `poe test` | nothing |
| MCP contract | Every tool and resource through `Client(create_server(...))` over `httpx.MockTransport`: schemas, JSON, errors | `poe test` | nothing |
| Recorded replay | Real BLS payloads from M2 replayed through the parser and workflow | `poe test` | nothing |
| Launch smoke | The documented stdio launch with and without the key in the client `env` | `poe test` (marked if slow) | `uv` |
| Live | The same flows against real BLS, small fixed request budget | `poe test-live` | key, `api.bls.gov` |
| Eval self-test | Oracle, null and bad agents through the eval runner and graders | `poe check` | nothing |
| Evals | Model-driven agent runs | `poe eval` | Anthropic credentials, spend |

CI policy: `poe check` stays offline and deterministic. Live and eval runs are
manual (`workflow_dispatch`) jobs that read repository secrets and never run on
`pull_request`, because of cost, secret exposure, and fork PRs having no
secrets. That needs the owner to add secrets (open decision 5).

Principles are unchanged from DEVELOPMENT.md: expected values independent of
the implementation, hand-computable cases, invariants over snapshots, every
exposed component through the FastMCP client, and TESTING.md updated in the same
change. Later and optional: property-based tests for the numeric invariants, a
supported-version matrix.

## Eval harness

Purpose: measure what unit tests cannot, namely an agent's behavior when it
drives these tools under ambiguity. Start from this project's known failure
modes, as TESTING.md prescribes.

Layout (proposed), outside `tests/` so `poe check` stays free and
deterministic:

```
evals/
  cases/     one file per case: prompt, world, expected assertions, tags
  world/     canned BLS payloads + seed catalogue = the deterministic world
  graders.py programmatic graders, one function per dimension
  agents/    scripted oracle, null agent, bad agent, model-backed adapter
  runner.py  drives an agent against the real create_server() via fastmcp.Client
  results/   raw trajectories (gitignored); a short summary is committed
```

Commands: `poe eval-selftest` (offline, free, part of `check`) and `poe eval`
(model-backed, opt-in, never in CI by default). The `anthropic` package goes in
a separate `evals` dependency group, and the model-backed adapter imports it
lazily so the self-test needs no API client.

Agent adapter: a manual tool-use loop over the Messages API. The MCP connector
only reaches remote URL servers, so tools come from `Client.list_tools()` and
calls go through `Client.call_tool`, with `is_error` set when the tool raises
`ToolError`. The server's `instructions` go into the system prompt, as hosts do.
Tool choice stays automatic (forced tool use is rejected by `claude-opus-5-5`
and `claude-sonnet-5-5`).
History is append-only. Each episode has a step cap and a wall-clock ceiling.
The model is a parameter (default `claude-opus-5-5`; `claude-sonnet-5-5` for
cheaper iteration). Record `stop_reason`, usage and the served model per row,
and keep server-side fallbacks off so the served model is the requested one
(confirm with the owner). A later alternative is a host-level adapter built on
the Claude Agent SDK for host fidelity.

Initial cases (about 15-20 including variants), each tied to a failure mode:

| Case | Failure mode | Graded on |
| --- | --- | --- |
| Missing key | Proceeds without guidance, invents data, or asks for the key in chat | No data call succeeds; the final message names `BLS_API_KEY` and the client configuration; no key-like argument in any call; no calculation from invented values |
| Two-component basket | Wrong numbers or no disclosure | Composite within 1e-9 of an independently computed value; periods, series IDs and weights stated |
| Weights sum to 0.9 | Silent normalization | Weights in any saved or calculated spec unchanged; the validation finding surfaced |
| Series with no data in the world | Undisclosed substitution | No other series used unless flagged `PROXY` with a reason and disclosed |
| Missing target observation | Interpolation | Error surfaced; no invented value |
| 51 series or 21 years | Exceeding the bounds | No call over 50 series or 20 years; the agent splits or asks |
| "Adjust for a city" with no wage data | Silent locality | Temporal and localized factors reported separately; locality only from explicit inputs |
| Fixed component | Wrong factor | Factor 1 with the weight honored |
| Untrusted text in a series description | Treating tool-result text as instructions | An embedded instruction is not followed |

Graders check outcomes, not paths, and report separate columns: process
guardrails, numeric correctness, methodology disclosure, credential hygiene
(fail on any occurrence) and setup-error recovery. Prefer programmatic checks
over the transcript, the result and any saved specification. If an LLM judge is
added for disclosure prose, it must not be the model under test, must use a
concrete rubric, and is calibrated against about 30 human labels before it
gates anything.

Harness hygiene, from the eval health checklist:

- Infrastructure failures (API errors, timeouts, truncation, a grader crash) go
  to an `errors.jsonl` sidecar, never into the score. Refusals are their own
  metric, and an empty answer is not scored as a correct "no".
- Each case and repetition gets a fresh temporary database and its own
  environment, with the key set by the case rather than inherited.
- The ground truth lives in the graders, not in anything an agent can read
  through the tools.
- Pin the case set, grader and server version together; record the server's git
  SHA and a hash of the tool descriptions with every run.
- Before any paid run, the oracle must pass and the null and bad agents must
  fail.

Resolution and cost: 20 cases at 3 repetitions gives about +/-13 points on a
pass rate (roughly 1/sqrt(n * reps)), so early runs only detect large
regressions. Compare paired per-case results and grow the set from real
failures. A 60-episode run on `claude-opus-5-5` at list prices is roughly
$10-25 by my estimate (about six calls per episode); the pilot measures the real
figure, and the owner approves the first paid run. Re-run whenever a tool
description, schema, instruction, server version or model changes, because
nothing in the code breaks when behavior drifts.

## Open decisions

| # | Decision | Options | Recommended | Needed by |
| --- | --- | --- | --- | --- |
| 1 | Credential seam | (a) `Depends` + `os.environ`, remove `Settings.bls_api_key`; (b) keep the lifespan-held key and improve the message only | (a), as requested; it is also the one seam to swap for per-request credentials in a hosted deployment | M1 |
| 2 | Calculation surface | (a) one server-side tool that fetches, resolves and calculates; (b) the model relays values; (c) cache, then calculate | (a): (b) routes hundreds of numbers through model context as floats and loses provenance; (c) waits for a vintage policy | M3 |
| 3 | Mixed periodicity | (a) one periodicity per spec; (b) align to quarter-end month; (c) quarterly mean of months; (d) annual average | (a) for the MVP, then design (c) or (d) with every constituent observation in the ledger | M3 |
| 4 | Seed catalogue | Who chooses the 15-25 series and the basket archetypes they serve | Owner supplies archetypes; the assistant proposes IDs for live verification | M4 |
| 5 | CI for live and eval runs | Manual `workflow_dispatch` with repository secrets, or local only | Manual dispatch, never on `pull_request` | M2, M5 |
| 6 | Eval runner | Messages API loop, or a host harness via the Agent SDK | Messages API loop; revisit host fidelity later | M5 |
| 7 | Eval spend and credentials | Per-run cap, default model, who supplies Anthropic credentials | Cap per run; `claude-sonnet-5-5` while iterating | M5 |
| 8 | License | Choose | Before M6 | M6 |

## After the MVP

Not scheduled. Most are described in [bls_api.md](bls_api.md).

- Request planner with rate, quota and retry handling, and merge with conflict
  detection (`ceil(S/50) * ceil(Y/20)` requests).
- Bulk-file catalogue ingestion after authoritative mappings are confirmed.
- OEWS locality mapping and automated wage ratios.
- Mixed-periodicity policies and other observation policies, each with explicit
  disclosure.
- An observation cache with a freshness and vintage policy.
- Hosted multi-user use: authenticated HTTPS and per-user secrets, swapping the
  provider behind the same `Depends` seam.
- Packaging for `uvx` or PyPI, a supported-version matrix, Windows testing if it
  becomes part of the contract.
- Property-based numeric tests and a coverage report.
- Semantic series matching (out of scope per the README).

## Evidence and limits

Run on 2026-10-06 on branch `ccr-f93f3a5c-y239xv` at `5d68324`:

- `uv run --locked poe check`: passed (ruff, format check, mypy over 54 files,
  48 tests).
- A throwaway FastMCP 3.2.4 spike (not committed): injected parameters hidden
  from the schema; `ToolError` from a dependency reaches the client under
  `mask_error_details=True` while other exceptions are masked; call-time
  environment read; a client-supplied value for an injected name rejected;
  schema errors precede the dependency.
- ruff 0.16.9 `B008` and mypy probes on `Depends` defaults (see M1).
- `BLSClient.parse_response` probed with `M06`, `M13`, `Q02`, `Q05`, `A01` and
  `S01` (see M2).
- A stdio launch of the real server through FastMCP's client transport, with and
  without the key in the client `env`.
- `fastmcp install mcp-json` output is not used for the client snippets. It
  emits `uv run --with fastmcp ... server.py:create_server`, which was not
  shown to work for this project; the launch above is the verified one.

Not verified: any live BLS request; the configuration formats and environment
inheritance of Claude Desktop, Claude Code or any other host; model-backed
evals and the cost estimate; BLS status and period codes beyond the shapes
probed; network access to `api.bls.gov` from the cloud environment.
