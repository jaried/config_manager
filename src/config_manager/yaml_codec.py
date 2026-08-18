"""Safe YAML 1.2-compatible load, dump, and semantic comparison helpers."""

from __future__ import annotations

import datetime as dt
import math
import re
from typing import Any

import yaml
from yaml.constructor import ConstructorError
from yaml.nodes import MappingNode


_BOOL_TAG = "tag:yaml.org,2002:bool"
_FLOAT_TAG = "tag:yaml.org,2002:float"
_INT_TAG = "tag:yaml.org,2002:int"


class YamlCodecError(ValueError):
    """Raised when YAML input or output violates the supported codec contract."""


class _Yaml12SafeLoader(yaml.SafeLoader):
    """SafeLoader with YAML 1.2 scalars and explicit duplicate-key rejection."""

    def construct_mapping(self, node: yaml.Node, deep: bool = False) -> Any:
        if not isinstance(node, MappingNode):
            raise ConstructorError(
                None,
                None,
                f"expected a mapping node, but found {node.id}",
                node.start_mark,
            )

        seen_keys = set()
        for key_node, _ in node.value:
            if key_node.tag == "tag:yaml.org,2002:merge":
                continue
            key = self.construct_object(key_node, deep=False)
            if key in seen_keys:
                raise ConstructorError(
                    "while constructing a mapping",
                    node.start_mark,
                    "found duplicate explicit key",
                    key_node.start_mark,
                )
            seen_keys.add(key)
        return super().construct_mapping(node, deep=deep)


class _Yaml12SafeDumper(yaml.SafeDumper):
    """SafeDumper sharing the loader's scalar resolvers."""


_BOOL_PATTERN = re.compile(r"^(?:true|True|TRUE|false|False|FALSE)$")
_INT_PATTERN = re.compile(
    r"^(?:[-+]?0b[0-1_]+|[-+]?0o?[0-7_]+|"
    r"[-+]?[0-9_]+|[-+]?0x[0-9a-fA-F_]+)$",
    re.X,
)
_FLOAT_PATTERN = re.compile(
    r"^(?:"
    r"[-+]?(?:[0-9][0-9_]*)\.[0-9_]*(?:[eE][-+]?[0-9]+)?|"
    r"[-+]?(?:[0-9][0-9_]*)(?:[eE][-+]?[0-9]+)|"
    r"[-+]?\.[0-9_]+(?:[eE][-+][0-9]+)?|"
    r"[-+]?\.(?:inf|Inf|INF)|"
    r"\.(?:nan|NaN|NAN))$",
    re.X,
)


def _install_yaml12_resolvers(codec_class: type[Any], base_class: type[Any]) -> None:
    codec_class.yaml_implicit_resolvers = {
        key: list(resolvers)
        for key, resolvers in base_class.yaml_implicit_resolvers.items()
    }
    for first_character, resolvers in codec_class.yaml_implicit_resolvers.items():
        codec_class.yaml_implicit_resolvers[first_character] = [
            resolver
            for resolver in resolvers
            if resolver[0] not in {_BOOL_TAG, _FLOAT_TAG, _INT_TAG}
        ]
    codec_class.add_implicit_resolver(_BOOL_TAG, _BOOL_PATTERN, list("tTfF"))
    codec_class.add_implicit_resolver(_INT_TAG, _INT_PATTERN, list("-+0123456789"))
    codec_class.add_implicit_resolver(_FLOAT_TAG, _FLOAT_PATTERN, list("-+0123456789."))


def _construct_yaml12_int(loader: _Yaml12SafeLoader, node: yaml.Node) -> int:
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


_install_yaml12_resolvers(_Yaml12SafeLoader, yaml.SafeLoader)
_install_yaml12_resolvers(_Yaml12SafeDumper, yaml.SafeDumper)
_Yaml12SafeLoader.add_constructor(_INT_TAG, _construct_yaml12_int)


def validate_supported_data(data: Any, path: str = "$") -> None:
    """Reject values that cannot be represented by the frozen YAML contract."""
    if data is None or type(data) in {
        str,
        int,
        float,
        bool,
        dt.date,
        dt.datetime,
    }:
        return
    if type(data) is list:
        for index, item in enumerate(data):
            validate_supported_data(item, f"{path}[{index}]")
        return
    if type(data) is dict:
        for key, value in data.items():
            if type(key) is not str:
                raise YamlCodecError(
                    f"unsupported mapping key at {path}: {type(key).__name__}"
                )
            validate_supported_data(value, f"{path}.{key}")
        return
    raise YamlCodecError(f"unsupported YAML data at {path}: {type(data).__name__}")


def load_yaml(text: str) -> Any:
    """Load untrusted YAML using the safe YAML 1.2-compatible loader."""
    if type(text) is not str:
        raise YamlCodecError(f"YAML input must be str, got {type(text).__name__}")
    try:
        data = yaml.load(text, Loader=_Yaml12SafeLoader)
        validate_supported_data(data)
        return data
    except YamlCodecError:
        raise
    except (yaml.YAMLError, TypeError, ValueError) as error:
        raise YamlCodecError(f"YAML load failed: {type(error).__name__}") from error


def dump_yaml(data: Any) -> str:
    """Serialize supported data with safe, block-style YAML output."""
    validate_supported_data(data)
    try:
        return yaml.dump(
            data,
            Dumper=_Yaml12SafeDumper,
            allow_unicode=True,
            default_flow_style=False,
            sort_keys=False,
        )
    except (yaml.YAMLError, TypeError, ValueError) as error:
        raise YamlCodecError(f"YAML dump failed: {type(error).__name__}") from error


def semantically_equal(left: Any, right: Any) -> bool:
    """Compare supported trees using exact scalar types and ordered sequences."""
    if type(left) is not type(right):
        return False
    if type(left) is dict:
        if left.keys() != right.keys():
            return False
        return all(semantically_equal(left[key], right[key]) for key in left)
    if type(left) is list:
        return len(left) == len(right) and all(
            semantically_equal(left_item, right_item)
            for left_item, right_item in zip(left, right)
        )
    if type(left) is float and math.isnan(left) and math.isnan(right):
        return True
    return left == right
