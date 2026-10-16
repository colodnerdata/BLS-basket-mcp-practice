# Architecture

This repository intentionally keeps a thin MCP layer and a deterministic calculation core.

Dependency direction:

MCP layer -> services -> repositories / clients -> external BLS / SQLite

Important boundaries:

- Models are shared domain types; they contain structured inputs and outputs.
- The `EscalationIndexSpec` defines methodology and inputs.
- `EscalationCalculationResult` contains the result of one calculation.
- `CalculationLedger` records provenance and observations used for a calculation.
- Repositories handle persistence concerns.
- The BLS client handles API retrieval for known series IDs.
- The catalog service answers simple metadata search questions.

Economic calculations should not depend on FastMCP, and repositories should not depend on the MCP surface area.


`create_server(settings=...)` registers typed adapters without opening external
resources. The lifespan initializes the configured SQLite database once, creates
a shared HTTP client and a typed `Services` container, and closes HTTP on exit.
Adapters obtain services through FastMCP `Context`, which is absent from public
schemas. Repository calls open and close their own SQLite connections. Separate
server instances do not share settings, clients, or service singletons.

Modules expose `register_tools(mcp)` or `register_resources(mcp)`. Discovery and
series resources use the same catalog service. Observation tools call the
observation service, which delegates HTTP to the configured BLS client.
