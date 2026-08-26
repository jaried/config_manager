"""Reproduce the S1-04 save, watcher, and backup chain in an isolated file."""

# ruff: noqa: E402

from datetime import datetime

first_start_time = datetime.now()

import contextlib
import io
import json
import os
from pathlib import Path
import shutil
import time

import config_manager
from config_manager import get_config_manager
from config_manager.yaml_codec import load_yaml


SCENARIO_DIR = Path(__file__).resolve().parent
INPUT_PATH = SCENARIO_DIR / "01_input.yaml"
RUNTIME_PATH = SCENARIO_DIR / "runtime_config_v2.yaml"


def _progress_value(path: Path):
    loaded = load_yaml(path.read_text(encoding="utf-8"))
    return loaded["__data__"]["progress"]


def main() -> None:
    shutil.copyfile(INPUT_PATH, RUNTIME_PATH)
    captured_stdout = io.StringIO()
    callback_calls = []
    manager_backup_arguments = []
    cfg = None

    with contextlib.redirect_stdout(captured_stdout):
        try:
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

            backup_root = Path(cfg.paths.backup_dir)
            before_backups = (
                set(backup_root.rglob("*.yaml")) if backup_root.exists() else set()
            )
            before_backup_mtimes = {
                path: path.stat().st_mtime_ns for path in before_backups
            }
            watcher_mtime_before = cfg._watcher._last_mtime
            original_callback = cfg._watcher._callback

            def recording_callback():
                callback_calls.append("called")
                return original_callback()

            cfg._watcher._callback = recording_callback
            original_save_config = cfg._file_ops.save_config

            def recording_save_config(config_path, data, backup_path=None):
                manager_backup_arguments.append(backup_path)
                return original_save_config(config_path, data, backup_path)

            cfg._file_ops.save_config = recording_save_config
            cfg.progress = "after"

            deadline = time.monotonic() + 4.0
            while time.monotonic() < deadline:
                after_backups = (
                    set(backup_root.rglob("*.yaml")) if backup_root.exists() else set()
                )
                config_saved = _progress_value(RUNTIME_PATH) == "after"
                backup_argument = (
                    Path(manager_backup_arguments[-1])
                    if manager_backup_arguments and manager_backup_arguments[-1]
                    else None
                )
                backup_saved = (
                    backup_argument is not None
                    and backup_argument.exists()
                    and _progress_value(backup_argument) == "after"
                )
                watcher_processed = cfg._watcher._last_mtime == os.path.getmtime(
                    RUNTIME_PATH
                )
                if (
                    config_saved
                    and backup_saved
                    and watcher_processed
                    and not cfg._watcher._internal_save_flag
                ):
                    break
                time.sleep(0.1)

            after_backups = (
                set(backup_root.rglob("*.yaml")) if backup_root.exists() else set()
            )
            backup_argument = Path(manager_backup_arguments[-1])
            backup_progress_after = _progress_value(backup_argument)
            backup_rewritten = (
                backup_argument not in before_backup_mtimes
                or backup_argument.stat().st_mtime_ns
                > before_backup_mtimes[backup_argument]
            )
            progress_after = _progress_value(RUNTIME_PATH)
            watcher_mtime_after = cfg._watcher._last_mtime
            runtime_mtime_after = os.path.getmtime(RUNTIME_PATH)
            watcher_internal_flag_after = cfg._watcher._internal_save_flag
            progress_stdout = captured_stdout.getvalue()
            progress_backup_arguments = list(manager_backup_arguments)
        finally:
            if cfg is not None:
                cfg._cleanup()

    messages = [
        line
        for line in progress_stdout.splitlines()
        if "自动备份" in line or "内部保存" in line or "文件变化" in line
    ]
    cleanup_messages = [
        line
        for line in captured_stdout.getvalue()[len(progress_stdout) :].splitlines()
        if "自动备份" in line or "内部保存" in line or "文件变化" in line
    ]
    result = {
        "backup_count_before": len(before_backups),
        "backup_count_after": len(after_backups),
        "backup_progress_after": backup_progress_after,
        "backup_rewritten_by_progress_save": backup_rewritten,
        "callback_count": len(callback_calls),
        "cleanup_messages": cleanup_messages,
        "config_manager_import": str(Path(config_manager.__file__).resolve()),
        "failure_signature_match": (
            progress_after == "after"
            and backup_progress_after == "after"
            and backup_rewritten
            and watcher_mtime_after == runtime_mtime_after
            and not watcher_internal_flag_after
            and any("配置已自动备份到" in message for message in messages)
            and any("跳过内部保存触发的文件变化检测" in message for message in messages)
        ),
        "input_change_keys": ["progress"],
        "manager_backup_argument": str(
            Path(progress_backup_arguments[-1]).relative_to(SCENARIO_DIR)
        ),
        "observed_messages": messages,
        "progress_after": progress_after,
        "watcher_internal_flag_after": watcher_internal_flag_after,
        "watcher_mtime_advanced": watcher_mtime_after > watcher_mtime_before,
        "watcher_processed_saved_mtime": watcher_mtime_after == runtime_mtime_after,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
