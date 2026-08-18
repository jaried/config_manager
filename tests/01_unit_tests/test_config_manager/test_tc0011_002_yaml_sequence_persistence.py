"""S1-03 frozen tests for sequence persistence and save transaction safety."""

from __future__ import annotations

import importlib
from pathlib import Path

import pytest


@pytest.fixture
def yaml_codec():
    """Load the codec at test time so missing production code remains a red test."""
    return importlib.import_module("config_manager.yaml_codec")


@pytest.fixture
def file_operations():
    module = importlib.import_module("config_manager.core.file_operations")
    return module, module.FileOperations()


def _patch_codec_boundary(
    monkeypatch, codec_module, file_operations_module, name, value
):
    monkeypatch.setattr(codec_module, name, value)
    monkeypatch.setattr(file_operations_module, name, value, raising=False)


def _candidate_paths(target: Path) -> list[Path]:
    return list(target.parent.glob(f".{target.name}.*.tmp"))


def _clear_config_instances() -> None:
    module = importlib.import_module("config_manager.config_manager")
    module._clear_instances_for_testing()


def test_s1_03_file_operations_saves_sequence_and_reloads_semantically(
    yaml_codec, file_operations, tmp_path
):
    file_operations_module, operations = file_operations
    target = tmp_path / "sequence.yaml"
    data = {
        "stock": [
            {"symbol": "600519", "enabled": True},
            {"symbol": "AAPL", "enabled": False},
        ],
        "category_subscription_order": ["stock", "future", "option"],
    }

    assert operations.save_config(str(target), data) is True
    reloaded = yaml_codec.load_yaml(target.read_text(encoding="utf-8"))

    assert yaml_codec.semantically_equal(reloaded, data)
    assert reloaded["stock"][0]["symbol"] == "600519"
    assert reloaded["category_subscription_order"] == ["stock", "future", "option"]
    assert _candidate_paths(target) == []
    assert file_operations_module is not None


@pytest.mark.parametrize("method_name", ["save_config", "save_config_only"])
def test_s1_03_dump_failure_preserves_existing_target_and_cleans_candidate(
    yaml_codec, file_operations, method_name, monkeypatch, tmp_path
):
    file_operations_module, operations = file_operations
    target = tmp_path / f"{method_name}.yaml"
    old_bytes = b"old-target-bytes\n"
    target.write_bytes(old_bytes)

    def fail_dump(data):
        raise yaml_codec.YamlCodecError("dump rejected at $")

    _patch_codec_boundary(
        monkeypatch, yaml_codec, file_operations_module, "dump_yaml", fail_dump
    )
    save = getattr(operations, method_name)

    result = save(str(target), {"stock": ["new"]})

    assert result is False
    assert target.read_bytes() == old_bytes
    assert _candidate_paths(target) == []


def test_s1_03_reload_failure_preserves_existing_target_and_cleans_candidate(
    yaml_codec, file_operations, monkeypatch, tmp_path
):
    file_operations_module, operations = file_operations
    target = tmp_path / "reload-failure.yaml"
    old_bytes = b"old-target-bytes\n"
    target.write_bytes(old_bytes)

    def fail_load(text):
        raise yaml_codec.YamlCodecError("candidate reload rejected at $")

    _patch_codec_boundary(
        monkeypatch, yaml_codec, file_operations_module, "load_yaml", fail_load
    )

    assert operations.save_config_only(str(target), {"stock": ["new"]}) is False
    assert target.read_bytes() == old_bytes
    assert _candidate_paths(target) == []


def test_s1_03_semantic_compare_failure_preserves_existing_target_and_cleans_candidate(
    yaml_codec, file_operations, monkeypatch, tmp_path
):
    file_operations_module, operations = file_operations
    target = tmp_path / "compare-failure.yaml"
    old_bytes = b"old-target-bytes\n"
    target.write_bytes(old_bytes)

    _patch_codec_boundary(
        monkeypatch,
        yaml_codec,
        file_operations_module,
        "semantically_equal",
        lambda left, right: False,
    )

    assert operations.save_config_only(str(target), {"stock": ["new"]}) is False
    assert target.read_bytes() == old_bytes
    assert _candidate_paths(target) == []


def test_s1_03_replace_failure_preserves_existing_target_and_cleans_candidate(
    yaml_codec, file_operations, monkeypatch, tmp_path
):
    file_operations_module, operations = file_operations
    target = tmp_path / "replace-failure.yaml"
    old_bytes = b"old-target-bytes\n"
    target.write_bytes(old_bytes)
    real_replace = file_operations_module.os.replace

    def fail_replace(source, destination):
        raise OSError(f"replace blocked for {destination}")

    monkeypatch.setattr(file_operations_module.os, "replace", fail_replace)

    assert operations.save_config_only(str(target), {"stock": ["new"]}) is False
    assert target.read_bytes() == old_bytes
    assert _candidate_paths(target) == []
    monkeypatch.setattr(file_operations_module.os, "replace", real_replace)


def test_s1_03_failed_save_keeps_absent_target_absent_and_cleans_candidate(
    yaml_codec, file_operations, monkeypatch, tmp_path
):
    file_operations_module, operations = file_operations
    target = tmp_path / "never-created.yaml"

    def fail_load(text):
        raise yaml_codec.YamlCodecError("candidate reload rejected at $")

    _patch_codec_boundary(
        monkeypatch, yaml_codec, file_operations_module, "load_yaml", fail_load
    )

    assert operations.save_config_only(str(target), {"stock": ["new"]}) is False
    assert not target.exists()
    assert _candidate_paths(target) == []


def test_s1_03_backup_failure_does_not_reverse_committed_main_target(
    yaml_codec, file_operations, monkeypatch, tmp_path
):
    file_operations_module, operations = file_operations
    target = tmp_path / "main.yaml"
    backup = tmp_path / "backup.yaml"
    data = {"stock": ["600519"], "enabled": True}
    real_replace = file_operations_module.os.replace

    def fail_backup_replace(source, destination):
        if Path(destination) == backup:
            raise OSError("backup destination unavailable")
        return real_replace(source, destination)

    monkeypatch.setattr(file_operations_module.os, "replace", fail_backup_replace)

    assert operations.save_config(str(target), data, backup_path=str(backup)) is True
    assert yaml_codec.semantically_equal(
        yaml_codec.load_yaml(target.read_text(encoding="utf-8")), data
    )
    assert not backup.exists()
    assert _candidate_paths(target) == []
    assert _candidate_paths(backup) == []


def test_s1_03_create_backup_only_has_independent_candidate_boundary(
    yaml_codec, file_operations, tmp_path
):
    _, operations = file_operations
    backup = tmp_path / "isolated-backup.yaml"
    data = {"stock": ["600519"], "category_subscription_order": ["stock"]}

    assert operations.create_backup_only(str(backup), data) is True
    assert yaml_codec.semantically_equal(
        yaml_codec.load_yaml(backup.read_text(encoding="utf-8")), data
    )
    assert _candidate_paths(backup) == []


def test_s1_03_create_backup_only_rejects_unsupported_data_without_target(
    yaml_codec, file_operations, tmp_path
):
    _, operations = file_operations
    backup = tmp_path / "invalid-backup.yaml"

    assert operations.create_backup_only(str(backup), {"bad": object()}) is False
    assert not backup.exists()
    assert _candidate_paths(backup) == []


def test_s1_03_e2e_standard_sequence_persistence(yaml_codec, tmp_path):
    config_path = tmp_path / "standard.yaml"
    config_path.write_text(
        """__data__:
  stock:
    # The sequence must remain valid when this comment is present.
    - symbol: 600519
      enabled: true
    - symbol: AAPL
      enabled: false
  category_subscription_order:
    - stock
    - future
__type_hints__: {}
""",
        encoding="utf-8",
    )
    updated_stock = [
        {"symbol": "600519", "enabled": True},
        {"symbol": "AAPL", "enabled": False},
        {"symbol": "IF", "enabled": True},
    ]
    config = None
    reloaded = None
    try:
        _clear_config_instances()
        manager_module = importlib.import_module("config_manager")
        config = manager_module.get_config_manager(
            config_path=str(config_path), watch=False, test_mode=False
        )
        config.set("stock", updated_stock, autosave=False)
        assert config.save() is True
        target = Path(config.get_config_file_path())
        assert yaml_codec.semantically_equal(
            yaml_codec.load_yaml(target.read_text(encoding="utf-8"))["__data__"][
                "stock"
            ],
            updated_stock,
        )
        config.cleanup()
        config = None
        _clear_config_instances()
        reloaded = manager_module.get_config_manager(
            config_path=str(target), watch=False, test_mode=False
        )
        assert reloaded.get("stock") == updated_stock
        assert reloaded.get("category_subscription_order") == ["stock", "future"]
    finally:
        if reloaded is not None:
            reloaded.cleanup()
        if config is not None:
            config.cleanup()
        _clear_config_instances()


def test_s1_03_e2e_raw_save_promotes_to_standard_envelope(yaml_codec, tmp_path):
    raw_paths = [tmp_path / "raw_non_test.yaml", tmp_path / "raw_test.yaml"]
    manager_module = importlib.import_module("config_manager")
    for test_mode, config_path in zip((False, True), raw_paths, strict=True):
        config_path.write_text(
            """stock:
  - symbol: 600519
    enabled: true
category_subscription_order:
  - stock
  - future
""",
            encoding="utf-8",
        )
        config = None
        reloaded = None
        try:
            _clear_config_instances()
            config = manager_module.get_config_manager(
                config_path=str(config_path), watch=False, test_mode=test_mode
            )
            config.set("stock", [{"symbol": "AAPL", "enabled": False}], autosave=False)
            assert config.save() is True
            target = Path(config.get_config_file_path())
            payload = yaml_codec.load_yaml(target.read_text(encoding="utf-8"))
            assert set(payload) >= {"__data__", "__type_hints__"}
            assert payload["__data__"]["stock"] == [
                {"symbol": "AAPL", "enabled": False}
            ]
            assert payload["__data__"]["category_subscription_order"] == [
                "stock",
                "future",
            ]
            config.cleanup()
            config = None
            _clear_config_instances()
            reloaded = manager_module.get_config_manager(
                config_path=str(target), watch=False, test_mode=False
            )
            assert reloaded.get("stock") == [{"symbol": "AAPL", "enabled": False}]
        finally:
            if reloaded is not None:
                reloaded.cleanup()
            if config is not None:
                config.cleanup()
            _clear_config_instances()


def test_s1_03_e2e_unsupported_value_preserves_target_bytes(yaml_codec, tmp_path):
    config_path = tmp_path / "unsupported-value.yaml"
    config_path.write_text(
        """__data__:
  stock:
    - symbol: 600519
__type_hints__: {}
""",
        encoding="utf-8",
    )
    config = None
    try:
        _clear_config_instances()
        manager_module = importlib.import_module("config_manager")
        config = manager_module.get_config_manager(
            config_path=str(config_path), watch=False, test_mode=False
        )
        target = Path(config.get_config_file_path())
        before = target.read_bytes()
        config.set("unsupported", object(), autosave=False)

        assert config.save() is False
        assert target.read_bytes() == before
        assert _candidate_paths(target) == []
    finally:
        if config is not None:
            config.cleanup()
        _clear_config_instances()
