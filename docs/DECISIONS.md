# Decisions

## 2026-10-07 — GSA hackathon project shell

- **Status:** accepted.
- **Decision:** Add the GSA launch/deployment/documentation shell around the
  existing factory and lifespan. Separate transport configuration from BLS
  settings; load local `.env` with environment precedence. Preserve existing
  stdio entry points. Verify APIs against installed FastMCP 3.2.4.
- **Why:** Template launch conventions and probes support platform integration
  without replacing reviewed typed adapters, services, or persistence.
  Prefer locked dependencies and Python 3.12 over the template's image defaults.
- **Deferred:** License choice, registry publication, vendor account-specific
  kits, authentication/tenant isolation, reusable prompts, and agent evals.
  Draft metadata has no invented remote URL; cloud.gov starts with no route.
- **Reference:** [Pinned template and mapping](hackathon_template.md).
- **Revisit when:** A concrete approved hosted demo needs platform identity,
  persistence, and access controls; do not infer those from shell files.

Record the choices future-you or a coding assistant might otherwise repeat.
Add an entry when a decision affects interfaces, architecture, dependencies,
data formats, verification, or a meaningful constraint. Keep entries short.

Preserve the original reasoning when a decision changes. Mark the old entry
superseded and link to the new one. Record rejected alternatives when the
reason is likely to be useful again. Search by mechanism before proposing a
design change.

## Entry pattern

- **Date and title:** YYYY-MM-DD — the decision in a few words.
- **Status:** accepted, rejected, deferred, or superseded (with a link).
- **Context:** the problem and constraint.
- **Decision:** what we chose.
- **Why:** the tradeoff and important alternative.
- **Revisit when:** evidence or a changed condition that would alter the choice.



## 2026-09-30 — FastMCP 3.2 contracts and lifecycle

- **Status:** accepted.
- **Context:** The scaffold allowed FastMCP 2.14.7 despite PR #1's claimed
  upgrade; untyped inputs and a registration-only test missed JSON boundary
  failures and broken catalog persistence.
- **Decision:** Support `fastmcp>=3.2.0,<3.3`, with 3.2.4 resolved in `uv.lock`.
  Keep explicit per-module registration functions, typed decorated adapters,
  and the server factory. FastMCP generates contracts from Pydantic models.
  Use its supported async-context-manager lifespan and `Context` injection
  to create services after startup and close the shared HTTP client on exit.
  Keep SQLite connections local to repository operations. No FastAPI layer.
- **Why:** A minor-version bound limits unreviewed API drift while the lockfile
  makes installation reproducible. Global services and per-handler database
  initialization hide configuration and cleanup ownership. FastMCP context
  keeps dependencies out of the public schema and allows isolated servers.
- **Errors:** Expected domain failures become `ToolError`; validation findings
  remain structured output. Unexpected errors are masked. Missing/empty or
  non-finite BLS values raise a domain error; real zero values remain zero.
  Preserve footnote text; preliminary status stays unknown until an
  authoritative program-specific flag mapping is implemented.
- **Save semantics:** Existing IDs are overwritten and `updated_at` changes;
  hints are non-read-only, destructive, non-idempotent, closed-world.
- **Verification:** Client tests exercise all ten tools and three resources,
  generated schemas, JSON deserialization, hand-calculated composites,
  save/read/overwrite, fresh database startup and shutdown after failure.
  Mypy is included in the same `poe check` task used by CI.
- **Revisit when:** A reviewed dependency upgrade changes contracts/lifecycle,
  or production ingestion needs explicit retries, vintages, and migrations.
- **Official references:** [Tools](https://gofastmcp.com/servers/tools),
  [Lifespans](https://gofastmcp.com/servers/lifespan),
  [Client testing](https://gofastmcp.com/servers/testing),
  [Project configuration](https://gofastmcp.com/deployment/server-configuration).
  APIs were also checked against installed FastMCP 3.2.4.

Observation values stay Decimal internally and serialize as decimal strings
with a plain string output schema. This preserves exact text while avoiding
Pydantic Decimal regexes that the FastMCP 3.2.4 client cannot reconstruct.
Series resources return explicit `ResourceResult`/`ResourceContent` with JSON
MIME types, verified on resource reads as well as discovery.


## 2026-10-01 — Repository-owned CodeQL scanning

- **Status:** superseded by
  [CodeQL scanning disabled pending GitHub Advanced Security](#2026-10-01--codeql-scanning-disabled-pending-github-advanced-security)
  for automatic runs; the workflow configuration below is still accepted.
- **Context:** PR #1 had ordinary checks and Copilot review, but no CodeQL
  workflow or CodeQL check on the hardened commit.
- **Decision:** Use advanced setup committed with the code, scanning Python
  and GitHub Actions with default security queries and no path exclusions.
  Run on pull requests, main pushes, weekly, and manual dispatch. Pin CodeQL
  v4 to a verified upstream commit; retain least-privilege job permissions.
- **Why:** Reviewable configuration follows the existing pinned CI practices.
  Default setup is an alternative, not an additional scanner to enable.
- **Revisit when:** More languages or a concrete need for extended queries
  appears. Dependency vulnerability alerts remain separate from code scanning.
- **References:** [GitHub advanced setup](https://docs.github.com/en/code-security/how-tos/find-and-fix-code-vulnerabilities/configure-code-scanning/configuring-advanced-setup-for-code-scanning),
  [Official workflow template](https://github.com/actions/starter-workflows/blob/main/code-scanning/codeql.yml).


## 2026-10-01 — CodeQL scanning disabled pending GitHub Advanced Security

- **Status:** accepted.
- **Context:** The repository is private. Code scanning's SARIF upload
  requires GitHub Advanced Security (GHAS) to be enabled on a private repo;
  it is not, so every run of the `CodeQL` workflow from the prior decision
  fails at the "Perform CodeQL analysis" step with "Code scanning is not
  enabled for this repository," not a scan finding. This blocked PR #3 as a
  required-looking red check with no code fix available.
- **Decision:** Remove the `push`/`pull_request`/`schedule` triggers from
  `.github/workflows/codeql.yml`, keeping only `workflow_dispatch`. The
  workflow configuration itself (advanced setup, pinned CodeQL v4, Python and
  GitHub Actions matrix, least-privilege job permissions) is unchanged and
  stays accepted per the prior entry; only automatic triggering is disabled.
- **Why:** The workflow cannot succeed without a repository-settings change
  (Settings > Code security > GitHub Advanced Security) that only a repo
  admin can make, and that is a cost/plan decision outside this change's
  scope. A red, unfixable-by-code check on every PR trains reviewers to
  ignore CI status. Deleting the workflow outright would lose the reviewed
  configuration; disabling triggers keeps it ready to re-enable.
- **Revisit when:** GitHub Advanced Security is enabled for this repository.
  At that point, restore the `push`/`pull_request`/`schedule` triggers (or
  run the workflow manually first to confirm GHAS is active) rather than
  rewriting the configuration.


## 2026-10-01 — Local BLS access guidance and request bounds

- **Status:** partially superseded by
  [2026-10-10 — Hackathon MVP: flat-file snapshot, build-from-Git deployment, and an ingestion manifest](#2026-10-10--hackathon-mvp-flat-file-snapshot-build-from-git-deployment-and-an-ingestion-manifest).
  The key requirement, setup guidance, and pre-HTTP bounds below now apply
  only to the deferred live-API path; the snapshot data source needs no key.
  "Never collect keys through the model" and "no anonymous fallback for the
  API" remain accepted for that path.
- **Decision:** Advertise setup through server instructions, a typed access-status
  tool, and `setup://bls-api`. Keep keys in the local launch environment; do not
  collect them through the model. Status is missing or configured-unverified and
  performs no HTTP. Require a configured key for live MCP retrieval and reject
  more than 50 series or 20 inclusive years before HTTP. No anonymous fallback.
- **Why:** Guidance belongs in MCP, but credentials remain outside public
  contracts. Configuration and successful data responses do not prove validity.
  Instructions alone cannot enforce setup or request bounds.
- **Deferred:** Explicit credential verification, hosted per-user secret storage,
  URL elicitation, batching, retries, throttling, and quota accounting. Detailed
  batching and consolidated-result requirements are in [bls_api.md](bls_api.md).
- **Compatibility:** Missing-key live MCP calls now fail with setup guidance.
  Non-network tools remain available. Low-level standalone client behavior is
  unchanged. The observation service receives the lifespan-owned access service.
- **References:** [BLS FAQ](https://www.bls.gov/developers/api_faqs.htm),
  [FastMCP instructions](https://gofastmcp.com/servers/server), and
  [MCP elicitation](https://modelcontextprotocol.io/specification/2025-11-25/client/elicitation).
- **Revisit when:** A deployment supports multiple users, or explicit verification
  and multi-request retrieval are implemented and independently validated.


## 2026-10-07 — Template component layout for future work

- **Status:** accepted; supersedes the shell mapping's earlier suggestion to
  keep grouping exposed tools by domain. The existing factory/lifespan and
  domain-service boundaries remain accepted.
- **Decision:** One exposed tool, prompt, or resource per file, each with a
  typed `register(mcp)` function and explicit package aggregation. Apply this
  to every component; the existing grouped modules have been split.
  Keep public contracts stable during
  layout-only migration and register each component exactly once.
- **Why:** The owner requested durable template compliance, including the
  template's one-tool-per-file convention. Canonical agent rules and developer
  instructions now agree; shared logic stays below the MCP handler layer.
- **Implementation:** All existing tools and resources were subsequently
  migrated in this PR to individual modules and package aggregators. Public
  contracts and resource contents are preserved. Layout checks and existing
  FastMCP client tests guard the migration; no grouped adapters remain.

## 2026-10-10 — Plan a BLS flat-file mirror instead of API-only retrieval

- **Status:** proposed; plan only, nothing implemented. Direction adopted for
  the MVP by the accepted hackathon entry below.
- **Decision:** Plan to cache `download.bls.gov/pub/time.series` flat files
  (PC, PD first; then ECI, OEWS; evaluate WP) with release-aligned conditional refresh,
  run outside MCP handlers. The API path stays for ad hoc lookups.
- **Why:** No per-call quota or key for bulk reads, a real series catalog,
  and reproducible provenance (file validators and hashes).
- **Correction (2026-10-10, after reading the saved BLS docs):** PD is the
  discontinued SIC-based PPI, not commodity data; it is static (updated each
  January and July), so only PC needs monthly refresh. Commodities are `WP`.
  `pd.series` rows have one more field than its header; see `bulk_files.md`.
- **Open:** Unverified facts are listed in `bulk_files.md` ("Verify first").
  Vintage policy for revised PPI values is required before observations are
  served from cache.
- **Update (2026-10-10):** the "ECI after the MVP" ordering below is revised
  by the MVP data-scope entry at the end of this document: ECI is the MVP's
  baseline labor source; OEWS localization is the deferred piece.
- **Revisit when:** The verify-first checklist is done.

## 2026-10-10 — Hackathon MVP: flat-file snapshot, build-from-Git deployment, and an ingestion manifest

- **Status:** accepted. Builds on the flat-file mirror proposal above; the
  per-program formats, quirks, and refresh cadence that inform it live in
  [bulk_files.md](bulk_files.md).
- **Context:** The project is an entry in GSA's MCP Server Hackathon (owner,
  2026-10-10; the event page and the GSA-TTS/mcp-hackathon-template repo
  were reviewed the same day). Deliverables are the repo, a slide deck, and
  an evaluation document; prototypes stay in sandbox environments and are
  not publicly deployed. Judges run the server locally in standard MCP
  clients. For the sandbox deployment the owner chose the IBM watsonx
  Orchestrate kit's Code Engine build-from-Git option: the repo is the
  build source judges inspect, and no build artifact is published (the
  prebuilt-image option would publish one; the owner declined it).
  Requiring judges to register BLS keys defeats zero-setup runs, and the
  owner's key must not be shared with unrelated users (see bls_api.md). BLS
  flat files under `download.bls.gov` are anonymous and public-domain;
  checked 2026-10-10, BLS publishes no volume policy for them, so
  `docs/bls_etiquette.md` imposes conservative self-limits.
- **Decision:** The MVP data path is an ingested flat-file snapshot; no
  user keys anywhere. The SQLite database is a build artifact rebuilt
  wherever needed — developer machines, CI, and the Code Engine image all
  build it from the same checked-in inputs (`docs/sample_data/` and fetched
  slices); nothing is committed whole, tracked with Git LFS, or published
  as a release or build artifact. Ingestion is recorded twice —
  `data/manifest.json` in git (authoritative: file IDs, URLs, retrieval
  dates, sha256 hashes, sizes, ingestion timestamps and code versions,
  row/series/observation counts, period-code warning counts, status —
  matching the per-file provenance fields in `bulk_files.md`) and an
  `ingestion_log` table in the database (the receipt). A
  `poe verify-ingest` task checks the two agree, offline. The sha256
  detects silent upstream revision: a hash mismatch on re-download is an
  explicit decision, never a silent overwrite. The live BLS API path
  (per-call `Depends` key, request bounds, retries) is deferred and
  optional.
- **Why:** Zero-setup judging locally and a judge-inspectable build source
  in Code Engine; deterministic, reproducible offline evals; few,
  identified, cached BLS fetches per the etiquette doc; cross-device
  reproducibility through the checked-in manifest. Rejected
  alternatives: per-judge BLS keys (setup burden); sharing the owner's key
  (policy, quota, hygiene); the prebuilt-image kit (publishes a build); Git
  LFS or release assets for the database (unnecessary at curated size; LFS
  versions binaries without deltas against a small account quota);
  committing full raw flat files beyond the sample set (size;
  generated-artifact doctrine in DEVELOPMENT.md).
- **Consequences:** The snapshot date is disclosed in provenance and
  methodology resources, and the server makes no claim of latest data after
  the snapshot. Build-from-Git requires the repo to be **public** and a
  paid-tier IBM Cloud account: making the repo public (after a
  no-secrets-in-history sweep) is part of milestone M5', and the
  2026-10-01 CodeQL entry's revisit condition should be reconsidered then
  (automatic triggers were disabled because the repo was private; scanning
  is free on public repos). The deployed `/mcp` endpoint is public without
  authentication per the kit's design — acceptable only because the data is
  public domain. Old roadmap M1/M2 (key plumbing, live readiness) and the
  LLM-backed eval harness move to after the MVP; the 2026-10-01
  access-bounds entry is partially superseded as noted in its status line.
  An earlier same-day VM-hosting direction was retracted by the owner and
  is recorded here for the history.
- **Revisit when:** The hackathon concludes; a revision/refresh cadence is
  scheduled (already drafted in `bulk_files.md`); the checked-in slice set
  outgrows comfortable size (then reconsider release assets or LFS); BLS
  publishes a flat-file usage policy; or non-public or multi-tenant
  features require authentication and per-user state.


## 2026-10-10 — MVP data scope: materials and baseline labor in, OEWS localization out

- **Status:** accepted. Revises the ECI ordering in the flat-file mirror
  proposal above ("ECI after the MVP") and the matching sentences in
  `bulk_files.md`.
- **Context:** The first basket archetype is vertical construction "from
  the materials to the labor" (owner, 2026-10-10). Labor escalation
  therefore cannot wait past the MVP; geographic localization can.
- **Decision:** MVP data scope is PPI materials (the `pc`/`pd` ingestion
  already landed; whether raw materials map better to the `wp` commodity
  program stays an open owner decision) **plus** the ECI program (`ci`) as
  the baseline labor source, ingested in M2' once its formats are sampled
  and verified. OEWS (`oe`) locality mapping and any automated wage-ratio
  application stay deferred to after the MVP. Locality factors remain
  explicit, user-supplied values only — the methodology rule (never
  inferred, locality and temporal factors reported separately) is
  unchanged.
- **WP resolution (2026-10-10, owner-requested evidence review):** `wp`
  **joins the MVP data scope as the materials layer.** `wp.txt` §1
  documents that the commodity structure organizes products "by similarity
  of end use or material composition, regardless of industry of origin" —
  the basket's unit of account; `pc` industry series (producer revenue by
  NAICS) remain ingested as background. WP series are all price indexes
  (ratio scale; no percent-change families), monthly with `M13` annual
  averages and per-series `YYMM` base dates, with dedicated partitions for
  Lumber (08), Metals (10/10x incl. steel-mill special indexes),
  Nonmetallic minerals (13), Construction services (80) and Inputs to
  construction industries (80i/IP23). Known hazard, recorded: discontinued
  commodity series migrate from WP to the separate WD database between
  releases, so a basket series may legitimately end — under the
  missing-data rule that is an explicit error, and refresh tooling must
  watch for it (a discontinued basket component is a methodology decision,
  never silent substitution). Byte-level verification of `wp.series`
  padding/columns is pending its fetch; the parser follows once the files
  land.
- **Consequences:** ECI is quarterly and PPI is monthly, and the MVP keeps
  the one-periodicity-per-specification rule (open decision 3 (a)), so a
  single basket mixing monthly materials and quarterly labor is still
  refused. Composition paths — an annual-average basket (PPI `M13` with
  ECI's annual-average code) or separate same-periodicity specifications —
  are decided once ECI's period encodings (`Q01`-`Q05`, any `S01`/`A01`)
  are verified against real `ci` files; they are unverified as of this
  decision. The owner fetches the small `ci` documentation/series/mapping
  files per `docs/bls_etiquette.md` and commits them to
  `docs/sample_data/`; ECI parsing and ingestion then follow the same
  verified-format, fixture-tested pattern as PC/PD.
- **Verified the same day:** `ci.txt` and `ci.series` settle the pending
  items (see the CI section of `bulk_files.md`): data periods are
  `Q01`—`Q04` only, with **no** annual-average period code, and ECI's
  `periodicity_code` (`I` index / `Q` 3-month / `A` 12-month percent
  change) decides eligibility — only index (`I`) series are escalation
  inputs. Consequence: monthly PPI materials and quarterly ECI labor still
  cannot share one specification, and an annual-average basket has no ECI
  counterpart, so the MVP composition path is **parallel same-periodicity
  specifications** (e.g. a quarterly labor spec alongside a monthly or
  annual-average materials spec) until open decision 3 is revisited.
  Confirmed on first real data ingestion: ECI files contain explicit
  missing-value rows (`-`, footnote `A`) and rows for ineligible series —
  both are skipped and counted in the manifest (`missing_rows`,
  `skipped_rows`), never stored or fabricated; the "missing is an error"
  rule governs calculation-time resolution, not ingestion.
- **Revisit when:** ECI period codes and value semantics are verified, or
  the hackathon concludes and OEWS localization returns to the plan.
