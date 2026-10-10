# Next

- Current goal: a hackathon-ready MVP for the GSA MCP Server Hackathon
  (kickoff 2026-10-19, halfway check-in 2026-11-03, closing ceremony
  2026-12-16; the submission deadline is not yet published). Deliverables:
  this repo aligned to GSA-TTS/mcp-hackathon-template, a slide deck, and an
  evaluation document. Judges clone and run the server locally with zero
  setup and no keys; the sandbox deployment uses the IBM watsonx Orchestrate
  kit's Code Engine build-from-Git option (owner's choice 2026-10-10 — the
  repo is the build source, no build artifact is published). Plan in
  `ROADMAP.md`; decisions in `DECISIONS.md` (2026-10-10).
- Data source: curated BLS flat-file slices checked into git, ingested into
  SQLite wherever needed (developer machine, CI, image build) — zero
  network at run time. `data/manifest.json` (git) and `ingestion_log`
  (database) record each ingested file with its sha256.
- Working state: FastMCP 3.2.4, typed MCP contracts, lifespan-owned
  services, client integration tests, and automated type checking are
  implemented; `poe check` passes.
- Next action: M0 (test-harness foundation), then M2' (flat-file ingestion
  + parser fixtures + manifest/`ingestion_log` + `poe verify-ingest` +
  curated seed). M2' starts with confirming authoritative per-program
  bulk-file mappings from BLS documentation — the plan's main research
  risk. Then M3 (local observation resolution), M4' (deterministic
  eval-evidence pack), M5' (template conformance + Code Engine spike).
- Owner inputs needed, mostly via the weekly office hours (Tuesdays from
  2026-10-13) or mcp@gsa.gov: the submission deadline; whether an existing
  repo may adopt the template's structure or must be based on it; IBM Cloud
  account tier (Code Engine needs paid) and watsonx Orchestrate access;
  confirmation the registration is active. Also: basket archetypes for the
  seed selection, and whether/when to make the repo public (required for
  build-from-Git — do the no-secrets-in-history sweep and license choice
  first, M5').
- The key-based live path (client-configured `BLS_API_KEY`, `Depends`
  provider, live-API readiness) is deferred and optional; see "After the
  MVP" in `ROADMAP.md`.
- Parser work — program-specific period encodings including `M13`/`Q05`/
  `S01`/`A01` and annual averages, codes currently dropped silently,
  preliminary flags, unknown-code handling — happens in M2' against
  checked-in flat-file fixture slices. Live-API-only items (retries,
  rejected-key mapping, quota envelopes) are deferred with the live path.
- Verification boundary: in-memory MCP and mocked HTTP integration are
  covered; live BLS calls, the Dockerfile, and network transports have not
  been validated (M5' scope). Any download or live call follows
  `bls_etiquette.md` (owner-invoked, one fetch per file, evidence
  recorded). Pre-scaffold SQLite databases with the old incomplete series
  schema need a deliberate migration or recreation; no production migration
  framework is introduced.
