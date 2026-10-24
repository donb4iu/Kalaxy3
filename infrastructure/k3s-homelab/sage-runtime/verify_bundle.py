"""Fail closed if supplied cluster-runtime package bytes have changed."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Dict


def verify(root: Path) -> int:
    """Validate every source file against the sealed package manifest.

    Args:
        root: Unpacked deployment package directory.

    Returns:
        Number of verified files.
    """
    manifest: Dict[str, str] = json.loads(
        (root / "bundle-sha256.json").read_text(encoding="utf-8")
    )
    for name, expected in manifest.items():
        target = (root / name).resolve()
        if not target.is_relative_to(root.resolve()) or not target.is_file():
            raise ValueError(f"unsafe or absent package file: {name}")
        actual = hashlib.sha256(target.read_bytes()).hexdigest()
        if actual != expected:
            raise ValueError(f"package integrity mismatch: {name}")
    return len(manifest)


def main() -> None:
    """Print the result of the package-integrity check."""
    try:
        count = verify(Path(sys.argv[1]))
    except (ValueError, KeyError, OSError) as exc:
        raise SystemExit(f"BLOCKED: {exc}") from exc
    print(f"SEALED DEPLOYMENT PACKAGE: PASS ({count} files)")


if __name__ == "__main__":
    main()
