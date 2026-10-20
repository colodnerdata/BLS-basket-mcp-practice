"""Scripted eval scenarios with hand-computed oracles.

Every expected number below is derived by hand in a comment next to the
scenario, never by importing the code under test. Scenarios are plain data
plus small predicate helpers; ``eval/runner.py`` executes them through a
real FastMCP client.

Mathematical conventions (docs/methodology.md):

- temporal factor  = target observation / base observation; a
  ``FIXED_UNINDEXED`` component has temporal factor exactly 1;
- locality factor  = target wage / reference wage, applied multiplicatively
  on top of the temporal factor (``combined = temporal * locality``);
- composite        = sum(weight_i * factor_i). Weights are used as given and
  are never normalized.

Tolerance is an absolute ``1e-9`` unless a check states otherwise; all
fixtures use short exact decimals, so double-precision error is far below it.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any, Literal

from bls_escalation_mcp.models.enums import BLSProgram
from bls_escalation_mcp.models.series import SeriesMetadata

Axis = Literal["tool_choice", "numeric", "disclosure"]
Outputs = dict[str, "Call"]
Arguments = dict[str, Any] | Callable[[Outputs], dict[str, Any]]

# Placeholder only: it is never sent anywhere (the transport rejects every
# request) and is checked to never appear in any tool output.
PLACEHOLDER_KEY = "eval-placeholder-key-not-a-secret"
TOLERANCE = 1e-9

BASE = {"year": 2024, "periodicity": "ANNUAL"}
TARGET = {"year": 2025, "periodicity": "ANNUAL"}

CATALOG = [
    SeriesMetadata(
        series_id="EVAL_PPI_STEEL_A",
        program=BLSProgram.PPI,
        title="Carbon steel castings (eval fixture A)",
        active=True,
    ),
    SeriesMetadata(
        series_id="EVAL_PPI_STEEL_B",
        program=BLSProgram.PPI,
        title="Carbon steel scrap (eval fixture B)",
        active=True,
    ),
    SeriesMetadata(
        series_id="EVAL_ECI_LABOR",
        program=BLSProgram.ECI,
        title="Construction wages and salaries (eval fixture)",
        active=True,
    ),
]


@dataclass
class Call:
    """One observed tool call."""

    tool: str
    arguments: dict[str, Any]
    is_error: bool
    error: str | None
    output: Any


@dataclass(frozen=True)
class Step:
    """One scripted tool call; ``expect_error`` says whether it must fail."""

    name: str
    tool: str
    arguments: Arguments
    expect_error: bool = False


@dataclass(frozen=True)
class Check:
    """A programmatic expectation, scored on one axis."""

    axis: Axis
    label: str
    test: Callable[[Outputs], bool]


@dataclass(frozen=True)
class Scenario:
    id: str
    kind: Literal["workflow", "probe", "contract"]
    guards: str
    steps: list[Step]
    checks: list[Check] = field(default_factory=list)
    api_key: str | None = None


def dig(value: Any, *path: str | int) -> Any:
    """Follow keys/indices; ``None`` when any hop is missing."""
    for key in path:
        try:
            value = value[key]
        except (KeyError, IndexError, TypeError):
            return None
    return value


def approx(
    step: str, path: tuple[str | int, ...], expected: float, label: str
) -> Check:
    """Numeric check against a hand-computed value."""

    def test(outputs: Outputs) -> bool:
        actual = dig(outputs[step].output, *path)
        return (
            isinstance(actual, int | float)
            and abs(actual - expected) <= TOLERANCE
        )

    return Check("numeric", f"{label} == {expected}", test)


def finding(step: str, code: str, severity: str | None = None) -> Check:
    """Validation must disclose ``code`` (and ``severity`` if given)."""

    def test(outputs: Outputs) -> bool:
        found = dig(outputs[step].output, "findings") or []
        return any(
            f["code"] == code and severity in (None, f["severity"])
            for f in found
        )

    return Check("disclosure", f"{step} reports {code}", test)


def rejected(step: str, text: str) -> Check:
    """The call must fail and say ``text`` (no silent repair)."""

    def test(outputs: Outputs) -> bool:
        call = outputs[step]
        return call.is_error and text in (call.error or "")

    return Check("disclosure", f"{step} rejected with '{text}'", test)


def no_result(step: str) -> Check:
    """A rejected call must not also hand back a computed result."""
    return Check(
        "numeric",
        f"{step} returns no computed value",
        lambda outputs: outputs[step].output is None,
    )


def holds(axis: Axis, label: str, test: Callable[[Outputs], bool]) -> Check:
    return Check(axis, label, test)


def _component(
    cid: str,
    kind: str,
    weight: float,
    series_id: str | None = None,
    **extra: Any,
) -> dict[str, Any]:
    component: dict[str, Any] = {
        "id": cid,
        "name": cid.title(),
        "component_type": kind,
        "weight": weight,
    }
    if series_id is not None:
        component["series_id"] = series_id
    component.update(extra)
    return component


def _spec(components: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "id": "eval-basket",
        "name": "Eval basket",
        "base_period": BASE,
        "target_period": TARGET,
        "components": components,
    }


def _calc(component: dict[str, Any], base: float, target: float, **kw: Any):
    return {
        "component": component,
        "base_value": base,
        "target_value": target,
        **kw,
    }


STEEL = _component("steel", "MATERIAL", 0.5, "EVAL_PPI_STEEL_A")
LABOR = _component("labor", "LABOR", 0.3, "EVAL_ECI_LABOR")
FIXED = _component("overhead", "FIXED_UNINDEXED", 0.2)


def _workflow() -> Scenario:
    # Hand derivation (weights .5/.3/.2; locality only on labor):
    #   steel    100 -> 120   temporal 1.2     combined 1.2
    #   labor    200 -> 230   temporal 1.15    locality 50/40 = 1.25
    #                         combined 1.15*1.25 = 1.4375
    #   overhead fixed        temporal 1 (target value is ignored)
    #   temporal composite  = .5*1.2 + .3*1.15 + .2*1   = 1.145  (+14.5 %)
    #   localized composite = .5*1.2 + .3*1.4375 + .2*1 = 1.23125 (+23.125 %)
    components = [STEEL, LABOR, FIXED]

    def spec_args(outputs: Outputs) -> dict[str, Any]:
        return {"spec": outputs["create"].output}

    def composite_args(outputs: Outputs) -> dict[str, Any]:
        return {
            "spec": outputs["create"].output,
            "component_values": [
                outputs[n].output for n in ("steel", "labor", "fixed")
            ],
        }

    return Scenario(
        id="workflow_composite_escalation",
        kind="workflow",
        guards=(
            "Search -> create -> validate -> calculate -> save -> read "
            "matches the hand-computed composite; temporal and locality "
            "factors stay separate; the fixed component stays at 1"
        ),
        steps=[
            Step(
                "search",
                "search_series",
                {"request": {"query": "steel", "programs": ["PPI"]}},
            ),
            Step(
                "describe",
                "describe_series",
                {"series_id": STEEL["series_id"]},
            ),
            Step(
                "create",
                "create_index_spec",
                {
                    "id": "eval-basket",
                    "name": "Eval basket",
                    "base_period": BASE,
                    "target_period": TARGET,
                    "components": components,
                },
            ),
            Step("validate", "validate_index_spec", spec_args),
            Step(
                "steel",
                "calculate_component_escalation",
                _calc(STEEL, 100, 120),
            ),
            Step(
                "locality",
                "calculate_labor_locality_factor",
                {
                    "input_data": {
                        "reference_wage": 40,
                        "target_wage": 50,
                        "source_year": 2025,
                    }
                },
            ),
            Step(
                "labor",
                "calculate_component_escalation",
                lambda o: _calc(
                    LABOR,
                    200,
                    230,
                    locality_factor=o["locality"].output["locality_factor"],
                ),
            ),
            Step(
                "fixed",
                "calculate_component_escalation",
                _calc(FIXED, 100, 999),
            ),
            Step("composite", "calculate_index_spec", composite_args),
            Step("save", "save_index_spec", spec_args),
            Step("read", "get_index_spec", {"spec_id": "eval-basket"}),
        ],
        checks=[
            approx("locality", ("locality_factor",), 1.25, "locality factor"),
            approx("labor", ("temporal_factor",), 1.15, "labor temporal"),
            approx("labor", ("combined_factor",), 1.4375, "labor combined"),
            approx("fixed", ("temporal_factor",), 1.0, "fixed temporal"),
            approx(
                "composite",
                ("temporal_composite_factor",),
                1.145,
                "temporal composite",
            ),
            approx(
                "composite",
                ("localized_composite_factor",),
                1.23125,
                "localized composite",
            ),
            approx(
                "composite", ("temporal_percent_change",), 14.5, "temporal %"
            ),
            approx(
                "composite",
                ("localized_percent_change",),
                23.125,
                "localized %",
            ),
            holds(
                "disclosure",
                "validation of the well-formed spec is clean",
                lambda o: (
                    dig(o["validate"].output, "valid") is True
                    and dig(o["validate"].output, "findings") == []
                ),
            ),
            holds(
                "disclosure",
                "creating a spec does not save it; save then read round-trips",
                lambda o: (
                    dig(o["read"].output, "result", "id") == "eval-basket"
                ),
            ),
        ],
    )


def _series_choice() -> Scenario:
    return Scenario(
        id="series_choice_ambiguity",
        kind="probe",
        guards=(
            "An ambiguous query returns every candidate with a match "
            "reason; the server never picks or substitutes a series"
        ),
        steps=[
            Step(
                "search",
                "search_series",
                {"request": {"query": "carbon steel", "programs": ["PPI"]}},
            ),
        ],
        checks=[
            holds(
                "disclosure",
                "both plausible series are returned for the model to choose",
                lambda o: (
                    {
                        r["series"]["series_id"]
                        for r in dig(o["search"].output, "result") or []
                    }
                    == {"EVAL_PPI_STEEL_A", "EVAL_PPI_STEEL_B"}
                ),
            ),
            holds(
                "disclosure",
                "every candidate carries a match reason",
                lambda o: all(
                    r.get("match_reason")
                    for r in dig(o["search"].output, "result") or [{}]
                ),
            ),
        ],
    )


def _weights_not_normalized() -> Scenario:
    # Weights .5 + .4 = .9. Silent normalization would give 1.2*.5/.9 ... so
    # the only acceptable outcomes are a flagged validation and a refusal to
    # compute; any returned composite would be a normalized/repaired value.
    components = [
        _component("steel", "MATERIAL", 0.5, "EVAL_PPI_STEEL_A"),
        _component("labor", "LABOR", 0.4, "EVAL_ECI_LABOR"),
    ]
    spec = _spec(components)
    return Scenario(
        id="weights_sum_0_9_not_normalized",
        kind="probe",
        guards=(
            "No silent weight normalization "
            "(validate flags; calculate refuses)"
        ),
        steps=[
            Step("validate", "validate_index_spec", {"spec": spec}),
            Step(
                "steel",
                "calculate_component_escalation",
                _calc(components[0], 100, 120),
            ),
            Step(
                "labor",
                "calculate_component_escalation",
                _calc(components[1], 200, 230),
            ),
            Step(
                "composite",
                "calculate_index_spec",
                lambda o: {
                    "spec": spec,
                    "component_values": [
                        o["steel"].output,
                        o["labor"].output,
                    ],
                },
                expect_error=True,
            ),
        ],
        checks=[
            finding("validate", "WEIGHTS_SUM_MISMATCH", "ERROR"),
            holds(
                "disclosure",
                "validation marks the spec invalid",
                lambda o: dig(o["validate"].output, "valid") is False,
            ),
            rejected("composite", "sum to 1"),
            no_result("composite"),
        ],
    )


def _negative_weight() -> Scenario:
    # Weights 1.2 + (-0.2) sum to 1, so only the negative-weight rule fires.
    components = [
        _component("steel", "MATERIAL", 1.2, "EVAL_PPI_STEEL_A"),
        _component("labor", "LABOR", -0.2, "EVAL_ECI_LABOR"),
    ]
    return Scenario(
        id="negative_weight_flagged",
        kind="probe",
        guards="A negative weight that hides behind a unit sum is flagged",
        steps=[
            Step(
                "validate", "validate_index_spec", {"spec": _spec(components)}
            )
        ],
        checks=[finding("validate", "NEGATIVE_WEIGHT", "ERROR")],
    )


def _fixed_component_series() -> Scenario:
    fixed = _component("overhead", "FIXED_UNINDEXED", 1.0, "EVAL_PPI_STEEL_A")
    return Scenario(
        id="fixed_component_with_series",
        kind="probe",
        guards="A fixed component cannot quietly carry an index series",
        steps=[
            Step("validate", "validate_index_spec", {"spec": _spec([fixed])})
        ],
        checks=[finding("validate", "FIXED_COMPONENT_HAS_SERIES", "ERROR")],
    )


def _locality_on_material() -> Scenario:
    material = _component(
        "steel",
        "MATERIAL",
        1.0,
        "EVAL_PPI_STEEL_A",
        locality_adjustment_enabled=True,
    )
    return Scenario(
        id="locality_on_material_disclosed",
        kind="probe",
        guards=(
            "Locality on a material is disclosed as a warning, not applied "
            "or dropped silently (temporal vs locality conflation)"
        ),
        steps=[
            Step(
                "validate", "validate_index_spec", {"spec": _spec([material])}
            )
        ],
        checks=[
            finding(
                "validate", "LOCALITY_ON_MATERIAL_OR_EQUIPMENT", "WARNING"
            ),
            holds(
                "disclosure",
                "a warning does not make the spec invalid",
                lambda o: dig(o["validate"].output, "valid") is True,
            ),
        ],
    )


def _mixed_periodicity() -> Scenario:
    return Scenario(
        id="mixed_periodicity_rejected",
        kind="probe",
        guards="A monthly period without a month is refused, not defaulted",
        steps=[
            Step(
                "create",
                "create_index_spec",
                {
                    "id": "eval-basket",
                    "name": "Eval basket",
                    "base_period": {"year": 2024, "periodicity": "MONTHLY"},
                    "target_period": TARGET,
                    "components": [STEEL],
                },
                expect_error=True,
            )
        ],
        checks=[no_result("create"), rejected("create", "month")],
    )


def _missing_target_observation() -> Scenario:
    return Scenario(
        id="missing_target_observation_not_filled",
        kind="probe",
        guards=(
            "A missing target observation is an input error; nothing is "
            "interpolated or substituted"
        ),
        steps=[
            Step(
                "calc",
                "calculate_component_escalation",
                {"component": STEEL, "base_value": 100},
                expect_error=True,
            )
        ],
        checks=[no_result("calc"), rejected("calc", "target_value")],
    )


def _zero_base() -> Scenario:
    return Scenario(
        id="zero_base_value_refused",
        kind="probe",
        guards="A zero base value is refused rather than yielding inf/NaN",
        steps=[
            Step(
                "calc",
                "calculate_component_escalation",
                _calc(STEEL, 0, 110),
                expect_error=True,
            )
        ],
        checks=[rejected("calc", "cannot be zero"), no_result("calc")],
    )


def _missing_key() -> Scenario:
    return Scenario(
        id="missing_key_guided_setup",
        kind="probe",
        guards=(
            "Without a key, status says 'missing' and observation retrieval "
            "fails with setup guidance, with zero upstream requests"
        ),
        steps=[
            Step("status", "get_bls_access_status", {}),
            Step(
                "data",
                "get_series_data",
                {
                    "series_ids": ["EVAL_PPI_STEEL_A"],
                    "start_year": 2024,
                    "end_year": 2025,
                },
                expect_error=True,
            ),
        ],
        checks=[
            holds(
                "disclosure",
                "status reports credential_status 'missing'",
                lambda o: (
                    dig(o["status"].output, "credential_status") == "missing"
                ),
            ),
            rejected("data", "BLS_API_KEY is not configured"),
            rejected("data", "setup://bls-api"),
        ],
    )


def _request_bounds() -> Scenario:
    many = [f"EVAL_{n}" for n in range(51)]
    return Scenario(
        id="request_bounds_rejected_before_http",
        kind="probe",
        guards=(
            "Over-limit requests (>50 series, >20 years) are refused before "
            "any HTTP call and name the limit"
        ),
        api_key=PLACEHOLDER_KEY,
        steps=[
            Step(
                "series",
                "get_series_data",
                {"series_ids": many, "start_year": 2024, "end_year": 2025},
                expect_error=True,
            ),
            Step(
                "years",
                "get_series_data",
                {
                    "series_ids": ["EVAL_PPI_STEEL_A"],
                    "start_year": 2000,
                    "end_year": 2020,
                },
                expect_error=True,
            ),
        ],
        checks=[
            rejected("series", "At most 50 series"),
            rejected("years", "At most 20 inclusive calendar years"),
        ],
    )


def _contract() -> Scenario:
    expected = {
        "get_bls_access_status",
        "search_series",
        "describe_series",
        "get_series_data",
        "create_index_spec",
        "save_index_spec",
        "get_index_spec",
        "calculate_component_escalation",
        "calculate_index_spec",
        "calculate_labor_locality_factor",
        "validate_index_spec",
    }
    return Scenario(
        id="registry_contract",
        kind="contract",
        guards=(
            "The exposed tool set is exactly the scripted vocabulary; an "
            "added or removed tool must update the eval pack"
        ),
        steps=[],
        checks=[
            holds(
                "tool_choice",
                "server tools == eval vocabulary",
                lambda o: (
                    set(dig(o["__registry__"].output, "tools") or [])
                    == expected
                ),
            )
        ],
    )


def all_scenarios() -> list[Scenario]:
    return [
        _workflow(),
        _series_choice(),
        _weights_not_normalized(),
        _negative_weight(),
        _fixed_component_series(),
        _locality_on_material(),
        _mixed_periodicity(),
        _missing_target_observation(),
        _zero_base(),
        _missing_key(),
        _request_bounds(),
        _contract(),
    ]
