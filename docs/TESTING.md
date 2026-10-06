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

## Unit tests

### `tests/test_calculations.py` — `EscalationCalculationService`

| Test | Expected | Guards against |
| --- | --- | --- |
| `test_one_component_weight_one` | `temporal_factor ≈ 1.1` for base 100 → target 110 | Temporal factor drifting from `target / base` |
| `test_if_every_temporal_factor_equals_one_works` | Composite `≈ 1.0` when every component's base equals its target | Weighting/aggregation introducing drift when no escalation occurred |
| `test_locality_factor_one_keeps_localized_equal_to_temporal` | `localized_composite_factor == temporal_composite_factor` when every `locality_factor = 1.0` | Locality factor of 1 failing to be a true no-op; localized/temporal paths diverging |
| `test_fixed_unindexed_component_has_temporal_factor_one` | `temporal_factor ≈ 1.0` for a `FIXED_UNINDEXED` component even with base 100 → target 200 | Fixed/unindexed components being escalated despite the methodology fixing them at 1 |
| `test_order_of_components_does_not_change_result` | Same composite factor with components reversed | Order-dependent (non-commutative) aggregation bug |
| `test_weighted_component_contributions_sum_to_composite_factor` | Composite equals `sum(weight * temporal_factor)` computed independently inline | Composite formula silently diverging from the documented weighted-sum methodology |
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

## Evals

**Status: not implemented.** The suite above verifies deterministic code —
given fixed inputs, is the output correct. It says nothing about an LLM or
agent's judgment when driving these MCP tools under ambiguity (which series
to pick, how to handle a basket with no explicit weights, whether to ask for
guidance instead of exceeding a request bound).

The planned design and its milestone (M5) are in [ROADMAP.md](ROADMAP.md).
When an evals harness is built, document it here in the same shape as the
tests above, and build it on these principles:

- Start from this project's own known failure modes, not generic prompts:
  silent weight normalization, series substitution without disclosure,
  missing-data interpolation, exceeding the 50-series/20-year bounds instead
  of consulting `setup://bls-api`, conflating temporal and locality factors.
- Score tool choice, numeric correctness, and methodology disclosure as
  separate dimensions — one blended pass rate hides which one regressed.
- Grade programmatically wherever checkable (the actual tool calls made, the
  returned provenance, the computed numbers) rather than by LLM judgment.
- Re-run whenever a tool description, schema, or model changes; nothing in
  the code "breaks" when behavior drifts, so only the evals catch it.
