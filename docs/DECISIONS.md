# Decisions

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

- **Status:** accepted.
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
