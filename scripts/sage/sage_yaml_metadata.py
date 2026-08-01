#!/usr/bin/env python3
"""Load non-secret YAML metadata while preserving tagged values as opaque."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

import yaml


class YamlMetadataError(RuntimeError):
    """Represent an invalid repository metadata document."""


class OpaqueTaggedValue:
    """Represent a YAML-tagged value that validators must not inspect."""

    __slots__ = ("tag",)

    def __init__(self, tag: str) -> None:
        """Record only the tag, never its payload."""
        self.tag = tag

    def __repr__(self) -> str:
        """Return a redacted representation."""
        return f"<opaque YAML tag {self.tag}>"

    def __bool__(self) -> bool:
        """Prevent accidental truth testing of opaque values."""
        raise TypeError(
            f"Opaque YAML value {self.tag} cannot be used as a boolean"
        )


class MetadataSafeLoader(yaml.SafeLoader):
    """Parse safe YAML while treating unknown tags as opaque metadata."""


def _construct_opaque_tag(
    loader: MetadataSafeLoader,
    tag_suffix: str,
    node: yaml.Node,
) -> OpaqueTaggedValue:
    """Discard an unknown tagged payload and retain only its tag."""
    del loader, node
    return OpaqueTaggedValue(tag_suffix)


MetadataSafeLoader.add_multi_constructor("", _construct_opaque_tag)


def load_yaml_metadata(path: Path) -> dict[str, Any]:
    """Load YAML metadata without decrypting unrelated tagged values."""
    try:
        payload = yaml.load(
            path.read_text(encoding="utf-8"),
            Loader=MetadataSafeLoader,
        )
    except yaml.YAMLError as error:
        raise YamlMetadataError(
            f"{path}: invalid YAML metadata: {error}"
        ) from error
    if not isinstance(payload, dict):
        raise YamlMetadataError(f"{path}: expected a YAML mapping")
    return payload


def require_plain_bool(
    mapping: Mapping[str, Any],
    key: str,
) -> bool:
    """Return a required untagged boolean metadata value."""
    value = mapping.get(key)
    if not isinstance(value, bool):
        raise YamlMetadataError(
            f"{key}: expected a plain boolean, found {value!r}"
        )
    return value
