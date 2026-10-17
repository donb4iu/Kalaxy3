#!/usr/bin/env python3
"""Validate exact Architecture Helper bytes before a deployment render."""
import hashlib
import json
import sys
from pathlib import Path


def digest(path: Path) -> str:
    """Hash a regular non-symlink source file."""
    if not path.is_file() or path.is_symlink():
        raise ValueError(f"Missing or unsafe file: {path}")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify(root: Path) -> dict:
    """Verify the static projection manifest and bounded file identities."""
    names = ("index.html", "evidence.json", "artifact-manifest.json")
    if not root.is_dir() or root.is_symlink():
        raise ValueError("Invalid artifact directory")
    if any((root / name).is_symlink() for name in names):
        raise ValueError("Symlinked artifact file")
    manifest = json.loads((root / names[-1]).read_text())
    if manifest.get("record_type") != "sage-architecture-helper-static-artifact-v1":
        raise ValueError("Wrong artifact record type")
    if manifest.get("functional_delivery_verified") is not False:
        raise ValueError("Unproven functional delivery")
    if manifest.get("protected_runtime") != "NOT_VERIFIED":
        raise ValueError("Unproven protected runtime")
    if manifest.get("governed_integration") != "NOT_VERIFIED":
        raise ValueError("Unproven integration")
    if set(manifest.get("files", {})) != set(names[:2]):
        raise ValueError("Unexpected file manifest")
    for name in names[:2]:
        if digest(root / name) != manifest["files"][name]:
            raise ValueError(f"Digest mismatch: {name}")
    if sum((root / name).stat().st_size for name in names) >= 750000:
        raise ValueError("Artifact too large for ConfigMap projection")
    return {"status": "PASS", "manifest_sha256": digest(root / names[-1])}


if __name__ == "__main__":
    try:
        print(json.dumps(verify(Path(sys.argv[1]))))
    except (ValueError, KeyError, IndexError, OSError) as exc:
        print(f"FAIL_CLOSED={exc}", file=sys.stderr)
        sys.exit(1)
