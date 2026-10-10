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
- Data source: BLS flat files ingested into SQLite, with per-file provenance
  (URL, retrieval time, validators, sha256) recorded in
  `data/manifest.json` (git) and the `ingestion_log` table (database), so
  any device can rebuild the database. Detailed format findings, cadence,
  and the fetcher/loader design live in `bulk_files.md`.
- Working state: FastMCP 3.2.4, typed MCP contracts, lifespan-owned
  services, client integration tests, and automated type checking are
  implemented; `poe check` passes. The template-aligned shell landed on
  main: one exposed component per file with package aggregators,
  `main.py`/`app.py`/`routes.py`, Dockerfile, `manifest.yaml`,
  `server.json`, QUICKSTART.md, and `eval/`. M0 (test-harness foundation)
  lands in PR #11: environment key isolation in `tests/conftest.py`, the
  shared canned-payload harness in `tests/harness.py`, the `live` marker
  with opt-in `poe test-live`, and the `poe test-cov` diagnostic.
- Next action: M2' flat-file ingestion. The mapping research is largely
  done in `bulk_files.md`: PC/PD file formats are confirmed from the
  checked-in `docs/sample_data/` files; remaining verification is a header
  probe from a networked machine (`scripts/probe_bls_headers.py pc`). ECI
  is deferred past the MVP; `wp` (PPI commodities) is undecided. Then M3
  (local observation resolution), M4' (deterministic eval-evidence pack),
  M5' (remaining submission readiness + Code Engine spike).
- Owner inputs needed, mostly via the weekly office hours (Tuesdays from
  2026-10-13) or mcp@gsa.gov: the submission deadline; whether an existing
  repo may adopt the template's structure or must be based on it; IBM Cloud
  account tier (Code Engine needs paid) and watsonx Orchestrate access;
  confirmation the registration is active. Also: basket archetypes for M3
  verification, and whether/when to make the repo public (required for
  build-from-Git — do the no-secrets-in-history sweep first; license is in
  place via PR #10).
- The key-based live path (client-configured `BLS_API_KEY`, `Depends`
  provider, live-API readiness) is deferred and optional; see "After the
  MVP" in `ROADMAP.md`.
- Parser work — program-specific period encodings including `M13` (annual
  average; present in both PC and PD despite `pd.txt` saying otherwise),
  preliminary (`P`) and correction (`C`) footnotes — happens in M2' against
  fixture slices cut from `docs/sample_data/`. Live-API-only items
  (retries, rejected-key mapping, quota envelopes) are deferred with the
  live path.
- Verification boundary: in-memory MCP and mocked HTTP integration are
  covered; live BLS calls, the Dockerfile, and network transports have not
  been validated (M5' scope). Any download or live call follows
  `bls_etiquette.md` (owner-invoked, conditional requests, evidence
  recorded). Pre-scaffold SQLite databases with the old incomplete series
  schema need a deliberate migration or recreation; no production migration
  framework is introduced.
