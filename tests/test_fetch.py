from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import httpx

from bls_escalation_mcp.config import Settings
from bls_escalation_mcp.data.fetch import FlatFileFetcher, fetch_many
from bls_escalation_mcp.data.manifest import (
    IngestionManifest,
    ManifestFile,
    save_manifest,
)


def test_flat_file_fetcher_download_and_conditional_304(
    tmp_path: Path,
) -> None:
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        if request.headers.get("If-None-Match") == "etag-1":
            return httpx.Response(
                304,
                headers={
                    "etag": "etag-1",
                    "last-modified": "Wed, 01 Jan 2025 00:00:00 GMT",
                },
            )
        body = b"abc"
        return httpx.Response(
            200,
            content=body,
            headers={
                "content-length": str(len(body)),
                "etag": "etag-1",
                "last-modified": "Wed, 01 Jan 2025 00:00:00 GMT",
            },
        )

    transport = httpx.MockTransport(handler)
    fetcher = FlatFileFetcher(
        "Example Ops <ops@example.com>",
        sleep=lambda _: None,
        transport=transport,
    )

    outcome = fetcher.fetch("pc", "pc.data.0.Current", tmp_path)
    assert outcome.status == "downloaded"
    assert (tmp_path / "pc.data.0.Current").read_bytes() == b"abc"
    assert seen[0].headers["User-Agent"] == "Example Ops <ops@example.com>"

    changed = fetcher.fetch(
        "pc",
        "pc.data.0.Current",
        tmp_path,
        etag="etag-1",
        last_modified="Wed, 01 Jan 2025 00:00:00 GMT",
    )
    assert changed.status == "unchanged"
    assert seen[1].headers["If-None-Match"] == "etag-1"
    assert (
        seen[1].headers["If-Modified-Since"]
        == "Wed, 01 Jan 2025 00:00:00 GMT"
    )
    fetcher.close()


def test_fetch_many_uses_settings_and_manifest_validators(
    tmp_path: Path,
) -> None:
    manifest_path = tmp_path / "manifest.json"
    save_manifest(
        manifest_path,
        IngestionManifest(
            files=[
                ManifestFile(
                    file_id="pc/pc.data.0.Current",
                    program="pc",
                    kind="data",
                    source_url=(
                        "https://download.bls.gov/pub/time.series/pc/"
                        "pc.data.0.Current"
                    ),
                    path_in_repo="tmp/pc.data.0.Current",
                    downloaded_at=datetime.now(UTC),
                    bls_last_modified="Wed, 01 Jan 2025 00:00:00 GMT",
                    bls_etag="etag-1",
                    size_bytes=3,
                    sha256="abc123",
                    ingested_at=datetime.now(UTC),
                    ingested_by="test",
                )
            ]
        ),
    )

    def handler(request: httpx.Request) -> httpx.Response:
        if request.headers.get("If-None-Match") == "etag-1":
            return httpx.Response(
                304,
                headers={
                    "etag": "etag-1",
                    "last-modified": "Wed, 01 Jan 2025 00:00:00 GMT",
                },
            )
        body = b"abc"
        return httpx.Response(
            200,
            content=body,
            headers={
                "content-length": str(len(body)),
                "etag": "etag-1",
                "last-modified": "Wed, 01 Jan 2025 00:00:00 GMT",
            },
        )

    outcomes, unchanged = fetch_many(
        ["pc.data.0.Current"],
        tmp_path,
        settings=Settings(
            bls_user_agent="Example Ops <ops@example.com>",
            database_path=str(tmp_path / "catalog.db"),
        ),
        sleep=lambda _: None,
        transport=httpx.MockTransport(handler),
        ingest=False,
        manifest_path=manifest_path,
    )

    assert outcomes[0].status == "unchanged"
    assert unchanged == ["pc.data.0.Current"]


def test_fetch_many_persists_emittted_validators_into_manifest(
    tmp_path: Path,
) -> None:
    manifest_path = tmp_path / "manifest.json"
    save_manifest(manifest_path, IngestionManifest())

    def handler(request: httpx.Request) -> httpx.Response:
        body = (
            b"series_id\tyear\tperiod\tvalue\tfootnote_codes\n"
            b"PCU123456123456\t2025\tM01\t100.0\t\n"
        )
        return httpx.Response(
            200,
            content=body,
            headers={
                "content-length": str(len(body)),
                "etag": "etag-2",
                "last-modified": "Wed, 02 Jan 2025 00:00:00 GMT",
            },
        )

    db_path = tmp_path / "catalog.db"
    outcomes, unchanged = fetch_many(
        ["pc.data.0.Current"],
        tmp_path,
        settings=Settings(
            bls_user_agent="Example Ops <ops@example.com>",
            database_path=str(db_path),
        ),
        sleep=lambda _: None,
        transport=httpx.MockTransport(handler),
        manifest_path=manifest_path,
    )

    assert outcomes[0].status == "downloaded"
    assert unchanged == []
    saved = manifest_path.read_text("utf-8")
    assert '"bls_etag": "etag-2"' in saved
    assert '"bls_last_modified": "Wed, 02 Jan 2025 00:00:00 GMT"' in saved
