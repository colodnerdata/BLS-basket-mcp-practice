# Actual-cost normalization — specification list

Status: **draft spec, not implemented** (2026-11-03). Specifies the design
accepted in `DECISIONS.md` 2026-11-02 and the planned pieces in
`ROADMAP.md` "After the MVP". Blocked on M3 (observation resolution over the
snapshot and snapshot identity). None of the components below are
registered yet.

Requirement IDs use `AC-<area>-<n>`. "Shall" is a requirement; "should" is
a recommendation; open questions are listed at the end and are not decided
by this document.

## 1. Concepts (read first)

**Normalization here means deflation:** restating dollars spent in
different months at one common price level (the *reference period* `R`), so
they can be added and compared. It is not weight normalization, which stays
forbidden.

| Symbol | Meaning | Unit |
| --- | --- | --- |
| `AC(w,t)` | Incremental actual cost (ACWP) booked to WBS element `w` in month `t` | nominal dollars |
| `P(i,t)` | Index level of BLS series `i` in period `t` (PPI or ECI) | index points (ratio scale) |
| `b` | Base period of a mix template (the period its weights are cost shares for) | period |
| `s(i)` | Template weight of series `i`; Σ s(i) = 1 within `BLS_WEIGHT_TOLERANCE` | fraction |
| `D(m,t)` | Composite level of template `m`: Σ s(i) · P(i,t) / P(i,b) | dimensionless, `D(m,b)=1` |
| `R` | Reference ("constant-dollar") period chosen by the caller | period |
| `RC(w,t)` | Real cost: `AC(w,t) · D(m,R) / D(m,t)` where `m` is `w`'s template | dollars at `R` prices |

Conventions:

1. **Deflate increments, then accumulate.** A cumulative AC mixes price
   levels, so `RC` is computed per month from increments and then summed.
   Cumulative real cost to month `T` is Σ_{t≤T} `RC(w,t)`.
2. **Two different periods.** `b` fixes the template's weights (Laspeyres
   composite, the existing `calculate_composite` math). `R` is the price
   level of the output. They may differ; `D(m,R)/D(m,t)` still depends on `b`
   through the weights, which is why `b` is reported.
3. **Per-WBS deflation.** Each WBS element is deflated by its own template.
   Direct real subtotal = Σ_w Σ_t `RC(w,t)`.
4. **G&A** is its own cost class with a caller-named deflator: a wage rate
   (ECI compensation series) or CPI-U (e.g. `CUUR0000SA0`), plus a reason.
   No default. Its real dollars are a separate line and are included in the
   project real total.
5. **Fee is not cost.** Fee rows are excluded from every total and reported
   as a finding.
6. **Implied deflator** = Σ nominal / Σ real over the same scope. It is
   current-weighted (Paasche-type) and is reported, never used as an input.
7. **Precision.** `Decimal` throughout the service; no rounding in the
   server. Tests compare `Decimal` results exactly against hand-computed
   values.

Relation to `custom_ppi_escalation_app_spec.md`: its normalized factor
`N(i,t) = P(i,t)/B(i)` and composite `I(t)` are the same rebasing and
fixed-weight math as `D(m,t)`. Both should call one shared service function
rather than reimplement it (AC-SVC-3).

## 2. Domain models (`models/evm.py`)

- **AC-MOD-1** `CostClass` StrEnum: `DIRECT`, `G_AND_A`, `FEE`.
- **AC-MOD-2** `ActualCostRow`: `wbs_id: str`, `period: EconomicPeriod`
  (monthly), `cost_class: CostClass`, `ac_increment: Decimal` (nominal
  dollars; negatives allowed), optional `note: str | None`.
- **AC-MOD-3** `WbsTemplateMapping`: `wbs_id: str`, `spec_id: str` (a saved
  `EscalationIndexSpec`; the template), `rationale: str`.
- **AC-MOD-4** `GaDeflatorKind` StrEnum: `WAGE_RATE_ECI`, `CPI_U`.
  `GaDeflator`: `kind`, `series_id: str`, `reason: str` (non-empty).
- **AC-MOD-5** `PeriodAlignmentRule` StrEnum: `EXACT` (default) and
  `QUARTER_STEP_HOLD` (a quarterly value applies to each of its three
  months). No interpolation option exists.
- **AC-MOD-6** `NormalizationMethod` StrEnum: `PER_WBS` (default) and
  `PROJECT_COMPOSITE_FALLBACK` (one template for all direct rows; allowed
  only when the caller says no WBS split exists, and labeled in the result).
- **AC-MOD-7** `ActualCostNormalizationRequest`: `rows: list[ActualCostRow]`,
  `mappings: list[WbsTemplateMapping]`, `reference_period: EconomicPeriod`,
  `ga_deflator: GaDeflator | None`, `alignment: PeriodAlignmentRule`,
  `method: NormalizationMethod`, `fallback_spec_id: str | None`.
- **AC-MOD-8** `ActualCostNormalizationResult`: per-row results (nominal,
  deflator value at `t` and `R`, real), per-WBS cumulative nominal and real
  by month, direct real subtotal, G&A nominal/real line, project
  nominal/real totals (fee excluded), implied deflator per WBS and overall,
  excluded fee total, `findings: list[ValidationFinding]`, a ledger
  (observations used with series, period, value text, footnotes, retrieval
  date; template spec IDs and their `updated_at`; snapshot identity),
  `methodology_version`, `calculated_at`.
- **AC-MOD-9** All new models are strict (`extra="forbid"`) and fully typed:
  no `dict[str, Any]`, generic `object`, or JSON-in-a-string fields.
- **AC-MOD-10** Monetary and index values are `Decimal`. Their JSON wire form
  must be verified with the pinned FastMCP 3.2.4 client before the contract
  is frozen (see AC-TST-7); record the result in `DECISIONS.md`.

## 3. Calculation rules (`services/deflation.py`, pure)

- **AC-CALC-1** `RC(w,t) = AC(w,t) · D(m,R) / D(m,t)` with `D` from AC-SVC-3.
- **AC-CALC-2** Real cumulative values are sums of real increments, never a
  deflated cumulative.
- **AC-CALC-3** G&A rows use `P(g,R)/P(g,t)` for the named series `g`.
- **AC-CALC-4** Fee rows contribute to no total and produce one finding with
  the excluded nominal amount and row count.
- **AC-CALC-5** Negative increments are deflated linearly (same formula) and
  each produces a warning finding.
- **AC-CALC-6** Project real total = direct real subtotal + G&A real.
  Project nominal total excludes fee.
- **AC-CALC-7** Under `QUARTER_STEP_HOLD`, the month's deflator is the value
  of the containing quarter; the rule and every held value appear in the
  ledger. Under `EXACT`, a monthly row against a quarterly series is an error.
- **AC-CALC-8** `PROJECT_COMPOSITE_FALLBACK` deflates all direct rows with
  `fallback_spec_id` and adds a finding that per-WBS deflation was not used.

## 4. Validation and errors

Hard errors (domain exceptions subclassing `BLSEscalationError`, translated
to `ToolError` by `domain_errors()`):

- **AC-ERR-1** A direct row's `wbs_id` has no mapping (under `PER_WBS`).
- **AC-ERR-2** A mapped `spec_id` is not saved, or fails existing spec
  validation (weights, index-level eligibility, single periodicity).
- **AC-ERR-3** G&A rows are present and `ga_deflator` is missing; or the
  named series is not of the declared kind; or `CPI_U` is requested before
  `cu` data is ingested (explicit "not ingested", never a substitute).
- **AC-ERR-4** Any needed observation (`t`, `R`, or template base `b`) is
  missing from the snapshot. No zero, carry-forward, or interpolation.
- **AC-ERR-5** Duplicate `(wbs_id, period, cost_class)` rows. They are not
  summed silently.
- **AC-ERR-6** A non-monthly row period, or a row count above
  `BLS_MAX_AC_ROWS` (AC-CFG-1).

Structured findings (returned, not raised): fee exclusion, negative
increments, fallback method used, preliminary observations used, mappings
supplied for WBS ids with no rows. Unexpected exceptions stay masked.

## 5. Services and lifespan

- **AC-SVC-1** New `DeflationService` in `services/deflation.py`, owned by
  the lifespan and added to `Services` as `deflation`.
- **AC-SVC-2** It reads saved templates through `SpecificationService` and
  observations through M3's snapshot observation repository/service. It
  never constructs clients, runs SQL in the handler, or calls BLS.
- **AC-SVC-3** Factor out one pure function for "composite level of a
  template at period t relative to its base", reused by
  `EscalationCalculationService`, this service, and the app spec's
  normalized factors. Existing `calculate_composite` results must not change.
- **AC-SVC-4** Snapshot identity comes from the shared service planned for
  `bls://snapshot`, so ledger and resource agree.

## 6. FastMCP components

One component per file, each with `register(mcp: FastMCP) -> None`, added
to its package aggregator; `create_server` is unchanged.

| Component | File | Contract | Phase |
| --- | --- | --- | --- |
| Tool `normalize_actual_cost` | `mcp/tools/normalize_actual_cost.py`; add to `register_tools` in `mcp/tools/__init__.py` | Input: typed `ActualCostNormalizationRequest` fields as parameters, plus hidden `ctx: Context`. Output: `ActualCostNormalizationResult` (FastMCP-generated input and output schemas). Annotations: `readOnlyHint: True`, `openWorldHint: False` (local snapshot only; align with whatever M3 sets for `calculate_index_from_bls`). Sync handler (SQLite, no network). Body: `with domain_errors(): return get_services(ctx).deflation.normalize(...)`. | Required |
| Resource `methodology://actual-cost-normalization` | `mcp/resources/methodology_actual_cost_resource.py`; add to `register_resources` | `text/plain`, static, local. States sections 1 and 3: increments-then-accumulate, `R` vs `b`, per-WBS templates, G&A options with no default, fee exclusion, alignment rules, caveats (procurement lag, preliminary PPI revisions, negative increments, locality separate). Text comes from a shared policy constant also used in docstrings, so prose and code agree. | Required |
| Prompt `normalize_actual_cost_workflow` | `mcp/prompts/normalize_actual_cost_workflow.py`; add to `register_prompts` | String arguments: required `project_description`; optional `reference_period`, `wbs_summary`. Returns a `str` user message asking the host to read the methodology resource, collect a WBS→template mapping (saving templates only on request), ask for the G&A deflator and reason, and call the tool. Does not run tools or calculate. | Optional; after the tool ships |

Not added: a result resource (results are not persisted; see
`mcp_resources_prompts.md`), a separate validation tool (validation is part
of the call and returns structured findings), or any tool that accepts
fee rows for deflation.

The tool description shall name the methodology resource and state that
fee is excluded and that G&A needs a named deflator.

## 7. Configuration

- **AC-CFG-1** `BLS_MAX_AC_ROWS` (typed `Settings` field, documented in
  `.env.example`) bounds request size. Default to be set with real export
  sizes in hand (open question 3).
- No credentials or paths in tool arguments or responses.

## 8. Data dependencies

- **AC-DATA-1** M3: exact-period observation resolution over the snapshot
  and snapshot identity. Hard prerequisite.
- **AC-DATA-2** ECI compensation series: already ingested; covers the
  `WAGE_RATE_ECI` option and labor components.
- **AC-DATA-3** CPI-U: needs a `cu` loader and one owner-invoked download
  under `docs/bls_etiquette.md`. Until then `CPI_U` fails per AC-ERR-3.
  Tests use fixture slices only.

## 9. Tests (update `docs/TESTING.md` in the same change)

- **AC-TST-1** Flat index: real = nominal for every row and total.
- **AC-TST-2** One-month, one-WBS case against a hand-computed value.
- **AC-TST-3** Additivity: Σ WBS real + G&A real = project real total
  (exact `Decimal`).
- **AC-TST-4** G&A under each deflator kind with hand-computed values;
  missing deflator refused; `CPI_U` without `cu` data refused.
- **AC-TST-5** Fee rows excluded from totals and reported in findings.
- **AC-TST-6** Deflating increments differs from deflating the cumulative
  when prices move (guards AC-CALC-2); negative increment flagged.
- **AC-TST-7** Client contract through `fastmcp.Client`: tool listed with
  annotations and a schema with no generic objects; JSON input and output
  round trip including `Decimal` fields; domain errors reach the client as
  `ToolError`; unexpected errors stay masked; resource readable with its
  MIME type; aggregator registers each component exactly once.
- **AC-TST-8** Alignment: `EXACT` rejects monthly-vs-quarterly;
  `QUARTER_STEP_HOLD` holds each quarter's value for its three months.
- **AC-TST-9** Regression: existing `calculate_index_spec` results unchanged
  after the AC-SVC-3 refactor.
- **AC-TST-10** Eval scenarios in `eval/scenarios.py` for fee exclusion and
  missing G&A deflator, with status in `eval/README.md` and `TESTING.md`.

## 10. Documentation touch points

`README.md` tool table, `docs/methodology.md`, `QUICKSTART.md` (manual flow),
`docs/hackathon_template.md` mapping, `server.json` if the version changes,
and a `DECISIONS.md` entry for the `Decimal` wire format (AC-MOD-10).

## 11. Open questions (owner)

1. Do real EVM exports give incremental or cumulative AC? If cumulative,
   should the tool accept it and difference it explicitly (reported per
   WBS), or require increments?
2. Default for `reference_period` when not supplied: refuse (current
   proposal), or the last month of data?
3. Typical export size, to set `BLS_MAX_AC_ROWS`.
4. Are there cost classes beyond direct / G&A / fee (e.g. overhead, COM)
   that need their own deflator line?
