# MVP FastMCP component list

Status reviewed **2026-10-21**. A one-page summary of the FastMCP components
the MVP needs: tools, resources, prompts, and context. It summarizes, and does
not replace, [mcp_resources_prompts.md](mcp_resources_prompts.md),
[ROADMAP.md](ROADMAP.md), and the status tables in the [README](../README.md);
those stay authoritative if they disagree.

**MVP scope:** a local BLS flat-file snapshot, no user API key, deterministic
and offline checks. A judge defines a weighted cost basket and gets an
escalation index in which every number traces to a snapshot observation.

**Status legend**

- **Implemented**: registered, with offline MCP-client contract tests.
- **Planned**: MVP work remains. Where a stub file exists it is not registered.
- **Optional**: registered or designed, but not needed for the snapshot MVP.

Currently registered: 11 tools, 3 static resources, 1 resource template, and
0 prompts.

## Tools

Tools validate, calculate, and explicitly persist state. Each lives in its own
file under `src/bls_escalation_mcp/mcp/tools/`.

### Basket design and storage

| Tool | Description | Status |
| --- | --- | --- |
| `search_series` | Search the local series catalog by text and program filters. | Implemented |
| `describe_series` | Return metadata for a known series ID, or null if it is not in the catalog. | Implemented |
| `create_index_spec` | Build a typed basket (periods, components, series, weights). Does not save or normalize weights. | Implemented |
| `validate_index_spec` | Return structured findings for a basket. M3 adds periodicity-mismatch and source-backed input checks. | Implemented; extension planned (M3) |
| `save_index_spec` | Persist a specification by ID. Replaces an existing ID and updates its timestamp. | Implemented |
| `get_index_spec` | Retrieve a saved specification, or null for an unknown ID. | Implemented |

### Source-backed calculation

| Tool | Description | Status |
| --- | --- | --- |
| `calculate_index_from_bls(spec_id)` | Read the saved spec, validate it, resolve exact base/target observations from the local snapshot, calculate, and return the composite with a ledger of sources, snapshot identity, and warnings. Missing data is an error, never zero. | **Planned (M3); not registered** |

### Supplied-value what-if calculations

These take values the caller provides. They produce no source provenance and
are labeled as what-ifs, not snapshot-backed results.

| Tool | Description | Status |
| --- | --- | --- |
| `calculate_component_escalation` | Component factor from supplied base/target values and an explicit locality factor. | Implemented |
| `calculate_index_spec` | Weighted composite from supplied component calculations, using the specification weights. | Implemented |
| `calculate_labor_locality_factor` | Target/reference wage ratio from supplied wages. OEWS lookup is deferred. | Implemented |

### Registered but not needed for the MVP

| Tool | Description | Status |
| --- | --- | --- |
| `get_bls_access_status` | Report live-API configuration and limits without HTTP or secrets. | Optional (live path) |
| `get_series_data` | Retrieve live-API observations for known series IDs (key required; 50 series and 20 years per call). | Optional (live path); hardening deferred |

Flat-file download and ingestion is deliberately **not** an MCP tool: judges
must not be able to trigger BLS traffic. It is operator CLI work (`poe
build-catalog`, `poe verify-ingest`) under [bls_etiquette.md](bls_etiquette.md).

## Resources

Resources are read-only, local, and bounded reference material. One per file
under `src/bls_escalation_mcp/mcp/resources/`.

| URI | Description | Status |
| --- | --- | --- |
| `guide://escalation-workflow` | Canonical project-to-index workflow: stages, questions to ask, which tool to call, missing-input handling, and links to the other resources. | Planned (stub) |
| `bls://snapshot` | Snapshot identity, per-file retrieval dates and hashes, per-program catalog versus observation coverage, and verification scope. Shares one snapshot-identity service with the M3 ledger. | Planned (stub) |
| `basket://archetypes/{archetype_id}` | Reviewed decomposition (materials, labor, fixed share), candidate search terms, and worked examples. Starts with `vertical-construction`. Examples never supply authoritative weights. | Planned (stub) |
| `bls://series/{series_id}` | JSON metadata for a known local series. Unknown IDs return a resource error. | Implemented (template) |
| `methodology://composite-index` | Temporal factors, weighted composite, and percent change. M3 extends it with weight tolerance, exact periods, single periodicity, precision, and snapshot disclosure. | Implemented; extension planned (M3) |
| `methodology://locality-adjustment` | The separate, explicitly applied wage ratio. Extended with wage-evidence requirements; states that OEWS mapping is deferred. | Implemented; extension planned |
| `setup://bls-api` | Optional live-API registration, key configuration, and limits. Reworded to separate it from the no-key snapshot flow. | Implemented; optional |

## Prompts

Prompts organize the host LLM's workflow. Retrieving one returns text only: it
runs no tools, saves nothing, downloads nothing, and calls no LLM. Hosts may
not expose prompts, so nothing may live only in a prompt; the workflow guide is
the single source. One per file under `src/bls_escalation_mcp/mcp/prompts/`.

| Prompt | Description | Status |
| --- | --- | --- |
| `design_escalation_basket` | Required `project_description`; optional `base_period`, `target_period`, `locality`, `archetype_id`. Guides scope clarification, candidate-series review, and a draft component table with exclusions and weight sources. | Planned (stub) |
| `calculate_and_explain_index` | Required `spec_id`. Guides a source-backed calculation and explains periods, contributions, provenance, and limits. Designed with M3 and not advertised until `calculate_index_from_bls` exists. | Planned (M3) |

## Context

FastMCP `Context` is a runtime object, not a registered component type. The
MVP uses it, and related shared context, as follows.

| Context item | Description | Status |
| --- | --- | --- |
| `ctx: Context` in handlers | Injected into every handler and hidden from client schemas. Handlers call `get_services(ctx)` (`mcp/adapters.py`), which reads `ctx.lifespan_context["services"]`. | Implemented |
| Lifespan-owned `Services` | Built once per server run in `lifespan.py`: access, catalog, observations, specifications, calculations, locality, validation. Never module singletons; SQLite connections stay scoped to repository operations. | Implemented |
| Snapshot-identity and observation-resolution services | Added to the lifespan for `bls://snapshot` and `calculate_index_from_bls`. | Planned (M3) |
| Server `instructions` | Entry-point guidance in `server.py`. Currently covers only the live-API flow; must point to `guide://escalation-workflow` and the no-key snapshot flow. | Implemented; update planned |
| `Settings` | Typed operator configuration (database path, weight tolerance) from `.env`. Credentials and settings never appear in client-visible arguments. | Implemented |
| Archetype and example content | Reviewed, versioned local content shared by the archetype resource, the prompt, and eval fixtures. | Planned |

Not used in the MVP: sampling, elicitation, subscriptions, progress reporting,
and MCP-level authentication.
