# Agent instructions

This is the canonical source of project instructions for coding assistants.
Tool-specific entry points should reference it instead of copying its rules.

## Get oriented

1. Read `README.md` and `docs/NEXT.md` for purpose and current work.
2. Read `docs/DEVELOPMENT.md` for commands and verification boundaries, and
   `docs/hackathon_template.md` for required template conventions.
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


## BLS site etiquette

BLS throttles or blocks excessive automated access, and a block lands on the
owner's whole network. `docs/bls_etiquette.md` is binding on every command
and run in this repository. Core rules: checks and tests never touch BLS;
live calls and flat-file downloads are opt-in and owner-invoked, never
started by an agent on its own; stay inside the published API bounds; no
retry loops and no evading limits; download flat files once and reuse them
with their retrieval date recorded. On any throttling signal, stop the whole
run and report — do not probe.

- Verify APIs against the supported FastMCP version's official documentation.
  Record version and lifecycle decisions in `docs/DECISIONS.md`; update
  dependency metadata and the lockfile together.
- Every exposed tool/resource has fully typed parameters, a precise return
  type, and a client-facing description. No untyped `spec`, generic `object`,
  or stringified JSON input contracts.
- Let FastMCP generate schemas, deserialize inputs, serialize outputs, and
  own the protocol. Handwritten schemas need a documented reason.
- Register each new component with decorators inside its module's
  `register(mcp: FastMCP) -> None`; package aggregators expose
  `register_tools`, `register_resources`, or `register_prompts`. Keep server
  assembly in `create_server`.
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


## GSA MCP Hackathon template conventions

- Follow the pinned template and mapping in `docs/hackathon_template.md`.
  Template updates require a reviewed comparison; do not blindly copy upstream
  examples, dependencies, deployment settings, or agent instructions.
- Use **one exposed tool per Python file** under
  `src/bls_escalation_mcp/mcp/tools/`, named for the tool's purpose. Reusable
  logic belongs in services/adapters, not a second tool in the same file.
- Use one exposed prompt or resource per file in the corresponding `mcp/`
  package. Each component module exposes `register(mcp: FastMCP) -> None`;
  its package `__init__.py` explicitly aggregates registrations. Adding or
  removing a component must update that aggregator and client contract tests.
  `create_server` calls the aggregators; avoid import-time registration.
- Preserve public names, schemas, annotations, and behavior during layout
  refactors unless the requested work explicitly changes them. Register each
  component exactly once through its package aggregator. Do not introduce
  grouped component modules or direct per-module wiring in `server.py`.
- Keep `main.py` and `app.py` thin; transport selection belongs in the launcher,
  HTTP probes in `routes.py`, and assembly/lifecycle in the existing factory.
  Preserve stdio defaults and platform-port precedence. Do not flatten the
  domain model/service/repository packages to mimic example filenames.
- Add operator settings as typed configuration fields and document them in
  `.env.example`. Keep credentials out of component arguments and responses.
  Update quickstart/deployment instructions when launch behavior changes.
- Keep `uv.lock` authoritative. Dependency changes update `pyproject.toml`,
  `uv.lock`, and the generated `requirements.txt` via `poe export-requirements`.
  Keep Docker/buildpack Python requirements compatible with the project.
- Maintain `/health` and `/version`, deployment drafts, `server.json` identity
  and version, security boundaries, and template mapping when affected.
  Never turn a draft into a claimed deployment or published endpoint without
  actual validation. Keep deterministic tests and agent evals distinct;
  document eval status in both `eval/README.md` and `docs/TESTING.md`.
- Document any deliberate exception in `docs/DECISIONS.md` and update the
  template mapping in the same change, explaining scope and reason.
