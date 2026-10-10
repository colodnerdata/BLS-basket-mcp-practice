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
  failures and broken catalogue persistence.
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

- **Status:** accepted.
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

- **Status:** proposed; plan only, nothing implemented.
- **Decision:** Plan to cache `download.bls.gov/pub/time.series` flat files
  (PC, PD first; then ECI, OEWS; evaluate WP) with release-aligned conditional refresh,
  run outside MCP handlers. The API path stays for ad hoc lookups.
- **Why:** No per-call quota or key for bulk reads, a real series catalogue,
  and reproducible provenance (file validators and hashes).
- **Correction (2026-10-10, after reading the saved BLS docs):** PD is the
  discontinued SIC-based PPI, not commodity data; it is static (updated each
  January and July), so only PC needs monthly refresh. Commodities are `WP`.
  `pd.series` rows have one more field than its header; see `bulk_files.md`.
- **Open:** Unverified facts are listed in `bulk_files.md` ("Verify first").
  Vintage policy for revised PPI values is required before observations are
  served from cache.
- **Revisit when:** The verify-first checklist is done.
