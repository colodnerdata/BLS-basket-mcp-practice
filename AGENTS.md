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
