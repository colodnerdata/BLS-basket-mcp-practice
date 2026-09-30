"""Check the starter's installed package, not application correctness."""

import subprocess
import sys
from pathlib import Path


def test_package_imports_outside_checkout(tmp_path: Path) -> None:
    """Ensure installation makes the src-layout package importable."""
    result = subprocess.run(
        [sys.executable, "-I", "-c", "import bls_escalation_mcp"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
