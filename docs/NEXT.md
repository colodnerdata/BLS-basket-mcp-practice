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
  implemented; `poe check` passes (including `verify-ingest`). The
  template-aligned shell landed on main (one component per file,
  `main.py`/`app.py`/`routes.py`, Dockerfile, `manifest.yaml`,
  `server.json`, QUICKSTART.md, `eval/`). M0 landed in PR #11. M2'
  groundwork landed in PR #12: PC/PD parsers, `ingestion_log` +
  `data/manifest.json` dual provenance, `poe build-catalog` /
  `poe verify-ingest`, and a catalog of all 21,949 PC/PD series
  ingested offline from the checked-in samples.
- Next action: M2' remainder — the conditional-GET fetcher (verified by
  the 2026-10-10 header probe: all `pc/` files honor 304; ETag is a
  per-release stamp, so the manifest sha256 is the revision signal) and one
  owner-invoked live download of the basket-relevant data partitions.
  First archetype is **vertical construction** (owner, 2026-10-10):
  materials through labor. Candidate partitions: 10.Wood, 13.PetroleumCoal
  (asphalt), 16.NonmetallicMineral (cement/aggregate), 17.PrimaryMetal,
  18.FabricatedMetal, 19.Machinery (HVAC), 21.ElectricalMachinery,
  75.Construction. Caveats: raw materials may map better to the `wp`
  commodity program (owner decision still open). Labor enters the MVP via
  ECI (`ci`) per the 2026-10-10 scope decision — next ECI step is
  owner-run: fetch the small `ci.txt`/`ci.series`/mapping files per
  `bls_etiquette.md` into `docs/sample_data/` so its quarterly period codes
  can be verified before parsing. OEWS (`oe`) localization (mapping and
  automated wage ratios) is the deferred piece. Then M3 (observation resolution over the
  snapshot), M4' (eval evidence pack), M5' (Code Engine spike).
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
