"""Check whether S1-03 reproduces outside ConfigManager test mode."""

from __future__ import annotations

# ruff: noqa: E402

from datetime import datetime

first_start_time = datetime.now()

from pathlib import Path
import re
import shutil
import sys


WORKTREE = Path(__file__).resolve().parents[6]
SOURCE_ROOT = WORKTREE / "src"
sys.path.insert(0, str(SOURCE_ROOT))

from config_manager import get_config_manager
from ruamel.yaml import YAML


SCRIPT_DIR = Path(__file__).resolve().parent
INPUT_PATH = SCRIPT_DIR / "01_input_commented.yaml"
RUNTIME_PATH = SCRIPT_DIR / "07_runtime_config.yaml"
OUTPUT_PATH = SCRIPT_DIR / "07_non_test_scenario_output.txt"
BROKEN_SEQUENCE = re.compile(
    r"(?m)^\s+[A-Za-z_][A-Za-z0-9_]*:\s+(?:&[^\s]+\s+)?-\s*$"
)


def parse_yaml(path: Path) -> tuple[bool, str]:
    try:
        with path.open("r", encoding="utf-8") as stream:
            YAML(typ="safe").load(stream)
    except Exception as error:
        return False, f"{type(error).__name__}: {error}"
    return True, ""


def main() -> int:
    shutil.copyfile(INPUT_PATH, RUNTIME_PATH)
    source_valid, source_error = parse_yaml(RUNTIME_PATH)
    manager = get_config_manager(
        config_path=str(RUNTIME_PATH),
        watch=False,
        autosave_delay=3600.0,
        first_start_time=first_start_time,
        test_mode=False,
    )
    if manager is None:
        print("scenario_status=blocked\nmanager=None")
        return 2

    try:
        after_init_valid, after_init_error = parse_yaml(RUNTIME_PATH)
        after_init_text = RUNTIME_PATH.read_text(encoding="utf-8")
        manager.set("monitor.watchlist.stock", ["SSE.600519"], autosave=False)
        manager.set(
            "monitor.category_subscription_order",
            ["index_option", "etf", "stock", "all"],
            autosave=False,
        )
        save_result = manager.save()
        saved_text = RUNTIME_PATH.read_text(encoding="utf-8")
        saved_valid, saved_error = parse_yaml(RUNTIME_PATH)
        broken_layout = bool(BROKEN_SEQUENCE.search(saved_text))
        signature_match = (
            source_valid
            and after_init_valid
            and save_result is True
            and not saved_valid
            and broken_layout
            and "sequence entries are not allowed here" in saved_error
        )
        lines = [
            f"input_path={INPUT_PATH}",
            f"runtime_path={RUNTIME_PATH}",
            "test_mode=False",
            f"source_valid={source_valid}",
            f"source_error={source_error}",
            f"after_init_valid={after_init_valid}",
            f"after_init_broken_layout={bool(BROKEN_SEQUENCE.search(after_init_text))}",
            f"after_init_error={after_init_error}",
            f"save_result={save_result}",
            f"saved_valid={saved_valid}",
            f"saved_broken_layout={broken_layout}",
            f"saved_error={saved_error}",
            f"failure_signature_match={signature_match}",
            f"scenario_status={'reproduced' if signature_match else 'not_reproduced'}",
        ]
    finally:
        manager.cleanup()

    OUTPUT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    return 0 if signature_match else 1


if __name__ == "__main__":
    raise SystemExit(main())
