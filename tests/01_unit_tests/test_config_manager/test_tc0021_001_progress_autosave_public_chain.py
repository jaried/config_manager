# tests/01_unit_tests/test_config_manager/test_tc0021_001_progress_autosave_public_chain.py
from __future__ import annotations
from datetime import datetime
start_time = datetime.now()
# ruff: noqa: DTZ001, DTZ005, I001, PLR1711, RUF013, UP006, UP035

from collections.abc import Callable
from pathlib import Path
from typing import Any, Dict

from src.config_manager.config_manager import ConfigManager
from src.config_manager.core.file_operations import FileOperations
from src.config_manager.core.manager import ConfigManagerCore
from src.config_manager.yaml_codec import load_yaml


class CapturingAutosaveManager:
    def __init__(self) -> None:
        self.callbacks: list[Callable[[], bool]] = []
        return

    def schedule_save(self, callback: Callable[[], bool]) -> None:
        self.callbacks.append(callback)
        return

    def fire(self) -> bool:
        assert self.callbacks
        callback = self.callbacks[-1]
        result = callback()
        return result


class RecordingFileOperations(FileOperations):
    def __init__(self) -> None:
        super().__init__()
        self.save_calls: list[tuple[str, Dict[str, Any], str | None]] = []
        self.save_only_calls: list[tuple[str, Dict[str, Any]]] = []
        return

    def save_config(
        self,
        config_path: str,
        data: Dict[str, Any],
        backup_path: str = None,
    ) -> bool:
        self.save_calls.append((config_path, data, backup_path))
        result = super().save_config(config_path, data, backup_path)
        return result

    def save_config_only(
        self,
        config_path: str,
        data: Dict[str, Any],
    ) -> bool:
        self.save_only_calls.append((config_path, data))
        result = super().save_config_only(config_path, data)
        return result


def _build_manager(tmp_path: Path) -> ConfigManagerCore:
    manager = object.__new__(ConfigManager)
    ConfigManagerCore.__init__(manager)
    manager._config_loaded_successfully = True
    manager._config_path = str(tmp_path / "config.yaml")
    manager._file_ops = RecordingFileOperations()
    manager._autosave_manager = CapturingAutosaveManager()
    manager._watcher = None
    manager._type_hints = {}
    manager._first_start_time = datetime(2025, 1, 1, 0, 0, 0)
    manager._autosave_last_time = 0
    manager._data.clear()
    return manager


def _seed_main_and_backup(manager: ConfigManagerCore) -> Path:
    manager._data["progress"] = "before"
    main_saved = manager._save_config_only()
    assert main_saved is True

    config_path = Path(manager._config_path)
    config_text = config_path.read_text(encoding="utf-8")
    backup_data = load_yaml(config_text)
    backup_path_text = manager._file_ops.get_backup_path(
        manager._config_path,
        manager._first_start_time,
        manager,
    )
    backup_saved = manager._file_ops.create_backup_only(
        backup_path_text,
        backup_data,
    )
    assert backup_saved is True

    manager._last_backup_path = backup_path_text
    manager._file_ops.save_calls.clear()
    manager._file_ops.save_only_calls.clear()
    backup_path = Path(backup_path_text)
    return backup_path


def _snapshot_backup_tree(backup_root: Path) -> Dict[str, tuple[int, bytes]]:
    snapshot = {}
    for backup_path in sorted(backup_root.rglob("*.yaml")):
        relative_path = backup_path.relative_to(backup_root).as_posix()
        file_state = (
            backup_path.stat().st_mtime_ns,
            backup_path.read_bytes(),
        )
        snapshot[relative_path] = file_state
    return snapshot


def test_tc0021_001_001_progress_public_chain_persists_without_backup(
    tmp_path: Path,
) -> None:
    manager = _build_manager(tmp_path)
    backup_path = _seed_main_and_backup(manager)
    backup_root = Path(manager._config_path).parent / "backup"
    backup_snapshot_before = _snapshot_backup_tree(backup_root)
    last_backup_path_before = manager._last_backup_path

    assert isinstance(manager, ConfigManager)
    assert len(backup_snapshot_before) == 1

    manager.progress = "after"

    autosave_manager = manager._autosave_manager
    assert isinstance(autosave_manager, CapturingAutosaveManager)
    assert len(autosave_manager.callbacks) == 1
    assert manager._pending_autosave_roots == {"progress"}
    assert manager._pending_autosave_unknown is False

    autosave_saved = autosave_manager.fire()
    assert autosave_saved is True

    file_ops = manager._file_ops
    assert isinstance(file_ops, RecordingFileOperations)
    assert len(file_ops.save_only_calls) == 1
    assert file_ops.save_calls == []
    assert manager._pending_autosave_roots == set()
    assert manager._pending_autosave_unknown is False

    config_path = Path(manager._config_path)
    config_text = config_path.read_text(encoding="utf-8")
    saved_config = load_yaml(config_text)
    assert saved_config["__data__"]["progress"] == "after"

    backup_snapshot_after = _snapshot_backup_tree(backup_root)
    backup_text = backup_path.read_text(encoding="utf-8")
    backup_config = load_yaml(backup_text)
    assert backup_snapshot_after == backup_snapshot_before
    assert backup_config["__data__"]["progress"] == "before"
    assert manager._last_backup_path == last_backup_path_before
    return
