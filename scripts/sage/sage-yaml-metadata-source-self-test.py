#!/usr/bin/env python3
"""Test YAML metadata contracts without PyYAML or site packages."""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

from sage_yaml_metadata import (
    OpaqueTaggedValue,
    YamlMetadataError,
    load_yaml_metadata,
    require_plain_bool,
)


def test_plain_metadata_contract() -> None:
    """Validate pure metadata behavior without parsing YAML."""
    if "yaml" in sys.modules:
        raise RuntimeError("Source-only test unexpectedly loaded PyYAML")

    if require_plain_bool({"enabled": True}, "enabled") is not True:
        raise RuntimeError("Plain boolean metadata was not preserved")

    try:
        require_plain_bool({"enabled": "true"}, "enabled")
    except YamlMetadataError:
        pass
    else:
        raise RuntimeError("String boolean metadata was accepted")


def test_opaque_value_contract() -> None:
    """Validate redaction and boolean rejection for opaque tags."""
    value = OpaqueTaggedValue("!vault")
    if "vault" not in repr(value):
        raise RuntimeError("Opaque tag identity was not retained")

    try:
        bool(value)
    except TypeError:
        pass
    else:
        raise RuntimeError("Opaque tagged value allowed boolean coercion")


def test_missing_parser_is_actionable() -> None:
    """Require parsing to fail clearly when PyYAML is unavailable."""
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "metadata.yml"
        path.write_text("enabled: true\n", encoding="utf-8")
        try:
            load_yaml_metadata(path)
        except YamlMetadataError as error:
            message = str(error)
        else:
            raise RuntimeError(
                "Source-only parsing unexpectedly succeeded without PyYAML"
            )

    required = (
        "PyYAML is required",
        "repository-managed runtime",
    )
    missing = [item for item in required if item not in message]
    if missing:
        raise RuntimeError(
            f"Missing actionable parser guidance: {missing}"
        )
    if "yaml" in sys.modules:
        raise RuntimeError(
            "Failed source-only parse retained a PyYAML module"
        )


def main() -> int:
    """Run source-only YAML metadata contract tests."""
    test_plain_metadata_contract()
    test_opaque_value_contract()
    test_missing_parser_is_actionable()
    print("PASS plain YAML metadata type contract")
    print("PASS opaque tagged-value redaction contract")
    print("PASS actionable missing-PyYAML recovery")
    print("Kalaxy3 YAML metadata source-only self-test: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
