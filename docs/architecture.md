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
- The catalogue service answers simple metadata search questions.

Economic calculations should not depend on FastMCP, and repositories should not depend on the MCP surface area.
