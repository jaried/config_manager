# tests/01_unit_tests/test_config_manager/test_tc0021_001_progress_autosave_public_chain.py
from __future__ import annotations
from datetime import datetime
start_time = datetime.now()
# ruff: noqa: E402

from pathlib import Path
from unittest.mock import Mock

from src.config_manager.config_manager import ConfigManager
from src.config_manager.core.file_operations import FileOperations
from src.config_manager.core.manager import ConfigManagerCore
from src.config_manager.yaml_codec import load_yaml


def test_tc0021_001_001_progress_public_chain_persists_without_backup(
    tmp_path: Path,
) -> None:
    manager = object.__new__(ConfigManager)
    ConfigManagerCore.__init__(manager)
    manager._config_loaded_successfully = True
    manager._config_path = str(tmp_path / "config.yaml")
    manager._watcher = None
    manager._type_hints = {}
    manager._first_start_time = datetime(2025, 1, 1, 0, 0, 0)
    manager._autosave_last_time = 0
    manager._data.clear()
    manager._data["progress"] = "before"

    file_ops = FileOperations()
    save_config = file_ops.save_config
    save_config_only = file_ops.save_config_only
    file_ops.save_config = Mock(wraps=save_config)
    file_ops.save_config_only = Mock(wraps=save_config_only)
    manager._file_ops = file_ops

    callbacks = []
    autosave_manager = Mock()
    autosave_manager.schedule_save.side_effect = callbacks.append
    manager._autosave_manager = autosave_manager

    baseline_saved = manager.save()
    assert baseline_saved is True
    assert hasattr(manager, "_last_backup_path")

    backup_root = tmp_path / "backup"
    backup_paths_before = tuple(sorted(backup_root.rglob("*.yaml")))
    backup_snapshot_before = {
        path.relative_to(backup_root).as_posix(): (
            path.stat().st_mtime_ns,
            path.read_bytes(),
        )
        for path in backup_paths_before
    }
    assert len(backup_snapshot_before) == 1
    last_backup_path_before = manager._last_backup_path

    file_ops.save_config.reset_mock()
    file_ops.save_config_only.reset_mock()

    manager.progress = "after"

    assert isinstance(manager, ConfigManager)
    autosave_manager.schedule_save.assert_called_once()
    assert len(callbacks) == 1
    assert manager._pending_autosave_roots == {"progress"}
    assert manager._pending_autosave_unknown is False

    callback = callbacks[0]
    autosave_saved = callback()
    assert autosave_saved is True

    file_ops.save_config_only.assert_called_once()
    file_ops.save_config.assert_not_called()
    assert manager._pending_autosave_roots == set()
    assert manager._pending_autosave_unknown is False

    config_path = Path(manager._config_path)
    config_text = config_path.read_text(encoding="utf-8")
    saved_config = load_yaml(config_text)
    assert saved_config["__data__"]["progress"] == "after"

    backup_paths_after = tuple(sorted(backup_root.rglob("*.yaml")))
    backup_snapshot_after = {
        path.relative_to(backup_root).as_posix(): (
            path.stat().st_mtime_ns,
            path.read_bytes(),
        )
        for path in backup_paths_after
    }
    assert backup_paths_after == backup_paths_before
    assert backup_snapshot_after == backup_snapshot_before
    assert manager._last_backup_path == last_backup_path_before
    return
