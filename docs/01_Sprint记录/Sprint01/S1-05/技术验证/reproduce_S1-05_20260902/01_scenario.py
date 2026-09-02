"""Verify the public progress autosave path in an isolated consumer runtime."""

from __future__ import annotations

import atexit
from datetime import datetime

first_start_time = datetime.now()

import json
import os
from pathlib import Path
import shutil
import sys
import time

import config_manager
from config_manager import get_config_manager
from config_manager.yaml_codec import load_yaml


SCENARIO_DIR = Path(__file__).resolve().parent
INPUT_PATH = SCENARIO_DIR / "01_input.yaml"
RUNTIME_PATH = SCENARIO_DIR / "runtime_config.yaml"


def _progress_value(path: Path):
    loaded = load_yaml(path.read_text(encoding="utf-8"))
    return loaded["__data__"]["progress"]


def _snapshot_backups(root: Path) -> dict[str, int]:
    if not root.exists():
        return {}
    return {
        str(path.relative_to(SCENARIO_DIR)): path.stat().st_mtime_ns
        for path in root.rglob("*.yaml")
    }


def main() -> None:
    shutil.copyfile(INPUT_PATH, RUNTIME_PATH)
    cfg = get_config_manager(
        config_path=str(RUNTIME_PATH),
        watch=True,
        auto_create=False,
        autosave_delay=0.1,
        first_start_time=first_start_time,
        test_mode=False,
    )
    if cfg is None:
        raise RuntimeError("config_manager initialization returned None")

    save_calls = []
    save_only_calls = []
    original_save_config = cfg._file_ops.save_config
    original_save_config_only = cfg._file_ops.save_config_only

    def recording_save_config(config_path, data, backup_path=None):
        save_calls.append(backup_path)
        return original_save_config(config_path, data, backup_path)

    def recording_save_config_only(config_path, data):
        save_only_calls.append(config_path)
        return original_save_config_only(config_path, data)

    cfg._file_ops.save_config = recording_save_config
    cfg._file_ops.save_config_only = recording_save_config_only

    backup_root = Path(cfg.paths.backup_dir)
    backups_before = _snapshot_backups(backup_root)
    runtime_mtime_before = RUNTIME_PATH.stat().st_mtime_ns

    cfg.progress = "after"

    deadline = time.monotonic() + 4.0
    while time.monotonic() < deadline:
        timer = cfg._autosave_manager._autosave_timer
        saved = _progress_value(RUNTIME_PATH) == "after"
        if saved and timer is None:
            break
        time.sleep(0.05)

    backups_after = _snapshot_backups(backup_root)
    runtime_mtime_after = RUNTIME_PATH.stat().st_mtime_ns
    result = {
        "backups_after": backups_after,
        "backups_before": backups_before,
        "backups_unchanged": backups_after == backups_before,
        "config_manager_import": str(Path(config_manager.__file__).resolve()),
        "config_progress_after": _progress_value(RUNTIME_PATH),
        "main_file_changed": runtime_mtime_after > runtime_mtime_before,
        "pending_roots_after": sorted(cfg._pending_autosave_roots),
        "pending_unknown_after": cfg._pending_autosave_unknown,
        "python_executable": sys.executable,
        "save_config_calls": len(save_calls),
        "save_config_only_calls": len(save_only_calls),
        "watcher_internal_flag_after": cfg._watcher._internal_save_flag,
        "watcher_mtime_matches_file": (
            cfg._watcher._last_mtime == os.path.getmtime(RUNTIME_PATH)
        ),
    }

    atexit.unregister(cfg._cleanup)
    cfg.cleanup()
    cfg._cleanup_done = True
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
