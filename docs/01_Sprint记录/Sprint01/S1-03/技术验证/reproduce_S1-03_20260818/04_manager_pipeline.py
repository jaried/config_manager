"""Locate S1-03's first divergence in the exact ConfigManager save pipeline."""

from __future__ import annotations

# ruff: noqa: E402

from datetime import datetime

first_start_time = datetime.now()

from io import StringIO
from pathlib import Path
import re
import sys


WORKTREE = Path(__file__).resolve().parents[6]
SOURCE_ROOT = WORKTREE / "src"
sys.path.insert(0, str(SOURCE_ROOT))

from config_manager import get_config_manager
from ruamel.yaml import YAML


SCRIPT_DIR = Path(__file__).resolve().parent
INPUT_PATH = SCRIPT_DIR / "01_input_commented.yaml"
OUTPUT_PATH = SCRIPT_DIR / "04_manager_pipeline_output.txt"
PRE_POSTPROCESS_PATH = SCRIPT_DIR / "04_pre_postprocess.yaml"
POSTPROCESSED_PATH = SCRIPT_DIR / "04_postprocessed.yaml"
BROKEN_SEQUENCE = re.compile(r"(?m)^\s+[A-Za-z_][A-Za-z0-9_]*:\s+-\s*$")


def parse_text(text: str) -> tuple[bool, str]:
    try:
        YAML(typ="safe").load(text)
    except Exception as error:
        return False, f"{type(error).__name__}: {error}"
    return True, ""


def main() -> int:
    manager = get_config_manager(
        config_path=str(INPUT_PATH),
        watch=False,
        autosave_delay=3600.0,
        first_start_time=first_start_time,
        test_mode=True,
    )
    if manager is None:
        print("probe_status=blocked\nmanager=None")
        return 2

    try:
        isolated_path = Path(manager.get_config_path()).resolve()
        isolated_before = isolated_path.read_text(encoding="utf-8")
        isolated_before_valid, isolated_before_error = parse_text(isolated_before)

        operations = manager._file_ops
        original_watchlist = operations._original_yaml_data["__data__"]["monitor"]["watchlist"]
        original_stock_after_init = original_watchlist["stock"]
        original_parent_key_comment = original_watchlist.ca.items.get("stock")

        manager.set("monitor.watchlist.stock", ["SSE.600519"], autosave=False)
        manager.set(
            "monitor.category_subscription_order",
            ["index_option", "etf", "stock", "all"],
            autosave=False,
        )

        serializable_data = manager._get_serializable_data()
        serialized_stock = serializable_data["monitor"]["watchlist"]["stock"]
        data_to_save = {
            "__data__": serializable_data,
            "__type_hints__": manager._type_hints,
        }
        prepared = operations._prepare_data_for_save(str(isolated_path), data_to_save)
        prepared_watchlist = prepared["__data__"]["monitor"]["watchlist"]
        prepared_stock = prepared_watchlist["stock"]

        stream = StringIO()
        operations._yaml.dump(prepared, stream)
        pre_postprocess_text = stream.getvalue()
        PRE_POSTPROCESS_PATH.write_text(pre_postprocess_text, encoding="utf-8")
        pre_valid, pre_error = parse_text(pre_postprocess_text)

        POSTPROCESSED_PATH.write_text(pre_postprocess_text, encoding="utf-8")
        operations._remove_duplicate_keys_from_yaml_file(str(POSTPROCESSED_PATH))
        postprocessed_text = POSTPROCESSED_PATH.read_text(encoding="utf-8")
        post_valid, post_error = parse_text(postprocessed_text)
        postprocessor_changed_output = postprocessed_text != pre_postprocess_text

        first_deviation_match = (
            isolated_before_valid
            and type(original_stock_after_init).__name__ == "list"
            and original_parent_key_comment is not None
            and type(serialized_stock).__name__ == "list"
            and type(prepared_stock).__name__ == "list"
            and not pre_valid
            and bool(BROKEN_SEQUENCE.search(pre_postprocess_text))
            and not post_valid
            and not postprocessor_changed_output
            and "sequence entries are not allowed here" in pre_error
        )
        lines = [
            f"input_path={INPUT_PATH}",
            f"isolated_path={isolated_path}",
            f"isolated_before_valid={isolated_before_valid}",
            f"isolated_before_error={isolated_before_error}",
            f"original_stock_after_init_type={type(original_stock_after_init).__name__}",
            f"original_parent_key_comment_after_init={repr(original_parent_key_comment)}",
            f"serialized_stock_type={type(serialized_stock).__name__}",
            f"serialized_stock_value={serialized_stock}",
            f"prepared_stock_type={type(prepared_stock).__name__}",
            f"prepared_stock_value={prepared_stock}",
            f"prepared_parent_key_comment={repr(prepared_watchlist.ca.items.get('stock'))}",
            f"pre_postprocess_valid={pre_valid}",
            f"pre_postprocess_broken_layout={bool(BROKEN_SEQUENCE.search(pre_postprocess_text))}",
            f"pre_postprocess_error={pre_error}",
            f"postprocessor_changed_output={postprocessor_changed_output}",
            f"postprocessed_valid={post_valid}",
            f"postprocessed_error={post_error}",
            "first_deviation_boundary=ConfigManagerCore._get_serializable_data -> "
            "FileOperations._prepare_data_for_save -> YAML.dump",
            f"first_deviation_match={first_deviation_match}",
            f"probe_status={'verified' if first_deviation_match else 'blocked'}",
        ]
    finally:
        manager.cleanup()

    OUTPUT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    return 0 if first_deviation_match else 1


if __name__ == "__main__":
    raise SystemExit(main())
