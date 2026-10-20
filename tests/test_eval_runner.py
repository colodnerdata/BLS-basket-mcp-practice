"""The offline eval pack (eval/) runs green and can actually fail."""

from __future__ import annotations

import dataclasses
import pytest

from eval.runner import failures, render_summary, run_all, run_scenario
from eval.scenarios import Check, Scenario, all_scenarios


@pytest.mark.asyncio
async def test_pack_passes_with_zero_upstream_requests() -> None:
    results = await run_all(all_scenarios())
    assert failures(results) == []
    # Every scenario carries the offline invariant.
    assert all(any(c.axis == "invariant" for c in r.checks) for r in results)
    assert "checks passed" in render_summary(results)


@pytest.mark.asyncio
async def test_wrong_oracle_and_wrong_script_are_reported() -> None:
    workflow: Scenario = all_scenarios()[0]
    bad_oracle = dataclasses.replace(
        workflow,
        checks=[Check("numeric", "deliberately wrong", lambda outputs: False)],
    )
    result = await run_scenario(bad_oracle, tmp_path)
    assert not result.passed
    assert [c.label for c in result.checks if not c.passed] == [
        "deliberately wrong"
    ]
    # A step scripted to fail that succeeds (or vice versa) is flagged.
    flipped = dataclasses.replace(
        workflow,
        steps=[dataclasses.replace(workflow.steps[0], expect_error=True)],
        checks=[],
    )
    result = await run_scenario(flipped, tmp_path)
    assert not result.passed
