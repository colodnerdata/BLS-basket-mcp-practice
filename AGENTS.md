# Agent instructions

This is the canonical source of project instructions for coding assistants.
Tool-specific entry points should reference it instead of copying its rules.

## Get oriented

1. Read `README.md` and `docs/NEXT.md` for purpose and current work.
2. Read `docs/DEVELOPMENT.md` for commands and verification boundaries.
3. Before a design change, search `docs/DECISIONS.md` by mechanism or concept.
   Preserve rejected approaches and explain any decision you supersede.

## Work on the requested change

- Prefer the simplest correct implementation that makes the reasoning clear.
- Keep domain logic separate from file access, presentation, and integrations.
- State mathematical conventions, assumptions, units, and tolerances where
  relevant. Cite a source when implementing a nontrivial published method.
- Use type hints on public Python functions. Explain non-obvious behavior in
  docstrings; use NumPy-style sections where useful.
- Keep changes focused. Avoid speculative frameworks, unrelated cleanup, or
  dependencies without a concrete need.
- Preserve existing uncommitted work and report any conflict with it.

## Verify what changed

- Run `uv run --locked poe check` before reporting a code change complete.
- Add tests for changed behavior and regression risks. Prefer invariants,
  small explicit cases, and independent expected results to implementation
  snapshots. Formatting-only or prose edits do not need new tests.
- Whenever a test is added, removed, or its intent changes, update
  `docs/TESTING.md` in the same change. It is the single human-readable
  record of what each test guards against, and of evals status, for anyone
  who isn't reading the test code. Group trivial/parametrized variants under
  one entry instead of listing every case.
- For generated deliverables, rebuild first and inspect the newly generated
  output. A check of an old artifact is not evidence about the new code.
- Report exactly what ran, what passed, and what could not run. Mocks and
  structural checks do not establish integration or numerical correctness.
- Keep repeatable verification commands in `pyproject.toml`; CI calls them.

## Leave useful context

- Explain the result and its reason, with the relevant validation evidence.
- Record consequential tradeoffs in `docs/DECISIONS.md`. Routine edits do not
  need decision entries.
- Update `docs/NEXT.md` when stopping with unfinished work. Include a specific
  next action and any blocker; do not append a session transcript.
- If asked to address PR review, connect each fix to the relevant comment and
  evidence. Do not mark an unresolved concern as resolved.
- Publishing, merging, or sending messages follows the owner's instructions.
  These repository notes are not blanket authorization for those actions.


## FastMCP conventions

- Verify APIs against the supported FastMCP version's official documentation.
  Record version and lifecycle decisions in `docs/DECISIONS.md`; update
  dependency metadata and the lockfile together.
- Every exposed tool/resource has fully typed parameters, a precise return
  type, and a client-facing description. No untyped `spec`, generic `object`,
  or stringified JSON input contracts.
- Let FastMCP generate schemas, deserialize inputs, serialize outputs, and
  own the protocol. Handwritten schemas need a documented reason.
- Register components with decorators inside `register_tools` or
  `register_resources`; keep server assembly in `create_server`.
- Handlers call services. Do not construct clients, initialize databases,
  run SQL, or perform economic calculations in handlers.
- Own shared services and external dependencies in the server lifespan.
  Keep configuration/credentials outside client-visible arguments. SQLite
  connections remain scoped to repository operations, never shared globally.
- Use async handlers for network I/O. Verify blocking behavior in the pinned
  version before adding concurrency mechanisms.
- Domain exceptions stay independent of FastMCP. Translate expected failures
  at the adapter boundary; return validation findings as structured results.
  Keep unexpected error details masked.
- Set tool annotations from actual behavior: reads and calculations are
  read-only; saving can replace existing IDs and changes timestamps.
  Annotations are hints, not permission enforcement.
- Test every exposed component through FastMCP's client, including JSON input
  and output contracts. Service tests alone do not verify MCP compatibility.
- Preserve explicit methodology: no silent weight normalization, missing-data
  substitution, series replacement, or locality application.
