#!/usr/bin/env python3
"""Refresh the SQLite-backed BLS catalogue metadata."""

from __future__ import annotations

import argparse

from bls_escalation_mcp.config import get_settings
from bls_escalation_mcp.data.loaders.eci import ECILoader
from bls_escalation_mcp.data.loaders.oews import OEWSLoader
from bls_escalation_mcp.data.loaders.ppi import PPILoader
from bls_escalation_mcp.db.connection import initialize_database


def main() -> None:
    """Initialize the database and load the configured BLS metadata sources."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--database",
        type=str,
        default=None,
        help="SQLite database path. Defaults to the configured path.",
    )
    parser.add_argument(
        "--source",
        choices=["ppi", "eci", "oews", "all"],
        default="all",
    )
    args = parser.parse_args()

    settings = get_settings()
    database_path = args.database or settings.database_path
    initialize_database(database_path)

    loaders = {
        "ppi": PPILoader(database_path=database_path),
        "eci": ECILoader(database_path=database_path),
        "oews": OEWSLoader(database_path=database_path),
    }

    requested = [args.source] if args.source != "all" else list(loaders)
    for source in requested:
        loader = loaders[source]
        print(f"Loading {source} metadata via {loader.__class__.__name__}...")
        count = loader.load()
        print(f"Loaded {count} records for {source}.")


if __name__ == "__main__":
    main()
