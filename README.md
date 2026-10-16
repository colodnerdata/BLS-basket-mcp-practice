# BLS Escalation MCP

This project is an early-stage FastMCP server for constructing transparent custom cost-escalation indexes from U.S. Bureau of Labor Statistics (BLS) data.

Start with [QUICKSTART.md](QUICKSTART.md) for local client connection.
The project shell follows the [GSA MCP Hackathon template](docs/hackathon_template.md),
with [deployment guidance](deploy/README.md), [agent evaluation status](eval/README.md),
and [security notes](SECURITY.md). The BLS implementation and service boundaries
remain project-specific.

## What this project is

This server helps an LLM or analyst build defensible escalation indexes by keeping the workflow explicit:

- project description
- cost basket definition
- candidate BLS series review
- selected series and weights
- BLS observations
- component escalation factors
- weighted composite escalation index
- optional labor locality adjustment
- validation and audit trail

The initial scaffold focuses on the deterministic core: typed models, SQLite-backed series metadata storage, BLS observation retrieval for known series IDs, deterministic escalation calculations, locality-factor logic, validation rules, and MCP tools/resources that expose those capabilities.

## What this project is not

This is not:

- a generic BLS API wrapper that covers every endpoint
- an LLM or semantic project-estimation engine
- a complete project-estimation system with authoritative weights
- a source of definitive project cost assumptions

## Core methodology

The implemented methodology separates temporal escalation from geographic/locality adjustment.

- Temporal factor = target value / base value
- Locality factor = target locality wage / reference locality wage
- Combined component factor = temporal factor * locality factor
- Fixed/unindexed component temporal factor = 1
- Weighted composite = sum(weight * factor)

Locality and temporal escalation remain distinct concepts and are reported separately. The code does not silently substitute series, interpolate missing values, normalize weights, or adjust observations without explicit methodology.

## Architecture

The project follows a simple dependency direction:

- MCP layer -> services -> repositories / clients -> external BLS / SQLite
- shared domain models are used across layers
- calculation logic is independent from FastMCP
- repositories do not depend on the MCP layer

## Current status and planned server components

Status reviewed **2026-10-15**: **11 registered tools, 3 static resources,
1 resource template, and no registered prompts**. **Implemented** means
present in code with offline client-contract coverage, not live BLS or
deployment validation. **Planned** means MVP work remains; **Deferred**
means post-MVP or awaiting a concrete design.

The MVP targets a **local BLS flat-file snapshot with no user API key**.
PC/PD/WP PPI and eligible current-dollar ECI index ingestion, observation
storage, per-file provenance, `poe build-catalog`, and `poe verify-ingest`
are implemented. Basket-relevant downloads and the source-backed calculation
workflow remain unfinished. Existing live-API tools are still registered;
live-API hardening is deferred.

### Tools

| Tool / capability | Purpose | Current status |
| --- | --- | --- |
| `search_series` | Search local metadata by text and program filters. | **Implemented.** Requires an ingested catalog; semantic matching and automatic selection are deferred. |
| `describe_series` | Read metadata for a known series ID. | **Implemented.** Returns null when absent from the local catalog. |
| `create_index_spec` | Construct a typed basket with periods, components, series, and weights. | **Implemented.** Does not save or normalize weights. |
| `validate_index_spec` | Return structured basket findings. | **Implemented; extension planned (M3).** Periodicity-mismatch validation and source-backed input checks remain. |
| `save_index_spec` | Persist a specification in SQLite. | **Implemented.** Replaces the same ID and updates its timestamp; deployed per-user isolation is deferred. |
| `get_index_spec` | Retrieve a saved specification. | **Implemented.** Returns null for an unknown ID. |
| `calculate_component_escalation` | Calculate a component factor from supplied base/target values and an explicit locality factor. | **Implemented.** Does not resolve BLS observations or produce snapshot provenance. |
| `calculate_index_spec` | Combine supplied component calculations using specification weights. | **Implemented.** Supplied-value calculation; source-backed resolution remains planned. |
| `calculate_labor_locality_factor` | Calculate target/reference wage ratio from supplied wages. | **Implemented.** OEWS lookup, geographic mapping, and automated wage ratios are deferred. |
| `get_bls_access_status` | Report live-API configuration and limits without HTTP or secrets. | **Implemented, optional live path.** Does not verify a key or remaining quota. |
| `get_series_data` | Retrieve live-API observations for known series IDs. | **Implemented, optional live path.** Requires a configured key; at most 50 series and 20 inclusive years per call; no batching or caching; live validation/hardening deferred. |
| `calculate_index_from_bls(spec)` | Validate, resolve exact observations from the local snapshot, calculate, and return a ledger with source references and warnings. | **Planned (M3); not registered.** Requires single periodicity, explicit missing-data errors, and snapshot identity/date. |
| Multi-request live retrieval / request planner (public name undecided) | Split and combine requests beyond API bounds with budgets and conflict detection. | **Deferred, post-MVP.** Separate from offline snapshot calculation. |

### Resources

| Resource / capability | Purpose | Current status |
| --- | --- | --- |
| `bls://series/{series_id}` | JSON metadata for a known local series. | **Implemented resource template.** Unknown IDs return a resource error. |
| `methodology://composite-index` | Explain temporal factors, weighted composites, and percent change. | **Implemented static resource; extension planned (M3).** Full observation/weight/precision conventions and snapshot disclosure remain. |
| `methodology://locality-adjustment` | Explain the separate, explicitly applied wage ratio. | **Implemented static resource.** Automated locality sourcing is deferred. |
| `setup://bls-api` | Explain registration, local key configuration, and API limits. | **Implemented static resource, optional live path.** The planned snapshot MVP needs no key. |
| Snapshot vintage and provenance disclosure | Supply snapshot identity/date so results can be interpreted and reproduced. | **Planned (M3).** File provenance exists in `data/manifest.json` and SQLite `ingestion_log`; disclosure in the calculation ledger and methodology resources remains. Target URI: `bls://snapshot`; see the [resource/prompt plan](docs/mcp_resources_prompts.md). |

### Planned resource additions

| Resource | Purpose | Status |
| --- | --- | --- |
| `guide://escalation-workflow` | Project-to-index workflow, missing-input handling, and tool/resource links. | **Planned, MVP preparation.** |
| `bls://catalog/coverage` | Available programs, value types, periodicities, and catalog versus observation coverage. | **Planned, MVP preparation.** |
| `bls://snapshot` | Manifest-derived snapshot identity, file retrieval dates, hashes, and verification scope. | **Planned, MVP preparation / M3.** |
| `bls://series/{series_id}/coverage` | Stored observation periods, counts, and known gaps for a series. | **Planned, M3.** |
| `basket://archetypes` and `basket://archetypes/{archetype_id}` | Reviewed decompositions, candidate search terms, and examples; begin with vertical construction. | **Planned, MVP preparation.** Illustrative examples do not supply authoritative weights. |
| `index://specifications/{spec_id}` | Read-only saved specification including assumptions and selection rationale. | **Planned, second tranche.** Same access boundary as the existing read tool. |

### Prompts

| Planned prompt | Purpose | Current status |
| --- | --- | --- |
| `design_escalation_basket` | Clarify scope, periods, shares and evidence; propose a reviewable component table. | **Planned, MVP preparation.** |
| `review_series_candidates` | Compare catalog-backed candidates, coverage and proxy rationale for a component. | **Planned, MVP preparation.** |
| `review_index_spec` | Review a saved specification, call validation, and expose unresolved assumptions. | **Planned, M3.** |
| `calculate_and_explain_index` | Guide source-backed calculation and explain component contributions, provenance and limits. | **Planned, after M3 calculation/ledger support.** |
| `review_labor_locality` | Clarify geographic intent and request comparable supplied wage evidence. | **Planned, second tranche.** OEWS automation remains deferred. |

See the [FastMCP resources and prompts plan](docs/mcp_resources_prompts.md)
for argument contracts, resource contents, archetype examples, delivery order,
and acceptance criteria. These additions are not registered yet. Retrieving
a prompt does not execute tools, calculate, save, download, or call an LLM.

Server-wide instructions already exist and are distinct from MCP prompts.
They currently cover live-API setup, credential handling, request bounds,
and the rule that missing observations are not zero.

### Context and supporting material

Context is supplied through server instructions, resource contents, and
reviewed examples; it is not a separate registered MCP component type.

| Context / supporting capability | Current status |
| --- | --- |
| Methodology and guardrails | **Partly implemented.** Supplied-value calculations and basic validation exist; M3 adds source-backed exact-period resolution, single-periodicity enforcement, and a calculation ledger. No silent normalization, substitution, interpolation, or locality application is allowed. |
| Basket archetypes and candidate-series examples | **Initial scope selected.** Vertical construction, from materials through labor, guides snapshot selection. A reviewed example set shared by archetype resources and prompts is planned in [the resource/prompt plan](docs/mcp_resources_prompts.md), but not implemented. Examples must not imply authoritative project weights. |
| PPI materials and ECI labor coverage | **Ingestion implemented; curated coverage unfinished (M2').** WP is the materials layer; ECI index levels are baseline labor. Monthly materials and quarterly labor require parallel same-periodicity specifications under the MVP plan. OEWS locality mapping is deferred. |
| Flat-file ingestion and refresh | **Partly implemented (M2').** Offline parsers, storage, manifest receipts, and agreement checks exist. Conditional-GET fetcher and basket-relevant owner-invoked downloads remain. This is operator CLI/service work, deliberately not an MCP download tool. |
| Evaluation evidence | **Offline tests implemented; evidence pack planned (M4').** Scripted end-to-end evidence and committed results remain; model-backed agent evals are post-MVP. |

See [docs/NEXT.md](docs/NEXT.md) for current work,
[docs/ROADMAP.md](docs/ROADMAP.md) for milestones and deferred scope, and
[docs/TESTING.md](docs/TESTING.md) for verification boundaries. LLM calls,
embeddings/vector search, a REST API, and a web app remain outside the
current implementation.

## Local launch and verification

Configure local settings in the ignored `.env` file; do not inject settings
through terminal environment assignments. For HTTP testing, set
`MCP_TRANSPORT=streamable-http`, `MCP_HOST=127.0.0.1`, and `MCP_PORT=8000`.

```bash
# Terminal 1, from the repository directory:
uv run --locked poe serve
# Terminal 2, from the repository directory:
uv run --locked poe smoke
```

The smoke command uses Python/FastMCP only: no Node.js or Inspector dependency.
It checks MCP discovery, configuration status, guidance resources, and a
supplied-value calculation. It does not fetch BLS data or save specifications.
See [QUICKSTART.md](QUICKSTART.md) for expected output and troubleshooting,
[docs/TESTING.md](docs/TESTING.md) for evidence and boundaries, and
[eval/README.md](eval/README.md) for the agent-eval status.

## Development

Install dependencies and run checks:

```bash
uv sync --locked
uv run --locked poe check
```

Run the server locally:

```bash
uv run --locked fastmcp run fastmcp.json
uv run --locked python main.py
# Equivalent module launch:
uv run --locked python -m bls_escalation_mcp.server
```

Set environment variables such as:

```bash
export BLS_API_KEY=...
export BLS_DATABASE_PATH=./bls_catalog.db
```

## Configuration

The project reads settings from environment variables and a `.env` file in
the working directory using pydantic-settings. Environment variables take
precedence. See `.env.example` for supported values. The `main.py`/`app.py`
launcher selects HTTP for platform ports or `MCP_TRANSPORT=streamable-http`;
the existing module and `fastmcp.json` launches continue to use stdio.

## BLS access and query limits

Before live retrieval, call `get_bls_access_status` and read `setup://bls-api`.
Configure your own key outside chat using `BLS_API_KEY`, then restart the server.
Status is configuration-only and does not verify the key or remaining quota.
Live retrieval requires a configured key and accepts at most 50 series and
20 inclusive calendar years per call. Automatic batching is deferred.
See [BLS setup, limits, and request planning](docs/bls_api.md) for registration
and the planned design for combining requests and returning multi-query results.

## License

This project is released under the MIT license; see [LICENSE](LICENSE).
The security policy is in [SECURITY.md](SECURITY.md).
