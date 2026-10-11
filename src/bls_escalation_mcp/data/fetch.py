"""Download BLS flat files with conditional requests (owner-invoked).

This is the live half of M2'. It exists for deliberate, owner-run
downloads only — never an MCP tool — and enforces
``docs/bls_etiquette.md`` by construction:

- an identifying ``User-Agent`` with a contact address is required;
- requests are sequential with a minimum delay between them (no
  parallelism, ever);
- any 4xx/5xx stops the run immediately — no automatic retries (a retry
  feature, if ever added, must respect 429/Retry-After and cap attempts).

Conditional refresh uses the validators recorded in the *manifest* (the
probe showed every file sends ``ETag``/``Last-Modified`` and honors 304):
a re-download of an unchanged file costs one conditional request. Content
integrity: downloads land in a ``.partial`` sibling and rename only after
the full body and its ``Content-Length`` agree, so a failed run leaves the
previous good copy in place.

Sync client by design: this is a sequential, rate-limited CLI, not an MCP
network handler (the async convention covers handlers).
"""

from __future__ import annotations

import argparse
import hashlib
import os
import sys
import time
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

import httpx

from bls_escalation_mcp.config import Settings, get_settings
from bls_escalation_mcp.data.ingest import IngestionService, classify_file
from bls_escalation_mcp.data.manifest import (
    DEFAULT_MANIFEST_PATH,
    load_manifest,
)
from bls_escalation_mcp.db.connection import get_database_path
from bls_escalation_mcp.db.schema import initialize_schema

DEFAULT_DOWNLOAD_DIR = Path("data/download")


class FetchBlockedError(RuntimeError):
    """BLS returned an error status; the run stops (etiquette rule 3)."""


@dataclass(frozen=True)
class FetchOutcome:
    """Result of fetching one file."""

    canonical_name: str
    status: str  # "downloaded" | "unchanged" (304)
    path: Path
    size_bytes: int = 0
    sha256: str = ""
    etag: str | None = None
    last_modified: str | None = None


class FlatFileFetcher:
    """Sequential conditional-GET fetcher for ``download.bls.gov`` files.

    Parameters
    ----------
    user_agent:
        Required: descriptive product name with a contact address (BLS has
        rejected anonymous traffic). No default on purpose.
    delay_seconds:
        Minimum pause between requests (default 1s).
    sleep:
        Sleep injectable for tests.
    transport:
        An ``httpx`` transport (e.g. ``MockTransport``) for tests.
    """

    def __init__(
        self,
        user_agent: str,
        *,
        delay_seconds: float = 1.0,
        sleep: Callable[[float], None] = time.sleep,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        if not user_agent or "@" not in user_agent:
            raise ValueError(
                "a descriptive User-Agent with a contact address is "
                "required (docs/bls_etiquette.md)"
            )
        self.delay_seconds = delay_seconds
        self._sleep = sleep
        self.request_log: list[httpx.Request] = []
        self._last_request = 0.0
        self._client = httpx.Client(
            headers={"User-Agent": user_agent},
            follow_redirects=True,
            timeout=60.0,
            transport=transport,
        )

    def close(self) -> None:
        self._client.close()

    def _paced(self) -> None:
        elapsed = time.monotonic() - self._last_request
        if elapsed < self.delay_seconds:
            self._sleep(self.delay_seconds - elapsed)
        self._last_request = time.monotonic()

    def fetch(
        self,
        program: str,
        canonical_name: str,
        dest_dir: Path,
        *,
        etag: str | None = None,
        last_modified: str | None = None,
    ) -> FetchOutcome:
        """Fetch one file; return ``unchanged`` on a 304.

        Pass the manifest-recorded validators so an unchanged file costs
        one request. On 200 the body is verified against Content-Length
        (when the server sends one) before the atomic rename.
        """
        url = (
            f"https://download.bls.gov/pub/time.series/{program}/"
            f"{canonical_name}"
        )
        headers: dict[str, str] = {}
        if etag:
            headers["If-None-Match"] = etag
        if last_modified:
            headers["If-Modified-Since"] = last_modified
        self._paced()
        try:
            response = self._client.get(url, headers=headers)
        except httpx.HTTPError as exc:
            raise FetchBlockedError(
                f"network error fetching {url}: {exc}"
            ) from exc
        self.request_log.append(response.request)
        if response.status_code == 304:
            return FetchOutcome(
                canonical_name,
                "unchanged",
                dest_dir / canonical_name,
                etag=etag,
                last_modified=last_modified,
            )
        if response.status_code != 200:
            raise FetchBlockedError(
                f"{url} returned {response.status_code}; stopping. Do not "
                "probe a block page — see docs/bls_etiquette.md."
            )
        body = response.content
        declared = response.headers.get("content-length")
        if declared is not None and int(declared) != len(body):
            raise FetchBlockedError(
                f"{url}: truncated download ({len(body)} != {declared}); "
                "the previous copy (if any) is left in place."
            )
        dest_dir.mkdir(parents=True, exist_ok=True)
        target = dest_dir / canonical_name
        partial = target.with_name(target.name + ".partial")
        partial.write_bytes(body)
        os.replace(partial, target)  # atomic: previous copy survives failure
        return FetchOutcome(
            canonical_name,
            "downloaded",
            target,
            size_bytes=len(body),
            sha256=hashlib.sha256(body).hexdigest(),
            etag=response.headers.get("etag"),
            last_modified=response.headers.get("last-modified"),
        )


def fetch_many(
    file_names: list[str],
    dest_dir: Path,
    *,
    settings: Settings | None = None,
    sleep: Callable[[float], None] = time.sleep,
    transport: httpx.BaseTransport | None = None,
    ingest: bool = True,
    database_path: str | None = None,
    manifest_path: Path = DEFAULT_MANIFEST_PATH,
) -> tuple[list[FetchOutcome], list[str]]:
    """Fetch then ingest each file; shared by the CLI and tests.

    Returns ``(outcomes, skipped_unchanged)``. A blocked fetch raises and
    halts before later files are attempted.
    """
    manifest = load_manifest(manifest_path)
    by_url = {entry.source_url: entry for entry in manifest.files}
    ua = (settings or get_settings()).bls_user_agent
    fetcher = FlatFileFetcher(ua or "", sleep=sleep, transport=transport)
    if ingest:
        initialize_schema(get_database_path(database_path))
        service = IngestionService(
            get_database_path(database_path), manifest_path
        )
    results: list[FetchOutcome] = []
    unchanged: list[str] = []
    try:
        for name in file_names:
            classified = classify_file(Path(name).name)
            if classified is None:
                raise ValueError(
                    f"{name!r} is not a known flat-file name (program/series/"
                    "mapping/data naming); see docs/bulk_files.md"
                )
            program, _, canonical = classified
            url = (
                f"https://download.bls.gov/pub/time.series/{program}/"
                f"{canonical}"
            )
            prior = by_url.get(url)
            outcome = fetcher.fetch(
                program,
                canonical,
                dest_dir,
                etag=prior.bls_etag if prior else None,
                last_modified=prior.bls_last_modified if prior else None,
            )
            results.append(outcome)
            if outcome.status == "unchanged":
                unchanged.append(canonical)
                continue
            if ingest:
                service.ingest_file(
                    outcome.path,
                    program=program,
                    kind=classified[1],
                    canonical_name=canonical,
                    ingested_by=f"fetch {outcome.sha256[:12]}",
                    downloaded_at=datetime.now(UTC),
                    notes=None,
                )
    finally:
        fetcher.close()
    return results, unchanged


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Owner-invoked conditional download+ingest of BLS "
        "flat files (docs/bls_etiquette.md)."
    )
    parser.add_argument(
        "files",
        nargs="+",
        help="Canonical file names, e.g. wp.data.9.Lumber ci.data.0.Current",
    )
    parser.add_argument(
        "--dir",
        type=Path,
        default=DEFAULT_DOWNLOAD_DIR,
        help=f"Download directory (default: {DEFAULT_DOWNLOAD_DIR}; "
        "git-ignored on purpose)",
    )
    parser.add_argument("--db", default=None, help="Database path")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST_PATH)
    parser.add_argument(
        "--no-ingest",
        action="store_true",
        help="Download only (leave ingestion for a later ingest run)",
    )
    args = parser.parse_args()
    outcomes, unchanged = fetch_many(
        args.files,
        args.dir,
        ingest=not args.no_ingest,
        database_path=args.db,
        manifest_path=args.manifest,
    )
    for outcome in outcomes:
        detail = (
            f"{outcome.size_bytes} bytes sha256 {outcome.sha256[:12]}"
            if outcome.status == "downloaded"
            else "not modified (304)"
        )
        print(f"{outcome.status}: {outcome.canonical_name} — {detail}")
    print(
        f"{len([o for o in outcomes if o.status == 'downloaded'])} "
        f"downloaded, {len(unchanged)} unchanged (conditional request)."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
