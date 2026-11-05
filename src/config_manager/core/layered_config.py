"""Pure data operations for the read-only base and writable overlay layers."""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from typing import Any


def merge_layers(base: Mapping[str, Any], overlay: Mapping[str, Any]) -> dict[str, Any]:
    """Return a recursively merged snapshot without modifying either input.

    Mappings at the same path are merged recursively.  Every other overlay
    value, including sequences and scalars, replaces the base value as a
    whole.
    """

    merged = _copy_mapping(base)
    for key, value in overlay.items():
        base_value = merged.get(key)
        if isinstance(base_value, Mapping) and isinstance(value, Mapping):
            merged[key] = merge_layers(base_value, value)
        else:
            merged[key] = deepcopy(value)
    return merged


def diff_from_base(merged: Mapping[str, Any], base: Mapping[str, Any]) -> dict[str, Any]:
    """Return the writable overlay values that differ from ``base``.

    Missing keys in ``base`` are retained.  Equal values and empty recursive
    mappings are omitted.  Deletion markers are intentionally not generated;
    the approved layered format has no tombstone protocol.
    """

    diff: dict[str, Any] = {}
    for key, value in merged.items():
        if key not in base:
            diff[key] = deepcopy(value)
            continue

        base_value = base[key]
        if isinstance(value, Mapping) and isinstance(base_value, Mapping):
            nested = diff_from_base(value, base_value)
            if nested:
                diff[key] = nested
        elif value != base_value:
            diff[key] = deepcopy(value)
    return diff


def _copy_mapping(value: Mapping[str, Any]) -> dict[str, Any]:
    """Deep-copy a mapping into an ordinary dictionary."""

    return {key: deepcopy(item) for key, item in value.items()}
