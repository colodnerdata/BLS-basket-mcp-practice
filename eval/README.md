# Agent evaluations

**Status: the deterministic offline pack is implemented; the LLM-backed
harness is not.** This is the evaluation entry point corresponding to the GSA
template's `eval/` directory. Deterministic unit tests remain in `tests/`;
[docs/TESTING.md](../docs/TESTING.md) records what each scenario guards
against.

```
uv run --locked poe eval-evidence   # runs the pack, refreshes results/summary.md
```

- `scenarios.py` - scripted scenarios: ordered tool calls plus programmatic
  checks. Expected numbers are hand-derived literals (arithmetic in comments),
  never computed by the code under test.
- `runner.py` - runs each scenario through a real in-memory `fastmcp.Client`
  against a fresh server and synthetic catalog, with every upstream HTTP
  request refused and counted. Failed calls are inspected with
  `raise_on_error=False`; numbers are scored from `structured_content`.
- `results/summary.md` - committed record (git SHA, command, per-axis pass
  counts). `results/raw.json` is gitignored.

Scores are kept on separate axes (tool choice, numeric correctness,
methodology disclosure, plus an offline invariant) so a regression in one is
not hidden by the others. Because the tool sequences are scripted, this pack
does **not** measure LLM tool choice or judgment under ambiguity; do not claim
agent performance from it. A model-backed harness could reuse the scenario
files as tasks and score the model's actual calls with the same checks.

Never run anything here against live BLS; see
[docs/bls_etiquette.md](../docs/bls_etiquette.md).
