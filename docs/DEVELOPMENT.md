# Development

## Commands

The template-style launcher is `uv run --locked python main.py`; see
[QUICKSTART.md](../QUICKSTART.md). Regenerate buildpack dependencies with
`uv run --locked poe export-requirements` after dependency changes. Do not
hand-edit `requirements.txt`; the lockfile remains authoritative. Docker and
vendor deployment validation are separate from `poe check`.

The project uses uv for its environment and lockfile, Poe for commands, Ruff
for lint and formatting, and pytest for tests. `pyproject.toml` is the command
source of truth. The development Python version is in `.python-version`.

| Purpose | Command |
| --- | --- |
| Reproduce the environment | `uv sync --locked` |
| Run the CI checks locally | `uv run --locked poe check` |
| Run tests | `uv run --locked poe test` |
| Type check | `uv run --locked poe typecheck` |
| Lint | `uv run --locked poe lint` |
| Apply formatting | `uv run --locked poe format` |
| Check formatting | `uv run --locked poe format-check` |
| Add a runtime dependency | `uv add PACKAGE` |
| Add a development dependency | `uv add --dev PACKAGE` |
| Deliberately refresh dependencies | `uv lock --upgrade` |

Commit dependency metadata and `uv.lock` together, and rerun `check` after
updates. `--locked` detects stale dependency metadata instead of silently
refreshing it. Review the dependency diff before merging it.

## A small development loop

1. Write down the expected behavior and the smallest useful change.
2. Use a short-lived branch for substantive work or AI-generated changes.
3. Implement the change and a test that could detect a real mistake.
4. Run the relevant focused test, then `check` before merging.
5. Read the diff yourself. Check assumptions, boundary cases, error behavior,
   dependencies, and anything an AI reviewer missed.
6. Merge the completed change and remove its branch.

A PR is a useful checkpoint even when you are its only human reviewer.
Small prose fixes can use a direct commit when that is simpler. Choose any
enforced main-branch rules accordingly. An issue is useful for a reproducible
bug or a larger chunk of work; it need not precede every edit.

## Tests that earn their maintenance cost

- Test observable behavior and mathematical invariants.
- Use hand-computable cases or an independent reference implementation for
  numerical results. Record tolerances and their reason.
- Include invalid inputs, degenerate cases, and past failure cases.
- A bug fix should normally have a test that fails without the fix.
- Use mocks to isolate boundaries, then test the real boundary when needed.
- Add property-based tests, type checking, coverage reporting, and additional
  Python/OS CI jobs when they address a specific risk. A coverage percentage
  is a diagnostic, not proof of correctness.

The initial CI job uses Python 3.12 on Linux. The starter permits Python 3.12
and later, but makes no claim to have tested every permitted version. Add a
supported-version matrix when this becomes a library used by other people.
If Windows or another platform is part of the product contract, test it too.

## Deliverables and integrations

For a workbook, UI, native dependency, GPU, or external service, add a specific
verification command and document its environment requirement here. Keep it
separate from headless checks. A missing required environment is a reported
limitation, not a passing integration check.

For generated files, use the order: build, verify that output, then publish.
If a check cannot run in CI, retain concise evidence tied to the commit,
command, environment, and artifact. Save useful failures as well as successes;
keep routine terminal logs out of the repository.

Keep source and generated output ownership clear. Prefer release assets for
large distributables; commit a generated artifact only when it serves a clear
purpose. Do not hand-edit a generated file whose source can be rebuilt.

## Resume without rereading a conversation

Use `docs/NEXT.md` for the current objective and a few next actions. Put detailed
work in issues if needed, and link to them instead of maintaining two backlogs.
Use `docs/DECISIONS.md` for decisions that explain an otherwise surprising
constraint, a rejected alternative, or a tradeoff likely to be revisited.
Add architecture documentation when actual boundaries become worth explaining.

## Release when there is something to release

Choose a license, document an example, verify the actual deliverable, and tag
the release. Keep a short changelog once users rely on versioned behavior.
Mark incompatible changes explicitly. Add publishing automation when the
manual sequence is stable and repeated often enough to justify it.

Dependabot is configured for monthly grouped uv and Actions update PRs, with
one open version-update PR per ecosystem. Review and test them; nothing here
auto-merges or publishes a release. Configure GitHub security alerts separately
where available so important notices do not wait for a monthly maintenance pass.


MCP integration tests use `Client(create_server(...))` with a temporary SQLite
database and mocked HTTP transport. They exercise the real MCP boundary without
claiming live BLS or network-transport validation. The launcher configuration in
`fastmcp.json` uses the installed locked environment; it does not duplicate the
dependency list in a separate environment definition.


## Code scanning

`.github/workflows/codeql.yml` is CodeQL advanced setup for Python and GitHub
Actions, `build-mode: none` (scanning does not run tests or make live BLS
calls), default security query suites, no excluded paths, SHA-pinned actions,
and `security-events: write` scoped to only the analysis job.

**Automatic triggers are currently disabled** (`workflow_dispatch` only): this
repository is private without GitHub Advanced Security enabled, so the
analyze job's SARIF upload fails every run with "Code scanning is not enabled
for this repository" — a repository-settings gap, not a scan finding or a
problem in a PR's diff. See `docs/DECISIONS.md`, "CodeQL scanning disabled
pending GitHub Advanced Security." Once a repo admin enables GitHub Advanced
Security in Settings > Code security, restore the `push`/`pull_request`/
`schedule` triggers (do not also enable GitHub's default code-scanning
setup — this is the advanced setup, and running both conflicts). Until then,
no CodeQL findings are being produced; passing ordinary CI does not establish
that code scanning ran or that no security findings exist.
