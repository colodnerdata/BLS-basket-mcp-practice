"""Run the scripted eval scenarios through a real in-memory FastMCP client.

Offline by construction: the server's HTTP transport rejects every request
(and counts it), no BLS key is read from the environment, and the catalog is
a small synthetic fixture. Nothing here touches BLS (docs/bls_etiquette.md).

Usage (from the repository root)::

    python -m eval.runner            # print the report, exit 1 on failure
    python -m eval.runner --write    # also refresh eval/results/summary.md
"""

from __future__ import annotations

import argparse
import asyncio
import datetime
import json
import logging
import subprocess
import sys
import tempfile
from dataclasses import asdict, dataclass
from importlib.metadata import version
from pathlib import Path
from typing import Any

import httpx
from fastmcp import Client

from bls_escalation_mcp.config import Settings
from bls_escalation_mcp.repositories.series import SeriesRepository
from bls_escalation_mcp.server import create_server
from eval.scenarios import (
    CATALOG,
    Axis,
    Call,
    Outputs,
    Scenario,
    all_scenarios,
)

RESULTS_DIR = Path(__file__).parent / "results"
AXES: tuple[Axis | str, ...] = (
    "tool_choice",
    "numeric",
    "disclosure",
    "invariant",
)
COMMAND = "uv run --locked poe eval-evidence"


@dataclass
class CheckResult:
    axis: str
    label: str
    passed: bool


@dataclass
class ScenarioResult:
    id: str
    kind: str
    checks: list[CheckResult]

    @property
    def passed(self) -> bool:
        return all(c.passed for c in self.checks)


class UpstreamCalls:
    """Transport that refuses (and records) any attempted HTTP request."""

    def __init__(self) -> None:
        self.count = 0

    def transport(self) -> httpx.MockTransport:
        def refuse(request: httpx.Request) -> httpx.Response:
            self.count += 1
            raise RuntimeError("eval pack must not make HTTP requests")

        return httpx.MockTransport(refuse)


def _error_text(content: list[Any]) -> str:
    return " ".join(getattr(block, "text", "") for block in content)


async def run_scenario(scenario: Scenario, work_dir: Path) -> ScenarioResult:
    """Execute ``scenario`` against a fresh server and score its checks."""
    upstream = UpstreamCalls()
    server = create_server(
        Settings(
            database_path=str(work_dir / f"{scenario.id}.db"),
            bls_api_key=scenario.api_key,
        ),
        http_transport=upstream.transport(),
    )
    outputs: Outputs = {}
    checks: list[CheckResult] = []
    async with Client(server) as client:
        registry = {tool.name for tool in await client.list_tools()}
        outputs["__registry__"] = Call(
            "list_tools", {}, False, None, {"tools": sorted(registry)}
        )
        # Startup created the schema; seed the synthetic catalog.
        repository = SeriesRepository(str(work_dir / f"{scenario.id}.db"))
        for series in CATALOG:
            repository.upsert(series)
        for step in scenario.steps:
            arguments = (
                step.arguments(outputs)
                if callable(step.arguments)
                else step.arguments
            )
            result = await client.call_tool(
                step.tool, arguments, raise_on_error=False, timeout=30
            )
            outputs[step.name] = Call(
                step.tool,
                arguments,
                result.is_error,
                _error_text(result.content) if result.is_error else None,
                None if result.is_error else result.structured_content,
            )
            checks.append(
                CheckResult(
                    "tool_choice",
                    f"{step.name}: {step.tool} exists and is "
                    f"{'refused' if step.expect_error else 'accepted'}",
                    step.tool in registry
                    and result.is_error is step.expect_error,
                )
            )
    for check in scenario.checks:
        try:
            passed = bool(check.test(outputs))
        except (KeyError, TypeError, IndexError):
            passed = False
        checks.append(CheckResult(check.axis, check.label, passed))
    serialized = json.dumps(
        {name: asdict(call) for name, call in outputs.items()}, default=str
    )
    checks.append(
        CheckResult(
            "invariant", "zero upstream HTTP requests", not upstream.count
        )
    )
    if scenario.api_key:
        checks.append(
            CheckResult(
                "invariant",
                "configured key never appears in any output",
                scenario.api_key not in serialized,
            )
        )
    return ScenarioResult(scenario.id, scenario.kind, checks)


async def run_all(scenarios: list[Scenario]) -> list[ScenarioResult]:
    with tempfile.TemporaryDirectory() as tmp:
        return [await run_scenario(s, Path(tmp)) for s in scenarios]


def _git(*args: str) -> str:
    try:
        return subprocess.run(
            ["git", *args], capture_output=True, text=True, check=True
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return ""


def render_summary(results: list[ScenarioResult]) -> str:
    """Markdown summary: per-scenario axis counts and the overall verdict."""
    sha = _git("rev-parse", "--short", "HEAD") or "unknown"
    dirty = " (+uncommitted changes)" if _git("status", "--porcelain") else ""
    lines = [
        "# Eval evidence (deterministic, offline)",
        "",
        f"- Command: `{COMMAND}`",
        f"- Git SHA: `{sha}`{dirty}",
        f"- Date (UTC): {datetime.datetime.now(datetime.UTC).date()}",
        f"- FastMCP: {version('fastmcp')}",
        "- Transport: in-memory `fastmcp.Client`; every upstream HTTP "
        "request is refused and counted; no BLS key; synthetic catalog.",
        "",
        "Cells are passed/total checks per axis. This pack scores scripted "
        "tool sequences; it says nothing about LLM tool choice "
        "(see eval/README.md).",
        "",
        "| Scenario | Kind | " + " | ".join(AXES) + " | Result |",
        "|---|---|" + "---|" * (len(AXES) + 1),
    ]
    for result in results:
        cells = []
        for axis in AXES:
            axis_checks = [c for c in result.checks if c.axis == axis]
            ok = sum(c.passed for c in axis_checks)
            cells.append(f"{ok}/{len(axis_checks)}" if axis_checks else "-")
        lines.append(
            f"| {result.id} | {result.kind} | "
            + " | ".join(cells)
            + f" | {'PASS' if result.passed else 'FAIL'} |"
        )
    total = sum(len(r.checks) for r in results)
    passed = sum(c.passed for r in results for c in r.checks)
    lines += ["", f"**{passed}/{total} checks passed.**", ""]
    return "\n".join(lines)


def failures(results: list[ScenarioResult]) -> list[str]:
    return [
        f"{r.id}: [{c.axis}] {c.label}"
        for r in results
        for c in r.checks
        if not c.passed
    ]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--write",
        action="store_true",
        help="refresh eval/results/summary.md and the gitignored raw.json",
    )
    args = parser.parse_args(argv)
    # Probes provoke expected tool errors; keep FastMCP's tracebacks out.
    logging.disable(logging.CRITICAL)
    results = asyncio.run(run_all(all_scenarios()))
    summary = render_summary(results)
    print(summary)
    failed = failures(results)
    for line in failed:
        print(f"FAILED {line}", file=sys.stderr)
    if args.write:
        RESULTS_DIR.mkdir(exist_ok=True)
        (RESULTS_DIR / "summary.md").write_text(summary, encoding="utf-8")
        (RESULTS_DIR / "raw.json").write_text(
            json.dumps([asdict(r) for r in results], indent=2),
            encoding="utf-8",
        )
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
