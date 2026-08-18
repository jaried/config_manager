"""Locate the first S1-03 divergence inside the FileOperations save pipeline."""

from __future__ import annotations

from collections.abc import Mapping
from io import StringIO
from pathlib import Path
import re
import sys


WORKTREE = Path(__file__).resolve().parents[6]
SOURCE_ROOT = WORKTREE / "src"
sys.path.insert(0, str(SOURCE_ROOT))

from config_manager.core.file_operations import FileOperations
from ruamel.yaml import YAML


SCRIPT_DIR = Path(__file__).resolve().parent
INPUT_PATH = SCRIPT_DIR / "01_input_commented.yaml"
PRE_POSTPROCESS_PATH = SCRIPT_DIR / "03_pre_postprocess_v2.yaml"
POSTPROCESSED_PATH = SCRIPT_DIR / "03_postprocessed_v2.yaml"
OUTPUT_PATH = SCRIPT_DIR / "03_first_deviation_output_v2.txt"
BROKEN_SEQUENCE = re.compile(r"(?m)^\s+[A-Za-z_][A-Za-z0-9_]*:\s+-\s*$")


def parse_text(text: str) -> tuple[bool, str]:
    try:
        YAML(typ="safe").load(text)
    except Exception as error:
        return False, f"{type(error).__name__}: {error}"
    return True, ""


def convert_mappings_to_plain_dict(value: object) -> object:
    """Mirror ConfigNode.to_dict while preserving ruamel sequence objects."""
    if isinstance(value, Mapping):
        return {
            key: convert_mappings_to_plain_dict(item)
            for key, item in value.items()
        }
    return value


def main() -> int:
    operations = FileOperations()
    loaded = operations.load_config(str(INPUT_PATH), auto_create=False, call_chain_tracker=None)
    if loaded is None:
        print("probe_status=blocked\nloaded=None")
        return 2

    lines: list[str] = []
    original_stock = operations._original_yaml_data["__data__"]["monitor"]["watchlist"]["stock"]
    lines.extend(
        [
            f"input_path={INPUT_PATH}",
            f"original_stock_type={type(original_stock).__name__}",
            f"original_stock_comment={repr(original_stock.ca.comment)}",
        ]
    )

    serializable_data = convert_mappings_to_plain_dict(loaded["__data__"])
    serializable_data["monitor"]["watchlist"]["stock"] = ["SSE.600519"]
    serialized_stock = serializable_data["monitor"]["watchlist"]["stock"]
    serialized_values_correct = serialized_stock == ["SSE.600519"]
    lines.extend(
        [
            f"serialized_stock_type={type(serialized_stock).__name__}",
            f"serialized_stock_value={serialized_stock}",
            f"serialized_values_correct={serialized_values_correct}",
        ]
    )

    data_to_save = {"__data__": serializable_data, "__type_hints__": {}}
    prepared = operations._prepare_data_for_save(str(INPUT_PATH), data_to_save)
    prepared_watchlist = prepared["__data__"]["monitor"]["watchlist"]
    prepared_stock = prepared_watchlist["stock"]
    lines.extend(
        [
            f"prepared_stock_type={type(prepared_stock).__name__}",
            f"prepared_stock_value={prepared_stock}",
            f"prepared_parent_key_comment={repr(prepared_watchlist.ca.items.get('stock'))}",
        ]
    )

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
        serialized_values_correct
        and type(original_stock).__name__ == "CommentedSeq"
        and type(prepared_stock).__name__ == "list"
        and not pre_valid
        and bool(BROKEN_SEQUENCE.search(pre_postprocess_text))
        and not post_valid
        and not postprocessor_changed_output
        and "sequence entries are not allowed here" in pre_error
    )
    lines.extend(
        [
            f"pre_postprocess_valid={pre_valid}",
            f"pre_postprocess_broken_layout={bool(BROKEN_SEQUENCE.search(pre_postprocess_text))}",
            f"pre_postprocess_error={pre_error}",
            f"postprocessor_changed_output={postprocessor_changed_output}",
            f"postprocessed_valid={post_valid}",
            f"postprocessed_error={post_error}",
            f"first_deviation_boundary=FileOperations._prepare_data_for_save -> YAML.dump",
            f"first_deviation_match={first_deviation_match}",
            f"probe_status={'verified' if first_deviation_match else 'blocked'}",
        ]
    )

    OUTPUT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    return 0 if "probe_status=verified" in lines else 1


if __name__ == "__main__":
    raise SystemExit(main())
