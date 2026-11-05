from __future__ import annotations

from pathlib import Path

import pytest

from config_manager.core.layered_config import diff_from_base, merge_layers
from config_manager.config_manager import ConfigManager, get_config_manager
from config_manager.yaml_codec import dump_yaml, load_yaml


def test_merge_layers_recursively_merges_mappings_and_replaces_sequences():
    base = {"scalar": "base", "nested": {"keep": 1, "override": "base"}, "items": [1]}
    overlay = {"scalar": "overlay", "nested": {"override": "overlay", "new": True}, "items": [2]}

    assert merge_layers(base, overlay) == {
        "scalar": "overlay",
        "nested": {"keep": 1, "override": "overlay", "new": True},
        "items": [2],
    }


def test_merge_layers_does_not_modify_nested_inputs():
    base = {"nested": {"value": [1]}}
    overlay = {"nested": {"value": [2]}}

    result = merge_layers(base, overlay)
    result["nested"]["value"].append(3)

    assert base == {"nested": {"value": [1]}}
    assert overlay == {"nested": {"value": [2]}}


def test_diff_from_base_omits_equal_and_empty_nested_values():
    base = {"same": 1, "nested": {"same": "x", "base_only": True}, "items": [1]}
    merged = {"same": 1, "nested": {"same": "x"}, "items": [2], "new": {"value": 3}}

    assert diff_from_base(merged, base) == {"items": [2], "new": {"value": 3}}


def test_diff_from_base_returns_independent_values():
    base = {"nested": {"value": 1}}
    merged = {"nested": {"value": 2}}

    result = diff_from_base(merged, base)
    result["nested"]["value"] = 3

    assert merged == {"nested": {"value": 2}}


def _write_yaml(path: Path, data: dict) -> bytes:
    encoded = dump_yaml(data).encode("utf-8")
    path.write_bytes(encoded)
    return encoded


@pytest.fixture(autouse=True)
def clear_config_manager_cache():
    ConfigManager._production_instances.clear()
    ConfigManager._instances.clear()
    yield
    for instance in list(ConfigManager._production_instances.values()):
        instance.cleanup()
    for instance in list(ConfigManager._instances.values()):
        instance.cleanup()
    ConfigManager._production_instances.clear()
    ConfigManager._instances.clear()


def test_public_factory_merges_standard_base_and_overlay_and_hints(tmp_path: Path):
    base_path = tmp_path / "base.yaml"
    overlay_path = tmp_path / "overlay.yaml"
    _write_yaml(
        base_path,
        {
            "__data__": {"shared": "base", "nested": {"base": 1}},
            "__type_hints__": {"shared": "str", "nested.base": "int"},
        },
    )
    _write_yaml(
        overlay_path,
        {
            "__data__": {"nested": {"overlay": 2}},
            "__type_hints__": {"nested.overlay": "int"},
        },
    )

    config = get_config_manager(
        str(overlay_path), watch=False, base_config_path=str(base_path)
    )

    assert config is not None
    assert config.get("shared") == "base"
    assert config.get("nested.base") == 1
    assert config.get("nested.overlay") == 2
    serializable = config.get_serializable_data()
    assert serializable.get("shared") == "base"
    assert serializable.get_type_hint("nested.base") == "int"
    assert serializable.get_type_hint("nested.overlay") == "int"


def test_all_save_payloads_write_overlay_diff_and_preserve_base(tmp_path: Path):
    base_path = tmp_path / "base.yaml"
    overlay_path = tmp_path / "overlay.yaml"
    _write_yaml(
        base_path,
        {
            "__data__": {"shared": "base", "nested": {"base": 1}},
            "__type_hints__": {"shared": "str", "nested.base": "int"},
        },
    )
    _write_yaml(
        overlay_path,
        {
            "__data__": {"nested": {"overlay": 2}},
            "__type_hints__": {"nested.overlay": "int"},
        },
    )
    base_before = base_path.read_bytes()

    config = get_config_manager(
        str(overlay_path), watch=False, base_config_path=str(base_path)
    )
    assert config is not None
    config.set("nested.base", 3, autosave=False)
    assert config.save()

    payload = load_yaml(overlay_path.read_text(encoding="utf-8"))
    assert payload["__data__"]["nested"] == {"base": 3, "overlay": 2}
    assert "shared" not in payload["__data__"]
    assert payload["__type_hints__"]["nested.base"] == "int"
    assert payload["__type_hints__"]["nested.overlay"] == "int"
    assert "shared" not in payload["__type_hints__"]
    assert base_path.read_bytes() == base_before


@pytest.mark.parametrize("overlay_exists", [False, True])
@pytest.mark.parametrize("auto_create", [False, True])
def test_missing_base_fails_closed_without_touching_overlay(
    tmp_path: Path, overlay_exists: bool, auto_create: bool
):
    base_path = tmp_path / "missing-base.yaml"
    overlay_path = tmp_path / "overlay.yaml"
    original = b"value: keep\n"
    if overlay_exists:
        overlay_path.write_bytes(original)

    config = get_config_manager(
        str(overlay_path),
        watch=False,
        auto_create=auto_create,
        base_config_path=str(base_path),
    )

    assert config is None
    assert not base_path.exists()
    if overlay_exists:
        assert overlay_path.read_bytes() == original
    else:
        assert not overlay_path.exists()


def test_base_requires_watch_false_and_cache_identity_includes_base(tmp_path: Path):
    base_a = tmp_path / "base-a.yaml"
    base_b = tmp_path / "base-b.yaml"
    overlay = tmp_path / "overlay.yaml"
    _write_yaml(base_a, {"value": "a"})
    _write_yaml(base_b, {"value": "b"})
    _write_yaml(overlay, {"override": "overlay"})

    with pytest.raises(ValueError, match="base_config_path requires watch=False"):
        get_config_manager(str(overlay), watch=True, base_config_path=str(base_a))

    config_a = get_config_manager(
        str(overlay), watch=False, base_config_path=str(base_a)
    )
    config_b = get_config_manager(
        str(overlay), watch=False, base_config_path=str(base_b)
    )
    config_a_again = get_config_manager(
        str(overlay), watch=False, base_config_path=str(base_a)
    )

    assert config_a is not None and config_b is not None
    assert config_a is config_a_again
    assert config_a is not config_b
    assert config_a.get("value") == "a"
    assert config_b.get("value") == "b"


def test_reload_reads_new_base_value_while_overlay_remains_authoritative(tmp_path: Path):
    base_path = tmp_path / "base.yaml"
    overlay_path = tmp_path / "overlay.yaml"
    _write_yaml(base_path, {"value": "before", "base_only": True})
    _write_yaml(overlay_path, {"value": "overlay"})

    config = get_config_manager(
        str(overlay_path), watch=False, base_config_path=str(base_path)
    )
    assert config is not None
    assert config.get("value") == "overlay"

    _write_yaml(base_path, {"value": "after", "base_only": False})
    assert config.reload()
    assert config.get("value") == "overlay"
    assert config.get("base_only") is False
