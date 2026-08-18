"""Validate a minimal PyYAML codec without importing project product code.

This probe compares the current ruamel.yaml YAML 1.2 scalar semantics with a
small PyYAML SafeLoader compatibility layer, then exercises the proposed
dump-validate-replace save boundary.
"""

from __future__ import annotations

import copy
import datetime as dt
import json
import math
import os
import re
import tempfile
from pathlib import Path
from typing import Any

import yaml
from ruamel.yaml import YAML
from yaml.constructor import ConstructorError
from yaml.nodes import MappingNode


BOOL_TAG = "tag:yaml.org,2002:bool"
FLOAT_TAG = "tag:yaml.org,2002:float"
INT_TAG = "tag:yaml.org,2002:int"


class Yaml12SafeLoader(yaml.SafeLoader):
    """PyYAML SafeLoader with the scalar rules used by ruamel.yaml YAML 1.2."""

    def construct_mapping(self, node: yaml.Node, deep: bool = False) -> Any:
        if not isinstance(node, MappingNode):
            raise ConstructorError(
                None,
                None,
                f"expected a mapping node, but found {node.id}",
                node.start_mark,
            )
        seen_keys: set[Any] = set()
        for key_node, _ in node.value:
            if key_node.tag == "tag:yaml.org,2002:merge":
                continue
            key = self.construct_object(key_node, deep=False)
            if key in seen_keys:
                raise ConstructorError(
                    "while constructing a mapping",
                    node.start_mark,
                    f"found duplicate key {key!r}",
                    key_node.start_mark,
                )
            seen_keys.add(key)
        return super().construct_mapping(node, deep=deep)


class Yaml12SafeDumper(yaml.SafeDumper):
    """SafeDumper using the same scalar rules so ambiguous strings are quoted."""


BOOL_PATTERN = re.compile(r"^(?:true|True|TRUE|false|False|FALSE)$")
INT_PATTERN = re.compile(
    r"^(?:[-+]?0b[0-1_]+|[-+]?0o?[0-7_]+|"
    r"[-+]?[0-9_]+|[-+]?0x[0-9a-fA-F_]+)$",
    re.X,
)
FLOAT_PATTERN = re.compile(
    r"^(?:"
    r"[-+]?(?:[0-9][0-9_]*)\.[0-9_]*(?:[eE][-+]?[0-9]+)?|"
    r"[-+]?(?:[0-9][0-9_]*)(?:[eE][-+]?[0-9]+)|"
    r"[-+]?\.[0-9_]+(?:[eE][-+][0-9]+)?|"
    r"[-+]?\.(?:inf|Inf|INF)|"
    r"\.(?:nan|NaN|NAN))$",
    re.X,
)


def install_yaml12_resolvers(codec_class: type[Any], base_class: type[Any]) -> None:
    codec_class.yaml_implicit_resolvers = {
        key: list(resolvers)
        for key, resolvers in base_class.yaml_implicit_resolvers.items()
    }
    for first_character, resolvers in codec_class.yaml_implicit_resolvers.items():
        codec_class.yaml_implicit_resolvers[first_character] = [
            resolver
            for resolver in resolvers
            if resolver[0] not in {BOOL_TAG, FLOAT_TAG, INT_TAG}
        ]
    codec_class.add_implicit_resolver(BOOL_TAG, BOOL_PATTERN, list("tTfF"))
    codec_class.add_implicit_resolver(INT_TAG, INT_PATTERN, list("-+0123456789"))
    codec_class.add_implicit_resolver(
        FLOAT_TAG,
        FLOAT_PATTERN,
        list("-+0123456789."),
    )


install_yaml12_resolvers(Yaml12SafeLoader, yaml.SafeLoader)
install_yaml12_resolvers(Yaml12SafeDumper, yaml.SafeDumper)


def construct_yaml12_int(loader: Yaml12SafeLoader, node: yaml.Node) -> int:
    value = loader.construct_scalar(node).replace("_", "")
    sign = -1 if value.startswith("-") else 1
    unsigned = value[1:] if value[:1] in "+-" else value
    if unsigned.startswith("0b"):
        return sign * int(unsigned[2:], 2)
    if unsigned.startswith("0o"):
        return sign * int(unsigned[2:], 8)
    if unsigned.startswith("0x"):
        return sign * int(unsigned[2:], 16)
    return sign * int(unsigned, 10)


Yaml12SafeLoader.add_constructor(INT_TAG, construct_yaml12_int)


def load_candidate(text: str) -> Any:
    return yaml.load(text, Loader=Yaml12SafeLoader)


def validate_supported_data(data: Any, path: str = "$root") -> None:
    if data is None or type(data) in {str, int, float, bool, dt.date, dt.datetime}:
        return
    if type(data) is list:
        for index, item in enumerate(data):
            validate_supported_data(item, f"{path}[{index}]")
        return
    if type(data) is dict:
        for key, value in data.items():
            if type(key) is not str:
                raise TypeError(f"unsupported mapping key at {path}: {type(key).__name__}")
            validate_supported_data(value, f"{path}.{key}")
        return
    raise TypeError(f"unsupported YAML data at {path}: {type(data).__name__}")


def dump_candidate(data: Any) -> str:
    validate_supported_data(data)
    return yaml.dump(
        data,
        Dumper=Yaml12SafeDumper,
        allow_unicode=True,
        default_flow_style=False,
        sort_keys=False,
    )


def describe(value: Any) -> dict[str, Any]:
    return {"type": type(value).__name__, "value": repr(value)}


def scalar_equal(actual: Any, expected: Any) -> bool:
    if type(actual) is not type(expected):
        return False
    if type(actual) is float and math.isnan(actual) and math.isnan(expected):
        return True
    return actual == expected


def assert_semantically_equal(actual: Any, expected: Any) -> None:
    assert type(actual) is type(expected), (type(actual), type(expected))
    if isinstance(expected, dict):
        assert actual.keys() == expected.keys(), (actual, expected)
        assert list(actual) == list(expected)
        for key in expected:
            assert_semantically_equal(actual[key], expected[key])
    elif isinstance(expected, list):
        assert len(actual) == len(expected)
        for actual_item, expected_item in zip(actual, expected, strict=True):
            assert_semantically_equal(actual_item, expected_item)
    else:
        assert scalar_equal(actual, expected), (actual, expected)


def validate_scalar_compatibility() -> dict[str, Any]:
    scalar_texts = [
        "yes", "no", "on", "off", "true", "false", "TRUE", "False",
        "0123", "077", "0o17", "0x10", "0b10", "+12", "-0", "1_000",
        "1e3", "1E+3", "1.25", ".5", ".5e+3", ".5e3", ".inf", ".NaN",
        "null", "~", "2026-08-18", "1:20", "1:20:30", "plain-text",
    ]
    reference_yaml = YAML(typ="safe")
    rows = []
    baseline_mismatches = []
    candidate_mismatches = []
    for scalar_text in scalar_texts:
        document = f"value: {scalar_text}\n"
        reference = reference_yaml.load(document)["value"]
        baseline = yaml.safe_load(document)["value"]
        candidate = load_candidate(document)["value"]
        row = {
            "source": scalar_text,
            "ruamel": describe(reference),
            "pyyaml_safe": describe(baseline),
            "candidate": describe(candidate),
        }
        rows.append(row)
        if not scalar_equal(baseline, reference):
            baseline_mismatches.append(scalar_text)
        if not scalar_equal(candidate, reference):
            candidate_mismatches.append(scalar_text)
    assert baseline_mismatches, "The probe must expose the unsafe drop-in replacement."
    assert not candidate_mismatches, candidate_mismatches
    return {
        "baseline_mismatches": baseline_mismatches,
        "candidate_mismatches": candidate_mismatches,
        "rows": rows,
    }


def validate_round_trip() -> dict[str, Any]:
    original = {
        "中文": "配置",
        "ambiguous_strings": ["yes", "no", "on", "off", "0123", "1e3"],
        "booleans": [True, False],
        "numbers": [0, 123, 1.25, 1000.0],
        "none": None,
        "date": dt.date(2026, 8, 18),
        "datetime": dt.datetime(2026, 8, 18, 9, 30, 45),
        "nested": {"items": ["alpha", {"beta": 2}]},
    }
    dumped = dump_candidate(original)
    reloaded = load_candidate(dumped)
    assert_semantically_equal(reloaded, original)
    assert "\n- " in dumped or "\n  - " in dumped
    assert "key:   -" not in dumped
    return {"dumped": dumped, "top_level_order": list(reloaded)}


def validate_allowed_normalization() -> dict[str, Any]:
    source = (
        "# leading comment\n"
        "defaults: &defaults\n"
        "  label: 'yes'  # inline comment\n"
        "copy: *defaults\n"
        "items: [one, two]\n"
    )
    loaded = load_candidate(source)
    dumped = dump_candidate(loaded)
    reloaded = load_candidate(dumped)
    assert_semantically_equal(reloaded, loaded)
    assert "# leading comment" not in dumped
    assert "# inline comment" not in dumped
    return {"source": source, "dumped": dumped}


def validate_safe_tag_rejection() -> dict[str, Any]:
    unsafe_document = "value: !!python/object/apply:os.system ['echo unsafe']\n"
    rejected = False
    error_type = None
    try:
        load_candidate(unsafe_document)
    except yaml.YAMLError as error:
        rejected = True
        error_type = type(error).__name__
    assert rejected
    return {"rejected": rejected, "error_type": error_type}


def validate_duplicate_key_rejection() -> dict[str, Any]:
    duplicate_document = "value: 1\nvalue: 2\n"
    reference_yaml = YAML(typ="safe")
    reference_rejected = False
    try:
        reference_yaml.load(duplicate_document)
    except Exception:
        reference_rejected = True
    baseline_result = yaml.safe_load(duplicate_document)
    candidate_rejected = False
    candidate_error_type = None
    try:
        load_candidate(duplicate_document)
    except yaml.YAMLError as error:
        candidate_rejected = True
        candidate_error_type = type(error).__name__
    assert reference_rejected
    assert baseline_result == {"value": 2}
    assert candidate_rejected
    return {
        "ruamel_rejected": reference_rejected,
        "pyyaml_safe_result": baseline_result,
        "candidate_rejected": candidate_rejected,
        "candidate_error_type": candidate_error_type,
    }


def validate_supported_type_boundary() -> dict[str, Any]:
    rejected_types = []
    for value in [{"value": (1, 2)}, {"value": {1, 2}}, {1: "value"}]:
        try:
            dump_candidate(value)
        except TypeError:
            rejected_types.append(type(next(iter(value.values()), next(iter(value)))).__name__)
    assert len(rejected_types) == 3
    return {"rejected_case_count": len(rejected_types)}


def atomic_write(target: Path, data: Any) -> None:
    candidate_path = target.with_name(f"{target.name}.tmp")
    try:
        with candidate_path.open("w", encoding="utf-8", newline="\n") as stream:
            stream.write(dump_candidate(data))
            stream.flush()
            os.fsync(stream.fileno())
        candidate = load_candidate(candidate_path.read_text(encoding="utf-8"))
        assert_semantically_equal(candidate, data)
        os.replace(candidate_path, target)
    finally:
        if candidate_path.exists():
            candidate_path.unlink()


def validate_atomic_boundary() -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="s1_03_pyyaml_") as temp_dir:
        target = Path(temp_dir) / "config.yaml"
        original_bytes = b"sentinel: unchanged\n"
        target.write_bytes(original_bytes)

        failure = None
        try:
            atomic_write(target, {"unsupported": object()})
        except (yaml.YAMLError, TypeError, AssertionError) as error:
            failure = type(error).__name__
        assert failure is not None
        assert target.read_bytes() == original_bytes

        replacement = {"items": ["one", "two"], "enabled": True}
        atomic_write(target, replacement)
        reloaded = load_candidate(target.read_text(encoding="utf-8"))
        assert_semantically_equal(reloaded, replacement)
        return {
            "failure_type": failure,
            "unchanged_after_failure": True,
            "successful_replacement": reloaded,
        }


def validate_raw_and_standard_projection() -> dict[str, Any]:
    raw = {"app": "demo", "items": ["one", "two"]}
    standard = {"__data__": copy.deepcopy(raw), "__type_hints__": {}}
    assert_semantically_equal(load_candidate(dump_candidate(raw)), raw)
    assert_semantically_equal(load_candidate(dump_candidate(standard)), standard)
    return {
        "raw_root_keys": list(raw),
        "standard_root_keys": list(standard),
    }


def main() -> None:
    results = {
        "runtime": {
            "pyyaml": yaml.__version__,
            "python": os.sys.version.split()[0],
        },
        "TV-PYAML-01-scalar-compatibility": validate_scalar_compatibility(),
        "TV-PYAML-02-round-trip": validate_round_trip(),
        "TV-PYAML-03-allowed-normalization": validate_allowed_normalization(),
        "TV-PYAML-04-safe-tag-rejection": validate_safe_tag_rejection(),
        "TV-PYAML-05-duplicate-key-rejection": validate_duplicate_key_rejection(),
        "TV-PYAML-06-supported-type-boundary": validate_supported_type_boundary(),
        "TV-PYAML-07-atomic-boundary": validate_atomic_boundary(),
        "TV-PYAML-08-envelope-round-trip": validate_raw_and_standard_projection(),
    }
    print(json.dumps(results, ensure_ascii=False, indent=2, default=str))


if __name__ == "__main__":
    main()
