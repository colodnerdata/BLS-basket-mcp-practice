# Testing and evals

This is the single human-readable record of what the test suite actually
guards against, and of the project's evals status. Update it in the same
change that adds, removes, or changes the intent of a test — a test whose
purpose isn't reflected here is undocumented. Group trivial or parametrized
variations of one idea into a single entry rather than listing each case.

## How to read this document

Each entry names the test(s), the expected value or outcome, and the
concrete mistake it would catch. "Expected value" is the independently
computable result the test checks against (see `docs/DEVELOPMENT.md`'s
testing principles) — not a description of the code path.

## Test harness (M0)

Shared scaffolding lives in `tests/conftest.py` (guarantees) and
`tests/harness.py` (importable helpers), with canned payloads in
`tests/fixtures/bls/` (hand-written, not recordings — see its README).

Guarantees, and what enforces them:

- **No test observes a real `BLS_API_KEY`.** An autouse fixture strips it
  before every test not marked `live`, so a key exported in a developer's
  shell can neither change offline results nor spend quota. `live` tests
  are exempt by design (they only run under `poe test-live`).
- **Nothing live runs by default.** The `live` marker is registered and
  deselected in `addopts`; `poe test-live` selects it, and a collection
  hook skips (never fails) when no key is exported, so CI and `poe check`
  stay offline per `docs/bls_etiquette.md`.
- **One canned-BLS world.** `CannedTransport` records requests, optionally
  asserts each request body, and serves a fixture payload;
  `server_env(...)` runs the real server on a temporary database through
  the real FastMCP client and asserts — for every consumer and on failure
  paths too — that the factory had no persistence side effects and the
  lifespan closed the injected transport. `bls_payload()` returns a fresh
  copy per call so tests cannot mutate each other's data.
- `poe test-cov` is a diagnostic only; it carries no threshold and is not
  part of `check`.

### `tests/test_harness.py` — harness self-tests

| Test | Expected | Guards against |
| --- | --- | --- |
| `test_env_leak_from_prior_test_a` + `_b` (an ordered pair relying on in-module definition order) | `_b` never observes the sentinel key that `_a` leaks into the real process environment | A leaked or shell-exported key silently changing offline results or letting a test spend real quota |
| `test_live_marker_seam` | Deselected in the default run; skipped (not failed) by `poe test-live` without a key; passes with one; no network call in any of these | The live seam accidentally running in `check`/CI, or failing closed instead of skipping cleanly |

## Unit tests

### `tests/test_flat_file.py` — BLS flat-file parsers (PC/PD)

Expected values are hand-checked against the fixture slices in
`tests/fixtures/bls/flatfile/` (bytes cut from the real files in
`docs/sample_data/`).

| Test | Expected | Guards against |
| --- | --- | --- |
| `test_pc_series_padding_and_fields` | `"PCU1133--1133--"` with padding stripped, title/base/periods as in the file | Space-padded fields leaking into stored IDs or metadata |
| `test_pd_series_blank_extra_column` / `test_pd_series_shape_drift_fails_loudly` | PD's undocumented blank 6th column skipped; any other shape → `FlatFileFormatError` | The header/row field-count mismatch silently shifting PD columns (known real quirk) |
| `test_data_file_period_identity_and_precision` | `M13` → `month=None` with exact value `99.0`; `234.780` keeps its 3-decimal scale; `P` footnote captured | Annual averages misfiling as a 13th month; float rounding of index values |
| `test_data_file_unknown_period_is_warned_not_dropped` | Unknown `Q05` row skipped with `warnings["Q05"] == 1` | Silent data loss — skips are always counted into the manifest |
| `test_data_file_header_only_partition_is_empty_not_error` | Header-only partition → 0 rows, no error | Empty partitions (they exist: 72 bytes) failing ingestion |
| `test_data_file_field_drift_fails_loudly` | `FlatFileFormatError` on a 6-field data row | Column-count drift parsing into wrong positions |
| `test_pd_product_quirk_name_in_last_field` / `test_simple_mappings` | `"Secondary products"` read from the last field of a 6-field row; code+name mappings exact | Fixed-position name parsing misreading real mapping rows |
| `test_ci_series_file_parse` | The 4 fixture rows parse with owner/industry/periodicity/estimate codes and quarterly begin/end (construction wages series: 2001-Q1 → 2026-Q2), padding stripped | ECI's 15-column layout misread |
| `test_ci_index_eligibility_gate` | The 3 `I` series are eligible and the `Q` percent-change twin is not | Percent-change or response-rate series leaking into the catalog as escalation inputs |
| `test_ci_mappings` | `I` → "Current dollar index number", `01` → "Total compensation", `2` → "Private industry workers" | CI's name-in-column-2 layout (trailing display metadata) being misparsed as the last field |
| `test_data_file_quarterly_periods` | `Q01` → quarter=1, month=None; out-of-range `Q05` skipped with a counted warning | Quarterly periods misfiled or silently dropped |
| `test_data_file_missing_dash_is_recorded` | A `-` row (footnote `A`) is skipped with `missing_rows == 1` and a parallel fabricated-value row (`abc`) raises `FlatFileFormatError` | The missing-data sentinel ever becoming a stored observation, or hard failures that would make real released files un-ingestible |
| `test_wp_series_file_parse` | 6 rows parse with group/item/seasonal/YYMM-base and titles (`WPS0811` lumber → 2026-M08); the doc's 10-field layout (file has 11: undocumented `footnote_codes`) fails loudly; retired series (`WPS00000000`, `WPS1371`) kept | WP header drift vs `wp.txt`; padding leaks; ended series vanishing |
| `test_wp_mappings` | `08\t11` → "Softwood lumber", `10\t17` → "Steel mill products", `08` → "Lumber and wood products" | The two-code item key or last-field name rule misread |
| `test_classify_file*` (parametrized) | Filenames map to `(program, kind, canonical upstream name)`, stripping `.txt`/`.sample`/`.head`/`.slice`; docs/probe/README files rejected | Misrouting a support file into a parser, or recording a sample's name as a canonical URL |

### `tests/test_manifest.py` — manifest and `verify-ingest`

| Test | Expected | Guards against |
| --- | --- | --- |
| `test_ingest_records_dual_provenance` | Manifest records all 13 fixture files with sha256/counts/repo paths, including the ECI eligibility skips (`skipped_series`) on `ci.series`; saving is byte-stable | Provenance drift, silent eligibility skips, or non-deterministic manifest writes |
| `test_verify_passes_on_consistent_records` | No mismatches after a clean fixture ingestion | False positives in the agreement check |
| `test_verify_catches_tampered_counts_and_hash` | Tampered size/hash/count in a copy → each reported | `verify-ingest` failing to detect a changed input file |
| `test_verify_catches_missing_file_and_log_drift` / `test_verify_flags_unlogged_manifest_entries` | Missing checkout file listed by path; manifest/log disagreements (counts; unlogged entries) each reported | The git record and the database receipt drifting apart |

### `tests/test_fetch.py` — conditional BLS file fetcher

| Test | Expected | Guards against |
| --- | --- | --- |
| `test_flat_file_fetcher_download_and_conditional_304` | A new file download saves the exact bytes and records the User-Agent; a follow-up conditional GET with the manifest's `ETag`/`Last-Modified` returns 304 instead of re-downloading | The fetcher silently re-fetching unchanged files or dropping the required contact-bearing `User-Agent` |
| `test_fetch_many_uses_settings_and_manifest_validators` | `fetch_many` reads the configured `bls_user_agent` and the manifest validators for `If-None-Match`/`If-Modified-Since`, and surfaces an unchanged result without ingesting the file again | The CLI using an unset/invalid user agent, or losing conditional-GET state between the manifest and the network fetch |

### `tests/integration/test_flatfile_ingest.py` — replay of the real samples (offline)

Ingests `docs/sample_data/` (owner-saved real BLS files) into a scratch
database. This is the recorded-replay layer: no network is involved.

| Test | Expected | Guards against |
| --- | --- | --- |
| `test_series_catalog_counts_match_files` | Exactly 4,510 PC + 17,439 PD + 5,312 WP series (verified file row counts), and ECI rows loaded equal the manifest's recorded eligible count with all skips accounted for | Series rows lost, double-counted at scale, or eligibility skips without a record |
| `test_eci_series_metadata_and_eligibility` | `CIS2022300000000I` (construction wages, private industry) is quarterly ECI with units "index (base Dec 2005=100)", 2001-Q1→2026-Q2, active, and searchable; its `Q`/`A` twins are absent | The percent-change families leaking into the catalog, or ECI metadata (base, periodicity, active) mis-set |
| `test_wp_series_metadata_and_activity` | `WPS0811` (softwood lumber) is active WP commodity with units "index (base 198200=100)"; retired `WPS00000000` (ended 1974-M12) is retained but inactive; "Softwood lumber" searchable | The survey-latest `active` rule, WP classification/parent codes, or units mis-set; ended series disappearing instead of flagging |
| `test_pc_series_metadata` / `test_pd_series_metadata` / `test_search_finds_real_series` | Hand-read values from the files (`PCU1133--1133--` base 198112, first `1981-M12`, active; `PDU1011#` SIC, inactive, ends `2003-M13` with a synthesized title; "Logging" searchable) | Mis-mapping real series-file fields into catalog metadata |
| `test_pc_observations_exact_and_preliminary` / `test_m13_is_a_distinct_annual_average` | `Decimal("234.780")` exact; `2026-M05` preliminary with footnote text and series-derived units; `1969-M13` is `ANNUAL_AVERAGE` distinct from `M12` and holds `35.0` | Value precision loss, preliminary-state confusion, and annual-average/month conflation through the full ingest path |
| `test_manifest_and_log_agree_after_ingest` / `test_verify_cli_passes` | Manifest and `ingestion_log` agree; `verify` exits 0 | The dual-record contract breaking end-to-end |

### `tests/test_calculations.py` — `EscalationCalculationService`

| Test | Expected | Guards against |
| --- | --- | --- |
| `test_one_component_weight_one` | `temporal_factor ≈ 1.1` for base 100 → target 110 | Temporal factor drifting from `target / base` |
| `test_if_every_temporal_factor_equals_one_works` | Composite `≈ 1.0` when every component's base equals its target | Weighting/aggregation introducing drift when no escalation occurred |
| `test_locality_factor_one_keeps_localized_equal_to_temporal` | `localized_composite_factor == temporal_composite_factor` when every `locality_factor = 1.0` | Locality factor of 1 failing to be a true no-op; localized/temporal paths diverging |
| `test_fixed_unindexed_component_has_temporal_factor_one` | `temporal_factor ≈ 1.0` for a `FIXED_UNINDEXED` component even with base 100 → target 200 | Fixed/unindexed components being escalated despite the methodology fixing them at 1 |
| `test_order_of_components_does_not_change_result` | Same composite factor with components reversed | Order-dependent (non-commutative) aggregation bug |
| `test_weighted_component_contributions_sum_to_composite_factor` | Composite equals `sum(weight * temporal_factor)` computed independently inline | Composite formula silently diverging from the documented weighted-sum methodology |
| `test_calculate_composite_raises_on_empty_components` | `InvalidWeightsError` for an empty component list | Returning a composite from no inputs instead of failing fast with a clear contract error |
| `test_calculate_composite_raises_when_weights_outside_tolerance` | `InvalidWeightsError` when the component weights differ from 1 by more than tolerance (`1e-4`) | Quietly accepting materially invalid weights and producing a misleading composite |
| `test_zero_base_value_raises` | `CalculationError` | Division by zero returning `inf`/garbage instead of an explicit domain error |

### `tests/test_locality.py` — `LocalityService`

| Test | Expected | Guards against |
| --- | --- | --- |
| `test_labor_locality_factor_for_reference_and_target_wages` | `locality_factor ≈ 1.25` for reference wage 40, target wage 50 | Locality factor formula drifting from `target / reference` |
| `test_zero_reference_wage_invalid` | `CalculationError` | Division by zero in the locality factor |

### `tests/test_validation.py` — `ValidationService`

| Test | Expected | Guards against |
| --- | --- | --- |
| `test_valid_basket` | `valid is True` | False positives on a well-formed basket |
| `test_weights_not_equal_to_one` | `WEIGHTS_SUM_MISMATCH` finding | Silently accepting a basket whose weights don't sum to 1 |
| `test_negative_weight` | `NEGATIVE_WEIGHT` finding | Silently accepting a negative weight (would invert escalation) |
| `test_missing_series_on_indexed_component` | `MISSING_SERIES_ID` finding | An indexed component calculating with no underlying data source |
| `test_series_on_fixed_component` | `FIXED_COMPONENT_HAS_SERIES` finding | A fixed component ambiguously wired to a series |
| `test_material_component_locality_warning` | `LOCALITY_ON_MATERIAL_OR_EQUIPMENT` finding | Labor-locality adjustment being applied to a non-labor cost type |

### `tests/test_periods.py` — `EconomicPeriod`

| Test | Expected | Guards against |
| --- | --- | --- |
| `test_valid_monthly_period`, `test_valid_quarterly_period`, `test_valid_annual_period` | String form `"2025-M03"` / `"2025-Q2"` / `"2025"` | Period label/formatting regressions that would corrupt displayed or stored provenance text |
| `test_invalid_period_combinations` | `ValueError` when `month` and `quarter` are both set | Constructing an internally contradictory period |
| `test_period_ordering` | Dec-2024 `<` Jan-2025 | Incorrect period comparison, which would break chronological sorting of observations |

### `tests/test_specifications.py`

| Test | Expected | Guards against |
| --- | --- | --- |
| `test_json_serialization_round_trip` | `model_dump(mode="json")` → `model_validate` preserves `id` and component `id` | Schema drift that silently loses or corrupts fields across the JSON wire format MCP clients actually receive |

### `tests/test_installation.py`

| Test | Expected | Guards against |
| --- | --- | --- |
| `test_package_imports_outside_checkout` | `import bls_escalation_mcp` succeeds in a subprocess run outside the repo checkout | A src-layout/packaging misconfiguration that only works by accident when run from inside the repo |

### `tests/test_review_regressions.py` — regressions from PR #1 review

| Test | Expected | Guards against |
| --- | --- | --- |
| `test_missing_observations_are_rejected` (parametrized: `None`, `""`, `"-"`, `"NaN"`, `"Infinity"`) | `BLSAPIError` ("Missing or non-numeric") | Silently coercing BLS's missing-data sentinels (notably `"-"`) into a numeric value |
| `test_actual_zero_is_preserved` | Observation value `Decimal(0)` | A real zero value being treated as missing by the check above |
| `test_deferred_loaders_return_no_fabricated_metadata` (parametrized: `PPILoader`, `ECILoader`, `OEWSLoader`) | `parse_metadata([])` and `parse_metadata([{"unmapped": "value"}])` both return `[]` | A stub loader fabricating plausible-looking series metadata instead of honestly returning nothing before real field mappings exist |
| `test_observation_cache_preserves_period_identity` (parametrized: monthly, quarterly, annual, annual-average) | Saved observation round-trips unchanged through SQLite, including period | Persistence losing or conflating period identity/periodicity |
| `test_annual_and_annual_average_do_not_overwrite` | Both an `ANNUAL` and an `ANNUAL_AVERAGE` observation for the same year persist distinctly | An upsert key bug that treats the two periodicities as the same row |
| `test_observation_decimal_text_is_exact` | A 29-digit decimal string round-trips exactly through parsing and JSON re-serialization | Float rounding/precision loss on BLS values (the reason observations are `Decimal`-as-string, per `docs/DECISIONS.md`) |

## Integration tests (real FastMCP client/server boundary)

All three modules build on the shared harness above (canned transport,
`server_env`, fixture payloads); the entries below keep their pre-M0 names
and guards — M0 consolidated scaffolding without changing what any test
asserts.

### `tests/integration/test_bls_client.py`

| Test | Expected | Guards against |
| --- | --- | --- |
| `test_bls_client_parses_mocked_payload` | 2 observations parsed from a mocked HTTP response, correct `series_id`/`value` | The client's request/response parsing breaking against the real BLS JSON shape |

### `tests/integration/test_bls_access.py`

| Test | Expected | Guards against |
| --- | --- | --- |
| `test_access_setup_and_preflight` (parametrized key: `None`, `""`, `"  "`, a real key) | `credential_status` reflects `missing`/`configured_unverified` correctly; status/setup calls make zero HTTP requests; the key never appears in any tool, resource, or instructions text; an unconfigured key fails every live call pointing to `setup://bls-api`; a configured key still enforces the 50-series/20-year bounds; a successful data response does not flip status to "verified" | Leaking the API key into client-visible output; treating a successful response as proof of key validity; burning request quota just to check status; accepting an over-limit request |

### `tests/integration/test_mcp_server.py`

| Test | Expected | Guards against |
| --- | --- | --- |
| `test_discovery_and_contracts` | Exact tool-name set; every tool has a description; no internal params (`ctx`, `api_key`, `database_path`) in input schemas; `readOnlyHint`/`openWorldHint`/`destructiveHint`/`idempotentHint` match each tool's real behavior | Internal wiring leaking into the public MCP contract; tool annotations misrepresenting side effects (e.g., `save` marked read-only) |
| `test_json_workflow_and_persistence` | Full search → describe → create → validate → calculate → save → re-read → update workflow; composite numbers match independent hand arithmetic (e.g. `.6*1.1 + .4*1.2 = 1.14`); save overwrites by id | The calculation result diverging from the documented formula once routed through the full JSON/MCP boundary, not just the service layer; save failing to overwrite an existing spec |
| `test_observations_locality_and_resources` | Observations keep correct shape/types, including preserved footnotes and a null `is_preliminary`; locality factor via MCP matches the service-level math; series/methodology resources return the expected MIME types and text | The MCP JSON boundary corrupting observation fields or resources returning the wrong content type |
| `test_validation_and_domain_errors` | Empty-components spec flagged invalid; invalid period combination, zero base value, empty `component_values`, and `end_year < start_year` each raise the specific expected `ToolError` | Domain errors leaking as unhandled exceptions, or being silently swallowed, instead of surfacing as structured tool errors |
| `test_resource_first_startup_and_cleanup_on_failure` | Reading an unseeded resource before any tool call doesn't error on missing SQL state; the database initializes exactly once; the HTTP transport closes even when the caller raises after startup | Lifespan/resource-ordering bugs and HTTP client leaks on error paths |
| `test_fixed_component_validation_and_calculation` | A `FIXED_UNINDEXED`-only spec validates and calculates to `temporal_factor`/composite `1.0` and 0% change; attaching a series to a fixed component, or omitting one from a material component, each produce the specific expected finding code | Fixed-component handling diverging between the unit-level service and the full MCP path |

### `tests/test_project_shell.py` — launcher and infrastructure

- Transport precedence: default stdio, explicit loopback HTTP, platform `PORT`,
  and Databricks port precedence. A mocked server verifies launch arguments;
  this does not test an actual network socket.
- Invalid platform ports fail before server construction.
- `.env` supplies transport/BLS settings; environment overrides file values.
- `/health` and `/version` return the documented JSON through a real ASGI app
  and its lifespan with a temporary database. These are availability probes,
  not live BLS checks. Docker and vendor deployments need separate validation.

The template-aligned evaluation entry point is [eval/README.md](../eval/README.md).

### `tests/test_component_layout.py` — template layout

Checks every tool/resource module has exactly one decorated component inside
its typed `register` function, named to match its filename. This prevents
regression to grouped handlers; existing MCP client tests separately guard
aggregate discovery, schemas, annotations, invocation and resource contents.

## Evals

**Status: a deterministic eval-evidence pack is in scope for the hackathon
MVP (M4' in [ROADMAP.md](ROADMAP.md)); the LLM-backed harness is deferred to
after the hackathon.** The M4' pack runs scripted scenarios through the real
MCP client against a fixture-built database (oracle workflows plus negative
probes), commits a short results summary under `eval/`, and feeds the
hackathon evaluation document's testing-methodology and performance-metrics
sections. The first external eval remains the hackathon judging
itself; owner manual-eval sessions precede it (the M6 gate).

The suite above verifies deterministic code — given fixed inputs, is the
output correct. It says nothing about an LLM or agent's judgment when
driving these MCP tools under ambiguity (which series to pick, how to
handle a basket with no explicit weights, whether to ask for guidance
instead of inventing a value).

When an evals harness is built, document it here in the same shape as the
tests above, and build it on these principles:

- Start from this project's own known failure modes, not generic prompts:
  silent weight normalization, series substitution without disclosure,
  missing-data interpolation, presenting a stale snapshot as current, and
  conflating temporal and locality factors. (The request-bounds failure
  modes belong to the deferred live-API path.)
- Score tool choice, numeric correctness, and methodology disclosure as
  separate dimensions — one blended pass rate hides which one regressed.
- Grade programmatically wherever checkable (the actual tool calls made, the
  returned provenance, the computed numbers) rather than by LLM judgment.
- Re-run whenever a tool description, schema, or model changes; nothing in
  the code "breaks" when behavior drifts, so only the evals catch it.


## Python smoke command

`tests/test_smoke_mcp.py` runs the command's workflow through the real in-memory
FastMCP client without a BLS key, verifies no upstream requests occur, checks
that an unrelated server fails discovery, and now guards the `main()` validation
boundary: remote/local-credential URLs and non-finite/non-positive timeouts are
rejected before a server connection is attempted. `poe smoke` separately targets
a running HTTP server and checks discovery, status, guidance resources and
an independent 110/100=1.1 calculation. It does not establish live BLS access
or agent performance and does not write specifications.


### Local verification evidence — 2026-10-08

- The Python smoke workflow passed over an actual loopback Streamable HTTP
  connection to a temporary-database server, with BLS HTTP mocked and no key.
  Discovery returned 11 tools, 3 static resources, and 1 resource template;
  status/guidance reads and the 110/100=1.1 calculation passed, exit code 0.
- After merging the `serve` task from main into the smoke branch at `ac52b90`,
  both Poe task dry-runs resolved to their intended Python modules.
  `uv run --locked poe check` passed: lint, formatting, mypy, and 74 tests.
- One existing Starlette TestClient deprecation warning remains.
- These checks establish local protocol connectivity and deterministic behavior.
  They do not establish live BLS access, deployment readiness, stdio host
  compatibility, or model-driven agent quality. No Node.js was required.
