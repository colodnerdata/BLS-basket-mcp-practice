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
  a local loopback HTTP smoke workflow has been validated with mocked BLS.
  Live BLS calls, remote deployment, and real stdio hosts remain unvalidated. Pre-scaffold
  SQLite databases with the old incomplete series schema need a deliberate
  migration or recreation; no production migration framework is introduced.

- Flat-file cache: plan drafted in `bulk_files.md` (PC, PD, ECI, later OEWS;
  release-aligned conditional refresh). PC/PD file formats are now
  confirmed from `docs/sample_data/`. PD data and the product
  mappings are also confirmed. PC data is confirmed too.
  Next action: run `scripts/probe_bls_headers.py pc` from a networked machine
  and commit its JSON (the remaining header check in "Verify first"). ECI is
  deferred past the MVP but stays in the plan; `wp` is undecided.

- Template layout: all exposed tools/resources now live in individual files
  and use package aggregators. Maintain this layout for future additions;
  see `AGENTS.md` and `hackathon_template.md`.

- Local workflow: `poe serve` launches the existing app; `poe smoke` checks
  running loopback HTTP with no Node.js, BLS requests, or specification writes.
  Configure `.env` without terminal environment injection. See `QUICKSTART.md`.
  Agent evals remain unimplemented; the smoke command is not an eval runner.
