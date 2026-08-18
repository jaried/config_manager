"""S1-03 frozen tests for the safe YAML 1.2 codec contract."""

from __future__ import annotations

import datetime as dt
import importlib
import math

import pytest


@pytest.fixture
def yaml_codec():
    """Load the package codec at test time so the red state still collects."""
    return importlib.import_module("config_manager.yaml_codec")


@pytest.mark.parametrize(
    ("scalar_text", "expected_type", "expected_value"),
    [
        ("yes", str, "yes"),
        ("no", str, "no"),
        ("on", str, "on"),
        ("off", str, "off"),
        ("true", bool, True),
        ("false", bool, False),
        ("TRUE", bool, True),
        ("False", bool, False),
        ("0123", int, 123),
        ("077", int, 77),
        ("0o17", int, 15),
        ("0x10", int, 16),
        ("0b10", int, 2),
        ("+12", int, 12),
        ("-0", int, 0),
        ("1_000", int, 1000),
        ("1e3", float, 1000.0),
        ("1E+3", float, 1000.0),
        ("1.25", float, 1.25),
        (".5", float, 0.5),
        (".5e+3", float, 500.0),
        (".5e3", str, ".5e3"),
        (".inf", float, math.inf),
        (".NaN", float, math.nan),
        ("null", type(None), None),
        ("~", type(None), None),
        ("2026-08-18", dt.date, dt.date(2026, 8, 18)),
        ("1:20", str, "1:20"),
        ("1:20:30", str, "1:20:30"),
        ("plain-text", str, "plain-text"),
    ],
)
def test_s1_03_yaml_12_scalar_resolver(
    yaml_codec, scalar_text, expected_type, expected_value, tmp_path
):
    """YAML 1.2 scalars use the approved exact type/value mapping."""
    loaded = yaml_codec.load_yaml(f"value: {scalar_text}\n")

    actual = loaded["value"]
    assert type(actual) is expected_type
    if expected_type is float and math.isnan(expected_value):
        assert math.isnan(actual)
    else:
        assert actual == expected_value
    assert tmp_path.exists()


def test_s1_03_codec_round_trip_preserves_sequence_and_supported_scalars(
    yaml_codec, tmp_path
):
    """Supported nested data round-trips through one codec without type drift."""
    data = {
        "stock": [
            {"code": "600519", "weight": 0.5},
            {"code": "AAPL", "enabled": True},
        ],
        "category_subscription_order": ["stock", "future", "option"],
        "date": dt.date(2026, 8, 18),
        "datetime": dt.datetime(2026, 8, 18, 12, 30, 45),
        "none": None,
        "nan": math.nan,
        "positive_inf": math.inf,
        "negative_inf": -math.inf,
    }

    encoded = yaml_codec.dump_yaml(data)
    decoded = yaml_codec.load_yaml(encoded)

    assert yaml_codec.semantically_equal(decoded, data)
    assert [item["code"] for item in decoded["stock"]] == ["600519", "AAPL"]
    assert decoded["category_subscription_order"] == ["stock", "future", "option"]
    assert tmp_path.exists()


def test_s1_03_dump_quotes_ambiguous_strings_before_reload(yaml_codec, tmp_path):
    """Strings that resemble YAML 1.2 scalars remain strings after dump/load."""
    data = {
        "yes": "yes",
        "octal_like": "0123",
        "scientific_like": "1e3",
        "leading_dot_exponent": ".5e3",
        "clock_like": "1:20",
        "plain": "plain-text",
    }

    decoded = yaml_codec.load_yaml(yaml_codec.dump_yaml(data))

    assert decoded == data
    assert all(type(decoded[key]) is str for key in data)
    assert tmp_path.exists()


@pytest.mark.parametrize(
    ("left", "right", "expected"),
    [
        ({"a": 1, "b": 2}, {"b": 2, "a": 1}, True),
        (["first", "second"], ["second", "first"], False),
        (1, True, False),
        (dt.date(2026, 8, 18), dt.datetime(2026, 8, 18), False),
        (float("nan"), float("nan"), True),
        (float("inf"), float("inf"), True),
        (float("inf"), float("-inf"), False),
        ({"nested": [1, {"ok": True}]}, {"nested": [1, {"ok": True}]}, True),
    ],
)
def test_s1_03_semantically_equal_uses_exact_types_and_values(
    yaml_codec, left, right, expected, tmp_path
):
    assert yaml_codec.semantically_equal(left, right) is expected
    assert tmp_path.exists()


@pytest.mark.parametrize(
    "yaml_text",
    [
        "value: !!python/object/apply:os.system ['echo unsafe']\n",
        "value: !!python/name:os.system\n",
    ],
)
def test_s1_03_safe_loader_rejects_python_tags_without_execution(
    yaml_codec, yaml_text, tmp_path
):
    sentinel = tmp_path / "unsafe-was-executed"
    unsafe_text = yaml_text.replace("echo unsafe", f"echo > {sentinel}")

    with pytest.raises(yaml_codec.YamlCodecError):
        yaml_codec.load_yaml(unsafe_text)

    assert not sentinel.exists()


def test_s1_03_loader_rejects_duplicate_explicit_mapping_keys(yaml_codec, tmp_path):
    duplicate = "items:\n  first: 1\n  first: 2\n"

    with pytest.raises(yaml_codec.YamlCodecError):
        yaml_codec.load_yaml(duplicate)

    assert tmp_path.exists()


def test_s1_03_loader_keeps_safe_merge_semantics_but_rejects_explicit_duplicates(
    yaml_codec, tmp_path
):
    merged = """
defaults: &defaults
  stock: [600519]
  enabled: true
config:
  <<: *defaults
  label: demo
"""
    loaded = yaml_codec.load_yaml(merged)
    assert loaded["config"] == {
        "stock": [600519],
        "enabled": True,
        "label": "demo",
    }

    explicit_duplicate = """
defaults: &defaults
  stock: [600519]
config:
  <<: *defaults
  stock: [A]
  stock: [B]
"""
    with pytest.raises(yaml_codec.YamlCodecError):
        yaml_codec.load_yaml(explicit_duplicate)
    assert tmp_path.exists()


class _UnsupportedS103:
    pass


@pytest.mark.parametrize(
    "unsupported",
    [
        (1, 2),
        {"a", "b"},
        b"bytes",
        _UnsupportedS103(),
        {1: "non-string-key"},
        {"outer": [{"inner": (1,)}]},
    ],
)
def test_s1_03_dump_rejects_unsupported_data_tree(yaml_codec, unsupported, tmp_path):
    with pytest.raises(yaml_codec.YamlCodecError) as exc_info:
        yaml_codec.dump_yaml(unsupported)

    message = str(exc_info.value)
    assert "$" in message
    assert any(
        token in message
        for token in ("tuple", "set", "bytes", "_UnsupportedS103", "int")
    )
    assert tmp_path.exists()


def test_s1_03_validate_supported_data_accepts_declared_tree(yaml_codec, tmp_path):
    declared = {
        "list": [None, False, 0, 1.5, dt.date(2026, 8, 18)],
        "nested": {"value": "ok"},
    }

    assert yaml_codec.validate_supported_data(declared) is None
    assert tmp_path.exists()


def test_s1_03_validate_supported_data_reports_stable_nested_path(yaml_codec, tmp_path):
    invalid = {"outer": [{"inner": {"bad"}}]}

    with pytest.raises(yaml_codec.YamlCodecError) as exc_info:
        yaml_codec.validate_supported_data(invalid)

    message = str(exc_info.value)
    assert "$.outer[0].inner" in message
    assert "set" in message
    assert tmp_path.exists()
