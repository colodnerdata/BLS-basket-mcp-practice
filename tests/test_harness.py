"""Meta-tests for the harness guarantees in tests/conftest.py."""

from __future__ import annotations

import os

import pytest

SENTINEL = "m0-harness-sentinel"


def test_env_leak_from_prior_test_a() -> None:
    # Deliberately leak a key into the real process environment, bypassing
    # monkeypatch, so it would persist without harness isolation.
    os.environ["BLS_API_KEY"] = SENTINEL


def test_env_leak_from_prior_test_b() -> None:
    """No test observes a key leaked by a prior test or exported in the shell.

    Relies on pytest's in-module definition order (a runs before b) and on
    the autouse fixture in conftest.py; without it this test sees the
    sentinel and fails.
    """
    assert os.environ.get("BLS_API_KEY") != SENTINEL


@pytest.mark.live
def test_live_marker_seam() -> None:
    """Prove the live seam: only `poe test-live` selects this test.

    Skipped cleanly without an exported key (see tests/conftest.py). Makes
    no network call; the live checks that land with the deferred live-API
    path make the real, budgeted requests per docs/bls_etiquette.md.
    """
    assert os.environ.get("BLS_API_KEY"), (
        "export BLS_API_KEY to run live tests"
    )
