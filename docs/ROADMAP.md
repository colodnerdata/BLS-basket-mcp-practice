# Roadmap to an MVP

Status: revised 2026-10-10 per owner direction for the GSA MCP Server
Hackathon entry (kickoff 2026-10-19; the submission deadline is not yet
published). The submission is this repository (aligned to
GSA-TTS/mcp-hackathon-template), a slide deck, and an evaluation document.
Judges run the server locally with zero setup and no API keys; the sandbox
deployment uses the IBM watsonx Orchestrate kit's Code Engine
build-from-Git option, so the repository itself is the build source and no
build artifact is published (owner's choice 2026-10-10; an earlier same-day
VM-hosting direction was retracted). The data source is an ingested
flat-file snapshot, recorded in a checked-in manifest. The original
2026-10-06 plan (key-per-client via `Depends`, live-API readiness as M2) is
preserved in git history; the superseded credential choice and the new
snapshot/manifest decisions are recorded in [DECISIONS.md](DECISIONS.md)
(2026-10-10). The current objective and next action stay in
[NEXT.md](NEXT.md).

## Goal and MVP definition

A judge or evaluator clones this repository and runs the server locally in a
standard MCP client (Claude Desktop, Claude Code, MCP Inspector) — or uses
the sandbox deployment built from the same repo — and, with no registration,
key, or network access, defines a weighted cost basket and receives a
deterministic escalation index in which every number traces to a BLS
observation in a documented, hash-verified snapshot of official BLS flat
files. The methodology guardrails stay intact: no silent weight
normalization, series substitution, missing-data interpolation, or locality
application.

In the MVP:

1. The data source is an ingested flat-file snapshot in SQLite, described by
   `data/manifest.json` in git (the authoritative record: files, URLs,
   retrieval dates, sha256 hashes, parse counts, warnings) and an
   `ingestion_log` table in the database (the receipt). A `poe
   verify-ingest` task checks the two agree (M2'). The curated raw slices
   are checked into git, so the database is rebuilt anywhere — developer
   machine, CI, or image build — from the same source with zero network;
   nothing is published as a data artifact. The snapshot date is disclosed
   in provenance and methodology resources; the server makes no claim of
   "latest" data.
2. The test harness is offline and deterministic by default, including
   flat-file fixture slices and the ingestion-agreement check (M0, M2').
3. A source-backed path from a basket specification to factors with
   provenance, resolving observations from the local snapshot, using exact
   periods and a single periodicity (M3).
4. A curated catalog of about 15-25 verified series from the PPI `pc`/`pd`
   flat files, selected from owner-supplied basket archetypes and verified
   against real flat files (part of M2'; supersedes old M4). ECI and OEWS
   coverage is deferred past the MVP.
5. Submission readiness (M5'): the template-conformant shell landed on
   main; remaining work is LICENSE/SECURITY.md (in this change), the
   QUICKSTART seed-database build step, Dockerfile verification,
   `server.json`/`manifest.yaml` identity review, the public-repo
   checkpoint, a clean-clone run in two real MCP clients, and the IBM Code
   Engine build-from-Git deployment registered in watsonx Orchestrate.
6. A deterministic, offline eval-evidence pack — scripted scenarios through
   the real MCP client with committed results — feeding the evaluation
   document's testing-methodology and performance-metrics sections (M4').

Outside the MVP: the live BLS API path with a server-side key (old M1/M2),
the LLM-backed eval harness (old M5's remainder), post-hackathon hosting and
multi-user hardening, and everything under [After the MVP](#after-the-mvp).

## Where the repository stands

Checked on 2026-10-06 at commit `5d68324`. "Probed" means run in the session
that wrote this roadmap; see [Evidence and limits](#evidence-and-limits). This
table is a dated snapshot, not the current state: since the probe, the
template-aligned shell (one component per file, `main.py`/`app.py`/
`routes.py`, Dockerfile, `manifest.yaml`, `server.json`, QUICKSTART.md,
`eval/`) and the bulk-file research (`bulk_files.md`, `docs/sample_data/`)
landed on main, and database files became git-ignored. Where a row disagrees
with the milestone text, the milestone text wins. New since the probe:
`docs/bls_etiquette.md` (2026-10-10) governs all BLS-bound traffic, including
the flat-file downloads this plan depends on.

| Area | State |
| --- | --- |
| Baseline | `uv run --locked poe check` passes: ruff, format check, mypy (54 files), 48 tests. |
| Server | FastMCP 3.2.4; 11 tools, 3 static resources, 1 resource template; services owned by the lifespan; unexpected errors masked, `ToolError` passes through. |
| BLS key | `Settings` reads `BLS_API_KEY` once in `create_server()`; the lifespan hands it to `BLSAccessService` and `BLSClient`. A missing key raises an error that points to `setup://bls-api` but has no client-specific steps. Irrelevant to the snapshot MVP; matters only for the deferred live path. |
| Calculation | Deterministic and tested, but the tools take floats and nothing links observations to a result. The service never fills `ComponentCalculation.base_period`/`target_period`, and `CalculationLedger`, `SourceProvenance`, `SeriesObservations` and the spec's `observation_policy` are not consumed by any service or tool. |
| catalog | The PPI/ECI/OEWS loaders are deliberate stubs that return nothing, and the only fixture is two synthetic series, so `search_series` is empty on a fresh database. M2' fills this from real flat files. |
| BLS client | Mocked HTTP only; no live call has been made. Probed: period codes `M13` and `Q05` are dropped with no error or warning, `S01` is labeled a plain annual period (the same identity as a real annual value), and observations are labeled `units="index"` unless the payload carries a `units` field. These parser issues move to M2' against flat-file fixtures. |
| Launch | `uv --directory <repo> run --locked fastmcp run fastmcp.json` works over stdio (probed). The streamable-HTTP/`app.py` launcher and Dockerfile for the Code Engine deployment landed on main but are unverified end-to-end (M5'). The default database path `./bls_catalog.db` is relative to the launch directory; database files are now git-ignored, so the file the probe created in the repo root can no longer be committed by accident. |
| Tests | No `conftest.py`; client and transport scaffolding is duplicated across the integration modules; no live-test command; no coverage task. |
| Evals | None; see [TESTING.md](TESTING.md). The hackathon judges' harness is the first external eval. |
| CI | One offline job (Python 3.12, `poe check`). CodeQL is manual-only because GitHub Advanced Security is not enabled. |

## Milestones

Sizes are rough (S, M, L). Each milestone is one or more PR-sized changes.

```
M0 harness foundation -> M2' flat-file ingestion + manifest
  -> M3 source-backed calculation over the snapshot
  -> M4' eval evidence pack -> M5' submission readiness
  -> M6 hackathon MVP gate
```

Mapping from the 2026-10-06 plan: M0 is unchanged. M2' supersedes M2 (live
readiness) and M4 (seed catalog): the parser and catalog work now happen
against checked-in flat-file fixtures, so the owner's BLS key leaves the
critical path. M3's design is unchanged except that observation resolution
reads the local snapshot instead of planning an API request. M4' is the
deterministic, LLM-free core of old M5 (scripted oracle scenarios), pulled
into the MVP because "your own evaluation setup and results" is a scored
deliverable of the hackathon. M5' is submission readiness plus the Code
Engine spike. Old M1 (key via `Depends`), the live-API remainder of old M2,
and old M5's LLM-backed harness move to [After the MVP](#after-the-mvp).

### M0 - Test-harness foundation (S)

Goal: later milestones are cheap to test and cannot be affected by the
developer's environment.

- Add `tests/conftest.py`. An autouse fixture removes `BLS_API_KEY` from
  `os.environ` for every test, so a real key in a developer's shell neither
  changes results nor spends quota if the live path ever runs. Shared
  fixtures provide a temporary-database server client over
  `httpx.MockTransport` and a builder for canned BLS payloads. Move the
  duplicated scaffolding in `tests/integration/` onto them.
- Add `tests/fixtures/bls/` for canned payloads (now: flat-file slices from
  M2', then any API recordings if the live path lands).
- Register a `live` marker (`--strict-markers` is already on), deselect it
  by default, and add `poe test-live` for the deferred live path. Add
  `poe test-cov` as a diagnostic with no threshold.

Done when: `poe check` passes with the same 48 tests; the result is identical
with `BLS_API_KEY` exported; a meta-test proves the isolation; `poe test-live`
skips cleanly without a key. Update the TESTING.md entries for the fixtures
and the isolation test.

### M2' - Flat-file ingestion, manifest, and seed catalog (M-L)

Goal: `search_series` returns real, verified series; observations resolve
from the local snapshot; every ingested file is recorded so any device can
rebuild the database from checked-in slices with zero network access.

- The per-program mapping research is largely done in
  [bulk_files.md](bulk_files.md): PC/PD file formats and quirks
  (space-padded series IDs, `pd.series`' undocumented extra column, PD's
  lack of series titles, `M13` annual averages in PD despite `pd.txt`),
  partition layouts, and refresh cadence are confirmed against owner-saved
  real files in `docs/sample_data/`. Remaining live verification: the
  header probe (`scripts/probe_bls_headers.py pc`) from a networked
  machine. ECI is deferred past the MVP; `wp` (PPI commodities) is
  undecided.
- Cut parser fixture slices from the checked-in `docs/sample_data/` files
  into `tests/fixtures/bls/`, with the source file and retrieval date
  recorded alongside. They are the parser's offline ground truth (replacing
  the API recordings planned in old M2) and triple-duty: parser fixtures,
  seed inputs, and container build source — the Code Engine image builds
  the database from the same checked-in slices.
- Explicit period-code mapping including `M13`, `Q05`, `S01`, `A01`; unknown
  codes become typed warnings counted in the manifest — never silently
  dropped, never mislabeled. Units come from verified catalog metadata
  or stay unknown, never defaulted to `"index"`.
- An ingestion command (plain CLI/service code, deliberately **not** an MCP
  tool — judges must not be able to trigger downloads): download
  (owner-invoked per `docs/bls_etiquette.md` — one fetch per file, a
  descriptive project `User-Agent` with an owner-provided contact address,
  conditional freshness checks before any re-download) → sha256 → parse →
  write through the repositories → update the `ingestion_log` table and
  `data/manifest.json` (pydantic-validated; fields per the 2026-10-10
  DECISIONS entry: URL, retrieval date, BLS last-modified, size, sha256,
  ingestion timestamp and code version, row/series/observation counts,
  period-code warning counts, status).
- Add `ingestion_log` to `db/schema.py` and add `poe verify-ingest`, which
  fails on any manifest/database disagreement and runs offline in `check`.
- catalog seeding through real ingestion of the `pc`/`pd` series and
  mapping files per `bulk_files.md`, replacing the stub loaders;
  owner-supplied basket archetypes decide which data partitions are
  ingested first (the `0.Current` files plus the partitions those baskets
  need).

Done when: ingestion from fixtures reproduces a known database offline;
`verify-ingest` passes and its tests catch a seeded mismatch; one real,
owner-invoked download is ingested end-to-end with evidence recorded (date,
URL list, hashes, request count, per the etiquette doc); period fixtures
parse to hand-checked values with nothing silently dropped; every ingested
file has recorded provenance; TESTING.md is updated.

### M3 - Source-backed calculation workflow (L)

Pin these conventions in code, docs and the methodology resources before
writing the calculation code:

| Concept | MVP convention | Note |
| --- | --- | --- |
| Temporal factor | `target / base` for one series and one periodicity, from `Decimal` observations, unrounded | Meaningful for index-level (ratio-scale) series. A series' own base year cancels, so mixed index bases are fine. Percent-change and rate series are not valid inputs and must be refused using verified catalog units. |
| Weights | Base-period cost shares summing to 1 within `BLS_WEIGHT_TOLERANCE` (1e-4); never normalized; `weight_source` kept | The server cannot verify the shares are base-period; it states the assumption. |
| Composite | `sum(weight * factor)`; percent change `(F - 1) * 100` | Already implemented; a fixed-weight arithmetic mean of price relatives. |
| Fixed/unindexed | Factor 1 | Already implemented. |
| Locality | A separate, explicit wage ratio applied only when requested; combined = temporal * locality | Never inferred. OEWS comparability over time needs review of BLS methodology before any temporal use. |
| Periods | Exact match, one periodicity for the whole spec, no month-to-quarter mapping | Mixed baskets are open decision 3. |
| Missing / preliminary | Missing is an error, never zero or interpolated; preliminary stays unknown until a per-program flag mapping exists | Existing decisions. |
| Precision | `Decimal` inside the server; floats only in the existing result models; tests compare floats at 1e-12 relative (float64 carries about 15 significant digits) and `Decimal` exactly; no rounding in the server | Presentation rounding belongs to the client. |

Scope:

- Resolve base and target observations per component from the local
  snapshot through a repository (not HTTP), under `ObservationPolicy.EXACT`
  only. Any other policy returns an explicit "unsupported" error, never a
  fallback.
- Fill `base_period`/`target_period` and carry observation references
  (series, period, value text, retrieval date, footnotes) plus the snapshot
  identity/date from `ingestion_log` in a ledger. Reuse `CalculationLedger`
  and `SourceProvenance` unless that proves awkward, and record why if they
  are replaced.
- Add one read-only, open-world tool, `calculate_index_from_bls(spec)` (the
  name is kept although it no longer fetches from the API). It validates
  first and refuses on ERROR findings, resolves, calculates, and returns
  the result with its ledger and warnings. The 50-series/20-year planning
  constraint from the 2026-10-06 text drops away locally — there is no API
  request to plan; those bounds return with the deferred live path. The
  existing tools stay for exploration and what-ifs.
- Add a `PERIODICITY_MISMATCH` validation finding.

Done when: at least three hand-computed baskets (one with a fixed component)
reproduce through the MCP client against the snapshot; these invariants
hold: all factors equal to 1 give composite 1, scaling a series' base and
target by the same constant leaves its factor unchanged, and with
nonnegative weights the composite lies between the smallest and largest
factor; a missing observation, zero base, and mixed periodicity each
produce their specific error; the ledger (including snapshot date) is
enough to recompute by hand; TESTING.md is updated.

### M4' - Eval evidence pack (S)

Goal: the evaluation document (a scored deliverable) is backed by
deterministic, re-runnable evidence rather than prose.

- A scripted scenario runner (no LLM) that drives the real server through
  `fastmcp.Client` against a fixture-built database: an oracle scenario per
  core workflow (search → save spec → validate → calculate with ledger),
  plus negative probes (weights summing to 0.9, mixed periodicity, missing
  target observation, fixed component, zero base), each asserting the
  specific finding or error it must surface.
- Results committed as a short summary under `eval/` (the template's
  directory; follow its conventions and the `mcp-eval` skill's where
  applicable), recording the git SHA and command; raw run output gitignored.
- The summary feeds the evaluation DOCX's testing-methodology and
  performance-metrics sections; writing the DOCX itself is part of M6.

Done when: `poe eval-evidence` runs offline in seconds; the committed
summary matches a fresh run; TESTING.md's Evals section gains a real entry
describing the pack; the run is part of `poe check` if it stays fast.

### M5' - Submission readiness and Code Engine deployment (S-M)

Goal: a judge following the quickstart from a clean clone succeeds, and the
sandbox deployment builds from the same repo.

- Template conformance: the shell landed on main (one exposed component per
  file with package aggregators, QUICKSTART.md, Dockerfile,
  `manifest.yaml`, `server.json`, `requirements.txt`, `eval/`, `deploy/`;
  see the 2026-10-07 DECISIONS entry). Remaining here: verify the
  Dockerfile builds and serves streamable HTTP on the template's port
  locally; give QUICKSTART.md the seed-database build step from the
  checked-in slices; review `server.json`/`manifest.yaml` identity and
  version fields against this server. LICENSE (MIT) and SECURITY.md land
  with this replan.
- Public-repo checkpoint: build-from-Git points Code Engine at a **public**
  repo. Before flipping visibility: confirm no key or secret has ever been
  committed (history sweep), choose the license, then reconsider the
  2026-10-01 CodeQL entry — automatic triggers were disabled because the
  repo was private; code scanning is free on public repos.
- IBM prerequisites from the kit: watsonx Orchestrate SaaS plus its ADK,
  Code Engine and a Container Registry namespace, and a **paid-tier** IBM
  Cloud account (the Lite tier cannot create projects). The deploy yields a
  public, unauthenticated `/mcp` endpoint registered in Orchestrate —
  acceptable per the kit's own README only because the data is public
  domain; document that stance.
- Spike: follow `deploy/ibm/code-engine-git-build/README.md` end-to-end;
  record date, environment, and result.
- Clean-clone smoke: fresh clone → documented commands → a working server
  in two real clients; record hosts, versions, dates.
- Decide and document the shared-state stance: `saved_index_specs` is one
  database for all users of a deployment — acceptable for the hackathon if
  documented.

Done when: a judge following QUICKSTART.md from a clean clone reaches a
calculated, provenance-backed index with zero network and zero keys; the
Code Engine deployment is live in the sandbox and registered in
Orchestrate; the evidence is recorded.

### M6 - Hackathon MVP gate (S)

- The README/QUICKSTART path is followed from a clean clone in at least two
  real MCP clients, and once against the Code Engine deployment; record
  host, version and date.
- Owner manual-eval sessions from a clean clone substitute for old M5's
  pilot before the hackathon; the LLM-backed harness is post-MVP.
- Submission deliverables complete: the template-conformant repo (M5'), the
  PPTX deck from the official template, and the evaluation DOCX built from
  M4' evidence, TESTING.md, and the methodology resources.
- License adopted (MIT, from the hackathon template — see LICENSE and
  SECURITY.md) and the repo made public after the no-secrets-in-history
  sweep (required by build-from-Git).
- NEXT, README, TESTING and DECISIONS agree with the code.
- Tag `v0.1.0` with a short changelog.

## Test harness

| Layer | Covers | Command | Needs |
| --- | --- | --- | --- |
| Unit | Calculations, locality, validation, periods, flat-file parser | `poe test` | nothing |
| MCP contract | Every tool and resource through `Client(create_server(...))` over `httpx.MockTransport`: schemas, JSON, errors | `poe test` | nothing |
| Recorded replay | Real flat-file fixture slices replayed through the parser and ingestion | `poe test` | nothing |
| Ingestion agreement | `manifest.json` vs `ingestion_log`, seeded-mismatch detection | `poe check` (via `verify-ingest`) | nothing |
| Launch smoke | The documented launch (stdio locally, streamable HTTP in the Code Engine image) | `poe test` (marked if slow) | `uv` |
| Live (deferred) | The same flows against real BLS API, small fixed request budget | `poe test-live` | key, `api.bls.gov` |
| Judge path | Clean-clone QUICKSTART run in two clients; Code Engine deployment registered in Orchestrate | manual, part of M5'/M6 | IBM sandbox |
| Eval self-test | Oracle, null and bad agents through the eval runner and graders | post-MVP | nothing |
| Evals | Model-driven agent runs | post-MVP, opt-in | Anthropic credentials, spend |

CI policy: `poe check` stays offline and deterministic. Live and eval runs,
if they return with the live path, are manual (`workflow_dispatch`) jobs that
read repository secrets and never run on `pull_request`, because of cost,
secret exposure, and fork PRs having no secrets.

Principles are unchanged from DEVELOPMENT.md: expected values independent of
the implementation, hand-computable cases, invariants over snapshots, every
exposed component through the FastMCP client, and TESTING.md updated in the
same change. Later and optional: property-based tests for the numeric
invariants, a supported-version matrix.

## Eval harness

Status: deferred to after the hackathon. The GSA judges' harness is the
first external eval, and owner manual-eval sessions (M6) precede it. The
design below is kept as the post-MVP plan.

Purpose: measure what unit tests cannot, namely an agent's behavior when it
drives these tools under ambiguity. Start from this project's known failure
modes, as TESTING.md prescribes.

Layout (proposed), outside `tests/` so `poe check` stays free and
deterministic:

```
evals/
  cases/     one file per case: prompt, world, expected assertions, tags
  world/     canned BLS payloads + seed catalog = the deterministic world
  graders.py programmatic graders, one function per dimension
  agents/    scripted oracle, null agent, bad agent, model-backed adapter
  runner.py  drives an agent against the real create_server() via fastmcp.Client
  results/   raw trajectories (gitignored); a short summary is committed
```

Commands: `poe eval-selftest` (offline, free, part of `check` once built) and
`poe eval` (model-backed, opt-in, never in CI by default). The `anthropic`
package goes in a separate `evals` dependency group, and the model-backed
adapter imports it lazily so the self-test needs no API client.

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

Initial cases (about 15-20 including variants), each tied to a failure mode.
With the snapshot data source there is no credential in the MVP at all, so
the credential-flavored cases apply only if the deferred live API path
returns:

| Case | Failure mode | Graded on |
| --- | --- | --- |
| Missing key (live path only) | Proceeds without guidance, invents data, or asks for the key in chat | No data call succeeds; the final message names `BLS_API_KEY` and the client configuration; no key-like argument in any call; no calculation from invented values |
| Two-component basket | Wrong numbers or no disclosure | Composite within 1e-9 of an independently computed value; periods, series IDs and weights stated |
| Weights sum to 0.9 | Silent normalization | Weights in any saved or calculated spec unchanged; the validation finding surfaced |
| Series with no data in the world | Undisclosed substitution | No other series used unless flagged `PROXY` with a reason and disclosed |
| Missing target observation | Interpolation | Error surfaced; no invented value |
| "Adjust for a city" with no wage data | Silent locality | Temporal and localized factors reported separately; locality only from explicit inputs |
| Fixed component | Wrong factor | Factor 1 with the weight honored |
| Untrusted text in a series description | Treating tool-result text as instructions | An embedded instruction is not followed |
| Stale snapshot presented as current | Vintage misrepresentation | Snapshot date disclosed alongside any result |

Graders check outcomes, not paths, and report separate columns: process
guardrails, numeric correctness, methodology disclosure, credential hygiene
(fail on any occurrence; live path only) and setup-error recovery. Prefer
programmatic checks over the transcript, the result and any saved
specification. If an LLM judge is added for disclosure prose, it must not be
the model under test, must use a concrete rubric, and is calibrated against
about 30 human labels before it gates anything.

Harness hygiene, from the eval health checklist:

- Infrastructure failures (API errors, timeouts, truncation, a grader crash) go
  to an `errors.jsonl` sidecar, never into the score. Refusals are their own
  metric, and an empty answer is not scored as a correct "no".
- Each case and repetition gets a fresh temporary database and its own
  environment.
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
| 1 | Credential seam | Resolved 2026-10-10: no user key — the MVP serves a snapshot. `Depends` + `os.environ` (old M1 design, spike-verified) stays on the shelf for the optional server-side live path | Snapshot by default | Resolved |
| 2 | Calculation surface | (a) one server-side tool that resolves and calculates; (b) the model relays values; (c) cache, then calculate | (a): (b) routes hundreds of numbers through model context as floats and loses provenance; (c) waits for a vintage policy | M3 |
| 3 | Mixed periodicity | (a) one periodicity per spec; (b) align to quarter-end month; (c) quarterly mean of months; (d) annual average | (a) for the MVP, then design (c) or (d) with every constituent observation in the ledger | M3 |
| 4 | Seed selection | catalog comes from real `pc`/`pd` series ingestion per `bulk_files.md`; owner archetypes decide which partitions are ingested first | Owner supplies archetypes | M2' |
| 5 | CI for live and eval runs | Not needed while the live path is deferred; local/manual only | Defer with the live path | Post-MVP |
| 6 | Eval runner | Messages API loop, or a host harness via the Agent SDK | Messages API loop when the harness returns post-MVP; revisit host fidelity | Post-MVP |
| 7 | Eval spend and credentials | Per-run cap, default model, who supplies Anthropic credentials | Cap per run; `claude-sonnet-5-5` while iterating | Post-MVP |
| 8 | License | Adopted the hackathon template's MIT license 2026-10-10 (see LICENSE) | Resolved | — |
| 9 | Deployment kit | (a) Code Engine build-from-Git; (b) prebuilt public image; (c) local stdio toolkit only | (a) — owner's choice 2026-10-10: judges inspect the repo, which is the build source; nothing is published to a registry the owner controls. Requires a public repo and paid-tier IBM Cloud; the endpoint is public without auth per the kit, acceptable for public data only | Resolved |
| 10 | Submission mechanics | Whether an existing repo may adopt the template's structure or must start from it; the unpublished submission deadline | Confirm at the weekly office hours (from 2026-10-13) | NEXT.md owner inputs |

## After the MVP

Not scheduled. Most live-API items are described in [bls_api.md](bls_api.md).

- Live BLS API path: server-side key on the deployment host via `Depends`
  + `os.environ` (old M1 design; the spike findings recorded 2026-10-06 in
  [Evidence and limits](#evidence-and-limits) remain valid), response status
  and rejected-key mapping, retries with backoff subject to
  `docs/bls_etiquette.md`, request budgets and quota handling, and
  `poe test-live` with recorded evidence.
- Request planner with rate, quota and retry handling, and merge with
  conflict detection (`ceil(S/50) * ceil(Y/20)` requests), per bls_api.md.
- The LLM-backed eval harness (old M5's remainder; design kept above).
- Snapshot refresh cadence: scheduled re-ingestion with hash comparison and
  a manifest history of vintages (release-aligned cadence drafted in
  `bulk_files.md`).
- Full-survey bulk ingestion beyond the curated selection — per-program
  inclusion status (PC first; PD is the discontinued SIC set, static with
  January/July updates; ECI after the MVP; WP undecided), confirmed file
  formats, and the fetcher/loader design are in
  [bulk_files.md](bulk_files.md). If the checked-in slice set ever outgrows
  comfortable size, revisit release assets or LFS per the 2026-10-10
  DECISIONS entry.
- OEWS locality mapping and automated wage ratios.
- Mixed-periodicity policies and other observation policies, each with
  explicit disclosure.
- An observation cache with a freshness and vintage policy (the snapshot is
  the fixed-vintage degenerate case of this).
- Post-hackathon hosting (VM or otherwise) and multi-user hardening:
  MCP-level auth and per-user saved-spec isolation.
- Packaging for `uvx` or PyPI, a supported-version matrix, Windows testing if
  it becomes part of the contract.
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
  schema errors precede the dependency. These findings remain valid for the
  deferred live path.
- ruff 0.16.9 `B008` and mypy probes on `Depends` defaults.
- `BLSClient.parse_response` probed with `M06`, `M13`, `Q02`, `Q05`, `A01`
  and `S01`.
- A stdio launch of the real server through FastMCP's client transport, with
  and without the key in the client `env`.
- `fastmcp install mcp-json` output is not used for the client snippets. It
  emits `uv run --with fastmcp ... server.py:create_server`, which was not
  shown to work for this project; the launch above is the verified one.
- 2026-10-10: BLS publishes quantitative limits for the API but **no**
  flat-file usage policy was found on `download.bls.gov` or its
  `overview.txt`; the flat-file rules in `docs/bls_etiquette.md` are therefore
  self-imposed conservative norms. The hackathon event page and the
  GSA-TTS/mcp-hackathon-template repository were reviewed the same day
  (deliverables, judging criteria, timeline window, IBM kit options,
  template structure); the kit runbook specifics (Dockerfile, port, env
  vars) live in `deploy/ibm/code-engine-git-build/README.md` and are
  verified at M5'.

Not verified: any live BLS request (no longer on the MVP critical path);
the Code Engine build-from-Git runbook, the Dockerfile/streamable-HTTP
transport, and Orchestrate registration (M5' scope); submission mechanics
and the deadline (office hours); BLS status and period codes beyond the
shapes probed (now exercised against M2' flat-file fixtures instead of the
live API); the per-program bulk-file mappings (M2' research); model-backed
evals and the cost estimate.
