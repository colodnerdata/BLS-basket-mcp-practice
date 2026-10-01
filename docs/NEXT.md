# Next

- Current goal: review and merge PR #1's hardened FastMCP scaffold.
- Working state: FastMCP 3.2.4, typed MCP contracts, lifespan-owned services,
  client integration tests, and automated type checking are implemented.
- Next action: complete one source-backed fixture workflow with observation
  selection and provenance, then confirm authoritative BLS bulk-file mappings
  before implementing catalogue ingestion.
- Before live use: explicitly handle program-specific period encodings
  (including annual averages), invalid periods currently skipped by the parser,
  preliminary flags, response status variants, API limits/retries, and vintages.
  Configured retry count remains a deferred seam; no retry behavior is claimed.
- Verification boundary: in-memory MCP and mocked HTTP integration are covered;
  live BLS calls and network transports have not been validated. Pre-scaffold
  SQLite databases with the old incomplete series schema need a deliberate
  migration or recreation; no production migration framework is introduced.
