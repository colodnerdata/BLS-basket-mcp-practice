#!/usr/bin/env python3
"""Record HTTP headers for every file in a BLS flat-file directory.

Answers the open questions in ``docs/bulk_files.md``: does the server send
``ETag`` / ``Last-Modified`` / ``Content-Length`` and does it honor
conditional requests (304)? Only ``HEAD`` requests are made, so no data file
is downloaded. Requests are sequential with a delay.

Example
-------
    uv run --locked python scripts/probe_bls_headers.py pc \\
        --user-agent "bls-basket-mcp-practice you@example.com"

The ``User-Agent`` must carry a real contact address; BLS has rejected
anonymous clients. It can also come from ``BLS_USER_AGENT``.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
import time
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse

import httpx

BASE_URL = "https://download.bls.gov/pub/time.series/"
HEADERS_OF_INTEREST = (
    "content-length",
    "last-modified",
    "etag",
    "accept-ranges",
    "cache-control",
    "content-type",
    "content-encoding",
    "server",
)


class _LinkParser(HTMLParser):
    """Collect ``href`` values from anchor tags."""

    def __init__(self) -> None:
        super().__init__()
        self.hrefs: list[str] = []

    def handle_starttag(
        self, tag: str, attrs: list[tuple[str, str | None]]
    ) -> None:
        if tag == "a":
            for name, value in attrs:
                if name == "href" and value:
                    self.hrefs.append(value)


def list_files(listing_html: str, directory_url: str) -> list[str]:
    """Return absolute URLs of files directly inside ``directory_url``.

    Links to the parent directory, sub-directories (trailing ``/``), sort
    links (``?``) and anything outside the directory are skipped.
    """
    parser = _LinkParser()
    parser.feed(listing_html)
    directory_path = urlparse(directory_url).path
    urls: list[str] = []
    for href in parser.hrefs:
        url = urljoin(directory_url, href)
        parsed = urlparse(url)
        if parsed.query or parsed.path.endswith("/"):
            continue
        parent, _, _ = parsed.path.rpartition("/")
        if parent + "/" != directory_path:
            continue
        if url not in urls:
            urls.append(url)
    return urls


def probe(client: httpx.Client, url: str) -> dict[str, str]:
    """HEAD ``url``, then repeat conditionally using the validators seen."""
    row: dict[str, str] = {"file": url.rsplit("/", 1)[-1]}
    first = client.head(url)
    row["status"] = str(first.status_code)
    for name in HEADERS_OF_INTEREST:
        row[name] = first.headers.get(name, "")
    conditional: dict[str, str] = {}
    if first.headers.get("etag"):
        conditional["If-None-Match"] = first.headers["etag"]
    if first.headers.get("last-modified"):
        conditional["If-Modified-Since"] = first.headers["last-modified"]
    if conditional:
        second = client.head(url, headers=conditional)
        row["conditional_status"] = str(second.status_code)
    else:
        row["conditional_status"] = "no validators"
    return row


def main() -> int:
    """Probe every file in one program directory and write the results."""
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("program", nargs="?", default="pc")
    parser.add_argument(
        "--user-agent",
        default=os.environ.get("BLS_USER_AGENT"),
        help="Identifying User-Agent with contact address.",
    )
    parser.add_argument("--delay", type=float, default=1.0)
    parser.add_argument("--timeout", type=float, default=30.0)
    parser.add_argument(
        "--out",
        default=None,
        help="Optional JSON output path (for example docs/sample_data/).",
    )
    args = parser.parse_args()
    if not args.user_agent or "@" not in args.user_agent:
        parser.error("--user-agent (or BLS_USER_AGENT) with an email needed")

    directory_url = f"{BASE_URL}{args.program}/"
    rows: list[dict[str, str]] = []
    with httpx.Client(
        headers={"User-Agent": args.user_agent},
        timeout=args.timeout,
        follow_redirects=True,
    ) as client:
        listing = client.get(directory_url)
        listing.raise_for_status()
        files = list_files(listing.text, directory_url)
        if not files:
            print(f"No files found at {directory_url}", file=sys.stderr)
            return 1
        for url in files:
            time.sleep(args.delay)
            try:
                rows.append(probe(client, url))
            except httpx.HTTPError as exc:
                rows.append(
                    {
                        "file": url.rsplit("/", 1)[-1],
                        "status": f"error: {type(exc).__name__}",
                    }
                )

    fields = [
        "file",
        "status",
        *HEADERS_OF_INTEREST,
        "conditional_status",
    ]
    writer = csv.DictWriter(
        sys.stdout, fieldnames=fields, delimiter="\t", restval=""
    )
    writer.writeheader()
    writer.writerows(rows)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as handle:
            json.dump(
                {"directory": directory_url, "files": rows}, handle, indent=2
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
