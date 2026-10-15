# FastMCP resources and prompts plan

Status: **planned, not implemented**, 2026-10-15. This plan replaces the
blanket deferral of reusable prompts in the 2026-10-07 shell decision.
Existing registrations remain 11 tools, three static resources, one resource
template, and zero prompts until implementation lands.

## Intended workflow and boundaries

The host LLM should turn a project idea into a defensible cost basket,
help the user review candidate BLS series and base-period cost shares,
calculate from verified observations, and explain the result with an audit
trail. The server supplies reference material and deterministic operations;
the host conducts the conversation. Resources provide facts and reusable
context; prompts organize the host's workflow; tools validate, calculate,
and explicitly persist state.

Prompt retrieval must not call an LLM, run tools, save a specification,
download data, or calculate an index. A rendered prompt asks the host to
use the relevant tools. Resources are read-only, local, and bounded.
Neither instructions nor prompts replace service-side validation.
A host may not load resources or expose prompts automatically: put a short
entry-point instruction and resource links in server instructions and tool
descriptions, and document the manual flow in QUICKSTART. Do not depend on
automatic attachment, subscriptions, sampling, or elicitation for the MVP.

## Planned resources

URIs below are target contracts. New URIs are not available yet. JSON
resources use explicit typed models and application/json; prose resources
use text/markdown. Preserve existing URIs and MIME contracts.

| URI | Content and source | Delivery / acceptance |
| --- | --- | --- |
| `guide://escalation-workflow` | Ordered stages, questions to ask, appropriate tool calls, review checkpoints, missing-input handling, and links to the remaining resources. Describe supplied-value and snapshot-backed paths separately. | MVP first tranche. A caller can discover how to proceed without API setup; no claim that planned tools already exist. |
| `bls://catalog/coverage` | Programs, eligible value types, catalog counts versus actual observation coverage, supported periodicities, limitations, and snapshot reference. Derive from local repositories and ingestion receipts, not hard-coded counts. | MVP first tranche. Empty/unbuilt catalog is reported explicitly. No implication that metadata presence guarantees observations. |
| `bls://snapshot` | Snapshot identity derived from a deterministic manifest digest, per-file retrieval dates/hashes, ingestion code version, and verification status with time/scope if actually verified. Link to bounded file details if the manifest grows. | MVP first tranche. Heterogeneous retrieval dates are preserved; never fabricate one common as-of date or claim latest data. Establish identity in a shared service used by M3's ledger. |
| `bls://series/{series_id}/coverage` | Available observation periodicities, first/last stored periods, counts, and known gaps, plus a warning that endpoints do not prove every intermediate period exists. | MVP with M3. Query local observations; retain existing `bls://series/{series_id}` metadata template. Unknown series and known series without observations have distinct outcomes. Exact period availability is checked again during calculation. |
| `basket://archetypes` | Small index of reviewed archetype IDs, descriptions, versions, and detail URIs. Begin with `vertical-construction`. | MVP first tranche. Lists only real reviewed content. |
| `basket://archetypes/{archetype_id}` | Scope boundaries; material/labor/fixed-share decomposition; candidate search terms; verified series references with rationale and limitations; questions to ask; worked examples. | MVP first tranche. Start with vertical construction; see example rules below. Unknown ID is a resource error. |
| `methodology://composite-index` (existing) | Extend with base-period shares, weight tolerance, fixed components, index-level eligibility, exact periods, single periodicity, precision, missing values, and snapshot/ledger references. | MVP with M3; keep text/plain contract. Use shared policy definitions so prose and validation agree. |
| `methodology://locality-adjustment` (existing) | Extend with user-supplied wage evidence requirements, reference/target geography, wage basis and year, and separation of temporal and geographic factors. Clearly state OEWS mapping is deferred. | MVP guidance; keep text/plain contract. No implied automatic city adjustment. |
| `index://specifications/{spec_id}` | Read-only view of the saved typed specification, including assumptions, weight sources, match/proxy rationale, periods, and timestamps. Reuse the specification service and the same access boundary as `get_index_spec`. | Second tranche, after the core workflow; JSON. Unknown ID is a resource error; no new listing endpoint or cross-user disclosure. Hosted user isolation remains a prerequisite for private use. |
| `setup://bls-api` (existing) | Retain optional live-API setup and limits; explicitly distinguish it from the no-key snapshot workflow. | Existing resource; wording update alongside entry-point guidance. |

Do not add calculation-result resources yet: results and ledgers are not
persisted. M3 returns the ledger directly. A future immutable result URI
requires a separate result-storage, access, and retention design. General
observation browsing, full catalog dumps, OEWS geography resources, and
live refresh remain outside this increment; search stays a tool.

## Archetypes as reusable examples

Use versioned, reviewed local content shared by resources and prompts.
An archetype is a starting point for questions and candidate searches,
not an authoritative estimate or automatic series-selection rule.

- Show at least a materials-only case, a labor-only case, a fixed-share
  case, and a rejected monthly-materials/quarterly-labor combination.
  Cases may be small variations of vertical construction, not invented
  additional supported project types.
- Each case states inputs, questions, candidate rationale, exclusions,
  expected findings, and disclosure language. Numeric examples are marked
  illustrative, with hand-checkable values and explicit weight sources.
- Real series IDs/titles must be checked against the ingested catalog and
  snapshot coverage. Synthetic fixtures are prominently labeled and never
  presented as BLS observations.
- Reuse a few relevant examples in a prompt, selected deterministically
  from the requested archetype. Keep the complete example library in
  resources; do not stuff every example into every response.
- Include negative examples: insufficient weights, no supported series,
  missing target period, discontinued series, unsupported locality, and
  an unapproved proxy. Examples cannot authorize normalization,
  interpolation, replacement, or made-up observations.

## Planned prompts and argument contracts

All prompts below are **planned**. Prompt arguments are strings on the MCP
wire. Prefer short text and saved-spec IDs rather than serialized nested
specifications; required arguments are marked below, all optional text
defaults to empty. Validate archetype IDs against the curated index.
Use a bounded, deterministic output; put length limits in the eventual
contract and test them. Do not accept arbitrary resource URLs or paths.

| Prompt | Arguments | Required host behavior / output |
| --- | --- | --- |
| `design_escalation_basket` | Required `project_description`; optional `base_period`, `target_period`, `locality`, `archetype_id`. | Read workflow, coverage, and relevant archetype. Ask for only missing scope, dates, cost shares and evidence. Produce a draft component table with exclusions, unanswered questions, and weight sources; distinguish user inputs from illustrative assumptions. Use create/validate tools once inputs are sufficient; no automatic save. A city alone does not authorize a locality factor. |
| `review_series_candidates` | Required `component_description`; optional `base_period`, `target_period`, `archetype_id`. | Use search, metadata and coverage to compare a small candidate set: exact ID/title, program, unit/value type, seasonal basis, periodicity, date coverage, fit, exclusions and proxy rationale. Missing metadata stays unknown. Ask the user to choose or approve a disclosed proxy; no claim of semantic certainty. Return an explicit no-match outcome when warranted. |
| `review_index_spec` | Required `spec_id`. | Read the saved spec and relevant methodology/coverage; call validation. Present findings, cost-share evidence, series selections, unresolved proxies, period compatibility, and any locality request. Return ready/blocked with reasons; changes require an explicit revised spec through existing tools, never silent repair. |
| `calculate_and_explain_index` | Required `spec_id`. | Re-read the current saved spec, validate and call M3's `calculate_index_from_bls`. Report periods, weights, component observations/factors/contributions, composite factor and percent change, locality separately, snapshot vintage, source references and limitations. If M3 is unavailable, explain the blocker; never imitate source-backed calculation by relaying invented values. Do not persist prompt output. |
| `review_labor_locality` | Required `spec_id`; optional `reference_locality`, `target_locality`. | Clarify temporal versus geographic intent; request comparable wage evidence, units/basis, source and year. Use `calculate_labor_locality_factor` only with explicit supplied values and request. Explain how an explicit factor enters the supported calculation path; do not imply M3 accepts locality data until its contract actually does. If evidence or support is missing, report a blocked locality adjustment and offer a clearly identified temporal-only result. |

The first four prompts form the MVP path; locality guidance follows in the
second tranche and does not bring OEWS automation into scope. Existing
supplied-value tools remain available for explicitly labeled what-if
calculations; the source-backed prompt must not silently switch to them.

Unsaved baskets stay in the conversation and typed create/validate tool
results. ID-based review/calculation prompts require an explicitly saved
specification: explain this prerequisite and use `save_index_spec` only
when requested, including disclosure if replacing an existing ID. Do not
invent a draft-store service just to pass prompt arguments.

## FastMCP implementation shape

Use the pinned FastMCP 3.2.4 environment, existing service/lifespan
ownership, and one exposed component per file:

- Add resource modules under `mcp/resources/`, each exposing
  `register(mcp: FastMCP) -> None`, and update `register_resources`.
- Add prompt modules under `mcp/prompts/`, with the same module pattern
  and a new explicit `register_prompts` aggregator called once by
  `create_server`.
- Keep content loading, coverage queries and snapshot identity in services.
  Handlers must not read files, issue SQL, fetch BLS, or implement math.
  Keep shared reference content outside handlers; no new LLM dependency.
- Start with prompt handlers returning `str` (a user message). Add a
  bounded multi-message example format only after exercising it with the
  pinned client; do not assume APIs from newer docs exist in 3.2.4.
- Prompt retrieval may read local services to resolve a saved ID, but does
  not validate economically or execute the workflow. Unknown IDs fail
  explicitly. Returned text identifies user descriptions and catalog text
  as data; embedded instructions in those fields must not become policy.
- Resources expose typed JSON or documented text, precise descriptions,
  bounded responses, and clear not-found behavior. No credentials,
  filesystem paths, arbitrary fetch URLs, or mutable result aliases.

Official implementation references:
[FastMCP resources](https://gofastmcp.com/servers/resources),
[FastMCP prompts](https://gofastmcp.com/servers/prompts), and
[client testing](https://gofastmcp.com/servers/testing).
These explain the component model, not evidence that every current example
works with the project's pin. Verify exact APIs in 3.2.4 before coding;
upgrade only through the existing reviewed dependency process.

## Delivery order and completion criteria

1. **M2' / M3 preparation:** add workflow, catalog coverage, snapshot and
   archetype resources; extend methodology and optional API setup wording;
   add `design_escalation_basket` and `review_series_candidates`.
   Implement the shared snapshot identity before returning provenance.
2. **M3:** add per-series observation coverage and the spec review prompt;
   complete source-backed calculation and its ledger, then add
   `calculate_and_explain_index`. Until then the prompt is not advertised
   as a working end-to-end path.
3. **Second tranche:** saved-spec resource and locality-review prompt;
   no expansion to automatic OEWS localization or mixed-periodicity math.
4. **M4' / M5':** include resource reads and prompt retrieval in the offline
   evidence pack and document real host selection in QUICKSTART; exercise
   the journey in two real clients when those clients are available.

Completion means client tests list every new resource/template/prompt,
read/render them with valid and invalid arguments, verify MIME contracts,
unknown IDs, bounded output and fresh/empty database behavior, and prove
prompt/resource reads cause no writes, downloads or tool execution.
Check shared example IDs against the fixture-built catalog and arithmetic
against independent expected values. Avoid whole-prose snapshots: assert
essential policy, references, messages and arguments.

Extend M4' scenarios to cover ambiguous project scope, an unapproved proxy,
missing/incorrect weights, incompatible periodicities, unsupported
locality, missing observations and stale snapshot disclosure. Deterministic
rendering/contract tests do not establish that an LLM follows instructions;
retain owner manual sessions and post-MVP model-backed evals for that claim.
Update `docs/TESTING.md` whenever those tests land, and run
`uv run --locked poe check` for implementation changes. No tests or runtime
components are added by this planning document.
