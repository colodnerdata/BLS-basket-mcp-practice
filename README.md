# BLS Escalation MCP

This project is an early-stage FastMCP server for constructing transparent custom cost-escalation indexes from U.S. Bureau of Labor Statistics (BLS) data.

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

## Current status

Implemented for this scaffold:

- package layout and configuration
- typed models for periods, series, observations, basket specs, calculations, locality, validation, and provenance
- deterministic escalation calculation service
- labor-locality calculation service
- validation service for obvious basket errors
- SQLite-backed series repository and simple catalogue search
- minimal BLS client for known series IDs
- FastMCP server exposing implemented discovery, validation, calculation, locality, specification, and observation tools
- client integration tests for all tools/resources, JSON schemas, and lifecycle
- mypy, lint, formatting, and tests in the standard `poe check` task
- documentation and deterministic fixture tests

Still intentionally scaffolded or deferred:

- semantic series matching and automatic series selection
- sophisticated BLS bulk-data ingestion logic
- full OEWS locality mapping
- LLM calls, embeddings, and vector search
- REST API or web app

See [docs/ROADMAP.md](docs/ROADMAP.md) for the plan from this scaffold to an
MVP with test and eval harnesses.

## Development

Install dependencies and run checks:

```bash
uv sync --locked
uv run --locked poe check
```

Run the server locally:

```bash
uv run --locked fastmcp run fastmcp.json
# Equivalent module launch:
uv run --locked python -m bls_escalation_mcp.server
```

Set environment variables such as:

```bash
export BLS_API_KEY=...
export BLS_DATABASE_PATH=./bls_catalogue.db
```

## Configuration

The project reads settings from environment variables using pydantic-settings. See `.env.example` for the supported values.

## BLS access and query limits

Before live retrieval, call `get_bls_access_status` and read `setup://bls-api`.
Configure your own key outside chat using `BLS_API_KEY`, then restart the server.
Status is configuration-only and does not verify the key or remaining quota.
Live retrieval requires a configured key and accepts at most 50 series and
20 inclusive calendar years per call. Automatic batching is deferred.
See [BLS setup, limits, and request planning](docs/bls_api.md) for registration
and the planned design for combining requests and returning multi-query results.

## License

This repository does not yet declare a project license; update before public reuse.

