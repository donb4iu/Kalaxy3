#!/usr/bin/env python3
"""Test vault-tolerant repository YAML metadata loading."""

from __future__ import annotations

import tempfile
from pathlib import Path

from sage_yaml_metadata import (
    OpaqueTaggedValue,
    load_yaml_metadata,
    require_plain_bool,
)

SAMPLE = """\
deploy_feature: true
ordinary_value: example
encrypted_value: !vault |
  $ANSIBLE_VAULT;1.1;AES256
  616263646566
nested_tag: !custom
  child: hidden
"""


def main() -> int:
    """Exercise ordinary, encrypted, and unknown-tag paths."""
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "metadata.yml"
        path.write_text(SAMPLE, encoding="utf-8")
        payload = load_yaml_metadata(path)

    if require_plain_bool(payload, "deploy_feature") is not True:
        raise RuntimeError("Plain deployment gate was not preserved")
    if payload.get("ordinary_value") != "example":
        raise RuntimeError("Ordinary YAML metadata was not preserved")

    encrypted = payload.get("encrypted_value")
    nested = payload.get("nested_tag")
    if not isinstance(encrypted, OpaqueTaggedValue):
        raise RuntimeError("Vault value was not made opaque")
    if not isinstance(nested, OpaqueTaggedValue):
        raise RuntimeError("Unknown mapping tag was not made opaque")
    if "616263646566" in repr(encrypted):
        raise RuntimeError("Encrypted payload leaked through representation")

    try:
        bool(encrypted)
    except TypeError:
        pass
    else:
        raise RuntimeError("Opaque tagged value allowed boolean coercion")

    print("PASS ordinary YAML metadata")
    print("PASS vault and unknown tags remain opaque")
    print("PASS opaque values reject boolean coercion")
    print("Kalaxy3 SAGE YAML metadata self-test: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
