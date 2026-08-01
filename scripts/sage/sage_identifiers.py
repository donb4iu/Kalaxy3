"""Canonical identifier allocation for Kalaxy3 SAGE registries."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, Iterable, Mapping


class IdentifierAllocationError(ValueError):
    """Raised when an identifier cannot be allocated safely."""


def normalize_date_token(value: str | date | datetime | None = None) -> str:
    """Return a validated YYYYMMDD token."""

    if value is None:
        return date.today().strftime("%Y%m%d")
    if isinstance(value, datetime):
        return value.date().strftime("%Y%m%d")
    if isinstance(value, date):
        return value.strftime("%Y%m%d")
    token = str(value)
    if len(token) != 8 or not token.isascii() or not token.isdigit():
        raise IdentifierAllocationError(
            f"Invalid date token: {token!r}"
        )
    try:
        datetime.strptime(token, "%Y%m%d")
    except ValueError as error:
        raise IdentifierAllocationError(
            f"Invalid calendar date token: {token!r}"
        ) from error
    return token


def allocate_scoped_id(
    *,
    prefix: str,
    date_token: str | date | datetime | None,
    existing_ids: Iterable[str],
    width: int = 3,
    maximum_sequence: int = 999,
) -> str:
    """Return the first unused identifier in a dated namespace.

    Allocation uses exact string membership. It does not parse identifiers
    with regular expressions and therefore cannot silently misclassify an
    escape sequence.
    """

    if not prefix or prefix.strip() != prefix:
        raise IdentifierAllocationError(
            "prefix must be non-empty and whitespace-normalized"
        )
    if width < 1:
        raise IdentifierAllocationError("width must be positive")
    if maximum_sequence < 1:
        raise IdentifierAllocationError(
            "maximum_sequence must be positive"
        )
    if maximum_sequence >= 10**width:
        raise IdentifierAllocationError(
            "maximum_sequence exceeds identifier width"
        )

    token = normalize_date_token(date_token)
    occupied = {str(value) for value in existing_ids}
    for sequence in range(1, maximum_sequence + 1):
        candidate = (
            f"{prefix}-{token}-{sequence:0{width}d}"
        )
        if candidate not in occupied:
            return candidate
    raise IdentifierAllocationError(
        f"No free identifier remains for {prefix}-{token}"
    )


def allocate_action_id(
    registry: Mapping[str, Any],
    *,
    date_token: str | date | datetime | None = None,
) -> str:
    """Allocate the next canonical SAGE improvement-action identifier."""

    actions = registry.get("actions")
    if not isinstance(actions, list):
        raise IdentifierAllocationError(
            "Improvement-action registry must contain an actions array"
        )
    identifiers: list[str] = []
    for index, item in enumerate(actions):
        if not isinstance(item, Mapping):
            raise IdentifierAllocationError(
                f"actions[{index}] must be an object"
            )
        action_id = item.get("action_id")
        if action_id is not None and not isinstance(action_id, str):
            raise IdentifierAllocationError(
                f"actions[{index}].action_id must be a string"
            )
        if isinstance(action_id, str):
            identifiers.append(action_id)

    return allocate_scoped_id(
        prefix="SAGE-ACTION",
        date_token=date_token,
        existing_ids=identifiers,
        width=3,
        maximum_sequence=999,
    )
