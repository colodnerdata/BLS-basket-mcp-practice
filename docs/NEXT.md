# Next

- Current goal: complete a source-backed observation-to-calculation workflow.
- Access guidance: configuration-only status and setup resource are implemented;
  live MCP calls require a key and enforce 50-series/20-inclusive-year bounds.
  See `bls_api.md` for limits and the planned batching/result-envelope contract.
  Explicit verification, anonymous fallback, and hosted credentials are deferred.
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
