# Agent evaluations

**Status: planned, not implemented.** This is the evaluation entry point
corresponding to the GSA template's `eval/` directory. Deterministic tests
remain in `tests/`; [docs/TESTING.md](../docs/TESTING.md) records their scope.

Implement milestone M5 from [the roadmap](../docs/ROADMAP.md) before claiming
agent performance. Include missing-key setup, explicit weights, series-choice
ambiguity, temporal/locality separation, missing observations, and request
bounds. Score tool choice, numerical correctness, and methodology disclosure
separately, using programmatic expectations wherever possible.

No evaluation framework or model dependency is added by shell alignment.
