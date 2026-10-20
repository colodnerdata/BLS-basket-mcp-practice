# Eval evidence (deterministic, offline)

- Command: `uv run --locked poe eval-evidence`
- Git SHA: `680f41b` (+uncommitted changes)
- Date (UTC): 2026-10-20
- FastMCP: 3.2.4
- Transport: in-memory `fastmcp.Client`; every upstream HTTP request is refused and counted; no BLS key; synthetic catalog.

Cells are passed/total checks per axis. This pack scores scripted tool sequences; it says nothing about LLM tool choice (see eval/README.md).

| Scenario | Kind | tool_choice | numeric | disclosure | invariant | Result |
|---|---|---|---|---|---|---|
| workflow_composite_escalation | workflow | 11/11 | 8/8 | 2/2 | 1/1 | PASS |
| series_choice_ambiguity | probe | 1/1 | - | 2/2 | 1/1 | PASS |
| weights_sum_0_9_not_normalized | probe | 4/4 | 1/1 | 3/3 | 1/1 | PASS |
| negative_weight_flagged | probe | 1/1 | - | 1/1 | 1/1 | PASS |
| fixed_component_with_series | probe | 1/1 | - | 1/1 | 1/1 | PASS |
| locality_on_material_disclosed | probe | 1/1 | - | 2/2 | 1/1 | PASS |
| mixed_periodicity_rejected | probe | 1/1 | 1/1 | 1/1 | 1/1 | PASS |
| missing_target_observation_not_filled | probe | 1/1 | 1/1 | 1/1 | 1/1 | PASS |
| zero_base_value_refused | probe | 1/1 | 1/1 | 1/1 | 1/1 | PASS |
| missing_key_guided_setup | probe | 2/2 | - | 3/3 | 1/1 | PASS |
| request_bounds_rejected_before_http | probe | 2/2 | - | 2/2 | 2/2 | PASS |
| registry_contract | contract | 1/1 | - | - | 1/1 | PASS |

**71/71 checks passed.**
