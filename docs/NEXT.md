# Next

- Current goal: reach an MVP: the BLS key comes from the client's server
  configuration with a client-side setup error, plus test and eval harnesses
  and a source-backed observation-to-calculation workflow. Plan and milestones
  are in `ROADMAP.md`.
- Access guidance: configuration-only status and setup resource are implemented;
  live MCP calls require a key and enforce 50-series/20-inclusive-year bounds.
  See `bls_api.md` for limits and the planned batching/result-envelope contract.
  Explicit verification, anonymous fallback, and hosted credentials are deferred.
- Working state: FastMCP 3.2.4, typed MCP contracts, lifespan-owned services,
  client integration tests, and automated type checking are implemented.
- Next action: M0 (test-harness foundation), then M1 (BLS key through FastMCP
  `Depends` and `os.environ`, with a setup error that explains the client-side
  configuration). The source-backed workflow is now M3. The MVP uses a curated
  seed catalogue; confirm authoritative BLS bulk-file mappings before any
  catalogue ingestion, which comes after the MVP. Blockers for M2 and M4: the
  owner's registered BLS key, network access to api.bls.gov, and the open
  decisions in `ROADMAP.md`.
- Before live use: explicitly handle program-specific period encodings
  (including annual averages), invalid periods currently skipped by the parser,
  preliminary flags, response status variants, API limits/retries, and vintages.
  Configured retry count remains a deferred seam; no retry behavior is claimed.
  The parser items are milestone M2 in `ROADMAP.md`.
- Verification boundary: in-memory MCP and mocked HTTP integration are covered;
  live BLS calls and network transports have not been validated. Pre-scaffold
  SQLite databases with the old incomplete series schema need a deliberate
  migration or recreation; no production migration framework is introduced.

- Template layout follow-up: migrate legacy grouped tools/resources and direct
  factory registration to one exposed component per file and package
  aggregators. Apply the rule to new/touched components immediately; a full
  migration is separate from the current MVP milestones. Preserve names,
  schemas, annotations, and lifecycle; verify client discovery/invocation and
  update `TESTING.md`. See `AGENTS.md` and `hackathon_template.md`.
