"""Reproduce S1-03 through get_config_manager(test_mode=True), set(), and save()."""

from __future__ import annotations

# ruff: noqa: E402

from datetime import datetime

first_start_time = datetime.now()

from pathlib import Path
import re
import sys


WORKTREE = Path(__file__).resolve().parents[6]
SOURCE_ROOT = WORKTREE / "src"
sys.path.insert(0, str(SOURCE_ROOT))

from config_manager import get_config_manager
from ruamel.yaml import YAML


SCRIPT_DIR = Path(__file__).resolve().parent
INPUT_PATH = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else SCRIPT_DIR / "01_input.yaml"
OUTPUT_PATH = Path(sys.argv[2]).resolve() if len(sys.argv) > 2 else SCRIPT_DIR / "01_scenario_output.txt"
BROKEN_SEQUENCE = re.compile(
    r"(?m)^\s+[A-Za-z_][A-Za-z0-9_]*:\s+(?:&[^\s]+\s+)?-\s*$"
)


def parse_yaml(path: Path) -> tuple[bool, str]:
    parser = YAML(typ="safe")
    try:
        with path.open("r", encoding="utf-8") as stream:
            parser.load(stream)
    except Exception as error:
        return False, f"{type(error).__name__}: {error}"
    return True, ""


def main() -> int:
    source_valid, source_error = parse_yaml(INPUT_PATH)
    lines = [
        f"worktree={WORKTREE}",
        f"source_root={SOURCE_ROOT}",
        f"config_manager_module={get_config_manager.__module__}",
        f"input_path={INPUT_PATH}",
        f"input_valid={source_valid}",
        f"input_error={source_error}",
    ]

    if not source_valid:
        lines.append("scenario_status=blocked")
        OUTPUT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
        print("\n".join(lines))
        return 2

    manager = get_config_manager(
        config_path=str(INPUT_PATH),
        watch=False,
        autosave_delay=60.0,
        first_start_time=first_start_time,
        test_mode=True,
    )
    if manager is None:
        lines.append("scenario_status=blocked")
        lines.append("manager=None")
        OUTPUT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
        print("\n".join(lines))
        return 3

    try:
        isolated_path = Path(manager.get_config_path()).resolve()
        after_init_text = isolated_path.read_text(encoding="utf-8")
        after_init_valid, after_init_error = parse_yaml(isolated_path)
        lines.extend(
            [
                f"isolated_path={isolated_path}",
                f"after_init_valid={after_init_valid}",
                f"after_init_broken_layout={bool(BROKEN_SEQUENCE.search(after_init_text))}",
                f"after_init_error={after_init_error}",
            ]
        )

        manager.set(
            "monitor.watchlist.stock",
            ["SSE.600519"],
            autosave=False,
        )
        manager.set(
            "monitor.category_subscription_order",
            ["index_option", "etf", "stock", "all"],
            autosave=False,
        )
        save_result = manager.save()

        saved_text = isolated_path.read_text(encoding="utf-8")
        saved_valid, saved_error = parse_yaml(isolated_path)
        broken_layout = bool(BROKEN_SEQUENCE.search(saved_text))
        signature_match = save_result is True and broken_layout and not saved_valid and (
            "sequence entries are not allowed here" in saved_error
        )
        lines.extend(
            [
                f"save_result={save_result}",
                f"saved_valid={saved_valid}",
                f"saved_broken_layout={broken_layout}",
                f"saved_error={saved_error}",
                f"failure_signature_match={signature_match}",
                f"backup_path={manager.get_last_backup_path()}",
                f"scenario_status={'reproduced' if signature_match else 'not_reproduced'}",
                "saved_excerpt_start",
            ]
        )
        lines.extend(
            line
            for line in saved_text.splitlines()
            if "watchlist" in line
            or "stock:" in line
            or "etf:" in line
            or "SSE." in line
            or "category_subscription_order:" in line
            or line.strip() in {"- index_option", "- etf", "- stock", "- all"}
        )
        lines.append("saved_excerpt_end")
    finally:
        manager.cleanup()

    OUTPUT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    return 0 if "scenario_status=reproduced" in lines else 1


if __name__ == "__main__":
    raise SystemExit(main())
