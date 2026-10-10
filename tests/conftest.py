"""Harness guarantees for the whole suite (see docs/TESTING.md, M0 tests).

- No test observes a real ``BLS_API_KEY`` from the developer's shell: the
  autouse fixture strips it for every test not marked ``live``. A leaked key
  would otherwise flip access status to ``configured_unverified`` and could
  let a test spend real quota if a code path ever calls the network.
- ``live`` tests are deselected by default (``addopts`` in pyproject.toml),
  are selected only by ``poe test-live``, and skip cleanly when no key is
  exported — the harness itself never fails closed.
"""

from __future__ import annotations

import os

import pytest


@pytest.fixture(autouse=True)
def _strip_bls_env(
    monkeypatch: pytest.MonkeyPatch, request: pytest.FixtureRequest
) -> None:
    """Remove BLS_API_KEY from the environment of every non-live test.

    ``live`` tests are exempt: they exist for the opt-in ``poe test-live``
    command and intentionally see the real (developer-exported) key.
    """
    if request.node.get_closest_marker("live") is not None:
        return
    monkeypatch.delenv("BLS_API_KEY", raising=False)


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    """Skip live tests cleanly when no key is exported."""
    if os.environ.get("BLS_API_KEY"):
        return
    skip = pytest.mark.skip(
        reason="BLS_API_KEY not set; live tests are opt-in (poe test-live) "
        "and follow docs/bls_etiquette.md"
    )
    for item in items:
        if item.get_closest_marker("live") is not None:
            item.add_marker(skip)
