from __future__ import annotations

import inspect
import os
import threading
from datetime import datetime
from pathlib import Path

import pytest

from src.config_manager.config_manager import ConfigManager
from src.config_manager.config_node import ConfigNode
from src.config_manager.core.file_operations import FileOperations
from src.config_manager.core.manager import ConfigManagerCore
from src.config_manager.core.watcher import FileWatcher
from src.config_manager.yaml_codec import load_yaml


class CapturingAutosaveManager:
    def __init__(self):
        self.callbacks = []

    def schedule_save(self, callback):
        self.callbacks.append(callback)

    def fire(self):
        assert self.callbacks
        return self.callbacks[-1]()


class RecordingFileOperations(FileOperations):
    def __init__(self):
        super().__init__()
        self.save_calls = []
        self.save_only_calls = []

    def save_config(self, config_path, data, backup_path=None):
        self.save_calls.append((config_path, data, backup_path))
        return super().save_config(config_path, data, backup_path)

    def save_config_only(self, config_path, data):
        self.save_only_calls.append((config_path, data))
        return super().save_config_only(config_path, data)


class FailingFileOperations:
    def __init__(self, error=None):
        self.error = error

    def save_config_only(self, config_path, data):
        if self.error:
            raise self.error
        return False


@pytest.fixture
def core(tmp_path):
    manager = ConfigManagerCore()
    manager._config_loaded_successfully = True
    manager._config_path = str(tmp_path / "config.yaml")
    manager._file_ops = RecordingFileOperations()
    manager._autosave_manager = CapturingAutosaveManager()
    manager._watcher = None
    manager._type_hints = {}
    manager._first_start_time = datetime(2025, 1, 1, 0, 0, 0)
    manager._autosave_last_time = 0
    manager._data.clear()
    yield manager


def test_root_attribute_passes_keyed_intent(core):
    core.progress = 0.25

    assert len(core._autosave_manager.callbacks) == 1
    assert core._pending_autosave_roots == {"progress"}
    assert core._pending_autosave_unknown is False


def test_config_node_only_schedules_root_manager():
    node = ConfigNode()
    node.value = 1

    assert not hasattr(node, "_pending_autosave_roots")


@pytest.mark.parametrize("key", ["progress", "progress.current"])
def test_core_set_collects_root_key(core, key):
    core.set(key, 0.5)

    assert core._pending_autosave_roots == {"progress"}
    assert core._pending_autosave_unknown is False
    assert len(core._autosave_manager.callbacks) == 1


def test_core_update_unions_roots_and_schedules_once(core):
    core.update({"progress.current": 0.5, "ordinary.value": 1})

    assert core._pending_autosave_roots == {"progress", "ordinary"}
    assert core._pending_autosave_unknown is False
    assert len(core._autosave_manager.callbacks) == 1


def test_progress_batch_uses_main_file_without_backup_and_round_trips(core):
    core._data["progress"] = 0.75
    core._pending_autosave_roots = {"progress"}

    assert core._delayed_save() is True

    operations = core._file_ops
    assert len(operations.save_only_calls) == 1
    assert operations.save_calls == []
    assert core._pending_autosave_roots == set()
    assert core._pending_autosave_unknown is False
    assert not hasattr(core, "_last_backup_path")

    saved = load_yaml(Path(core._config_path).read_text(encoding="utf-8"))
    assert saved["__data__"]["progress"] == 0.75


@pytest.mark.parametrize(
    "roots,unknown",
    [
        ({"progress", "ordinary"}, False),
        ({"ordinary", "progress"}, False),
        (set(), True),
    ],
)
def test_non_progress_or_unknown_batch_uses_backup_save(core, roots, unknown):
    core._pending_autosave_roots = roots
    core._pending_autosave_unknown = unknown
    core._data["progress"] = 0.75
    core._data["ordinary"] = 1

    assert core._delayed_save() is True

    operations = core._file_ops
    assert len(operations.save_calls) == 1
    assert operations.save_only_calls == []
    assert core._pending_autosave_roots == set()
    assert core._pending_autosave_unknown is False
    assert core._last_backup_path == operations.save_calls[0][2]
    assert os.path.exists(core._last_backup_path)


def test_explicit_save_keeps_generic_backup_semantics(core):
    core._pending_autosave_roots = {"progress"}
    core._data["progress"] = 0.5

    assert core.save() is True

    assert len(core._file_ops.save_calls) == 1
    assert core._file_ops.save_only_calls == []


def test_facade_set_keeps_public_signature_and_schedules_one_root_key():
    manager = object.__new__(ConfigManager)
    ConfigManagerCore.__init__(manager)
    manager._config_loaded_successfully = True
    manager._autosave_manager = CapturingAutosaveManager()
    manager._autosave_last_time = 0

    signature = inspect.signature(ConfigManager.set)
    assert list(signature.parameters) == ["self", "key", "value", "autosave", "type_hint"]

    ConfigManager.set(manager, "progress.current", 0.5)

    assert len(manager._autosave_manager.callbacks) == 1
    assert manager._pending_autosave_roots == {"progress"}
    assert manager._pending_autosave_unknown is False


def test_watcher_guard_reenters_and_confirms_watermark(tmp_path):
    config_path = tmp_path / "config.yaml"
    config_path.write_text("old", encoding="utf-8")
    old_mtime = config_path.stat().st_mtime

    watcher = FileWatcher()
    watcher._config_path = str(config_path)
    watcher._last_mtime = old_mtime

    with watcher._internal_save_guard():
        watcher.set_internal_save_flag(True)
        config_path.write_text("new", encoding="utf-8")
        os.utime(
            config_path,
            ns=(
                config_path.stat().st_atime_ns,
                int(old_mtime * 1_000_000_000) + 1_000_000,
            ),
        )
        watcher._confirm_internal_save()

    assert watcher._last_mtime == os.path.getmtime(config_path)
    assert watcher._internal_save_flag is False
    assert watcher._state_lock.acquire(blocking=False)
    watcher._state_lock.release()


@pytest.mark.parametrize("error", [None, RuntimeError("write failed")])
def test_failed_progress_save_clears_flag_without_advancing_watermark(tmp_path, error):
    config_path = tmp_path / "config.yaml"
    config_path.write_text("old", encoding="utf-8")
    old_mtime = config_path.stat().st_mtime

    manager = ConfigManagerCore()
    manager._config_loaded_successfully = True
    manager._config_path = str(config_path)
    manager._file_ops = FailingFileOperations(error)
    manager._watcher = FileWatcher()
    manager._watcher._config_path = str(config_path)
    manager._watcher._last_mtime = old_mtime
    manager._type_hints = {}
    manager._data["progress"] = 0.5
    manager._pending_autosave_roots = {"progress"}

    if error:
        with pytest.raises(RuntimeError, match="write failed"):
            manager._delayed_save()
    else:
        assert manager._delayed_save() is False

    assert manager._watcher._last_mtime == old_mtime
    assert manager._watcher._internal_save_flag is False
    assert manager._watcher._state_lock.acquire(blocking=False)
    manager._watcher._state_lock.release()
    assert manager._pending_autosave_roots == set()
    assert manager._pending_autosave_unknown is False


def test_watcher_external_change_calls_back_after_guard_release(tmp_path):
    config_path = tmp_path / "config.yaml"
    config_path.write_text("old", encoding="utf-8")

    callback_lock_was_free = []
    watcher = FileWatcher()
    watcher._config_path = str(config_path)
    watcher._last_mtime = config_path.stat().st_mtime

    def callback():
        acquired = watcher._state_lock.acquire(blocking=False)
        callback_lock_was_free.append(acquired)
        if acquired:
            watcher._state_lock.release()

    watcher._callback = callback
    with watcher._internal_save_guard():
        watcher.set_internal_save_flag(True)
        config_path.write_text("internal", encoding="utf-8")
        watcher._confirm_internal_save()

    os.utime(
        config_path,
        ns=(config_path.stat().st_atime_ns, config_path.stat().st_mtime_ns + 1_000_000),
    )
    watcher._poll_once()

    assert callback_lock_was_free == [True]


def test_watcher_poll_is_blocked_by_guard_until_confirmation(tmp_path):
    config_path = tmp_path / "config.yaml"
    config_path.write_text("old", encoding="utf-8")
    watcher = FileWatcher()
    watcher._config_path = str(config_path)
    watcher._last_mtime = config_path.stat().st_mtime
    watcher._callback = lambda: pytest.fail("internal progress save must not callback")

    entered = threading.Event()
    released = threading.Event()

    def poll():
        entered.set()
        watcher._poll_once()
        released.set()

    with watcher._internal_save_guard():
        watcher.set_internal_save_flag(True)
        config_path.write_text("internal", encoding="utf-8")
        os.utime(
            config_path,
            ns=(
                config_path.stat().st_atime_ns,
                int(watcher._last_mtime * 1_000_000_000) + 1_000_000,
            ),
        )
        thread = threading.Thread(target=poll)
        thread.start()
        assert entered.wait(timeout=1)
        assert not released.wait(timeout=0.05)
        watcher._confirm_internal_save()

    thread.join(timeout=1)
    assert released.is_set()
