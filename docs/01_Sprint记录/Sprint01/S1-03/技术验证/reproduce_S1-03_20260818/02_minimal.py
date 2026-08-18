"""Isolate S1-03 to ruamel.yaml comment metadata plus sequence replacement."""

from __future__ import annotations

from io import StringIO
from pathlib import Path
import re

from ruamel.yaml import YAML


SCRIPT_DIR = Path(__file__).resolve().parent
INPUT_PATH = SCRIPT_DIR / "02_input.yaml"
OUTPUT_PATH = SCRIPT_DIR / "02_minimal_output.txt"
UNCHANGED_PATH = SCRIPT_DIR / "02_unchanged.yaml"
REPLACED_PATH = SCRIPT_DIR / "02_replaced.yaml"
PLAIN_CONTROL_PATH = SCRIPT_DIR / "02_plain_control.yaml"
IN_PLACE_CONTROL_PATH = SCRIPT_DIR / "02_in_place_control.yaml"
BROKEN_SEQUENCE = re.compile(r"(?m)^\s+[A-Za-z_][A-Za-z0-9_]*:\s+-\s*$")


def configured_yaml(*, safe: bool = False) -> YAML:
    yaml = YAML(typ="safe") if safe else YAML()
    if not safe:
        yaml.preserve_quotes = True
        yaml.map_indent = 2
        yaml.sequence_indent = 4
        yaml.sequence_dash_offset = 2
        yaml.default_flow_style = False
    return yaml


def parse_text(text: str) -> tuple[bool, str]:
    try:
        configured_yaml(safe=True).load(text)
    except Exception as error:
        return False, f"{type(error).__name__}: {error}"
    return True, ""


def dump_text(data: object) -> str:
    stream = StringIO()
    configured_yaml().dump(data, stream)
    return stream.getvalue()


def main() -> int:
    source_text = INPUT_PATH.read_text(encoding="utf-8")
    source = configured_yaml().load(source_text)
    original_sequence = source["watchlist"]["stock"]
    original_sequence_type = type(original_sequence).__name__
    original_comment = repr(original_sequence.ca.comment)

    unchanged_text = dump_text(source)
    UNCHANGED_PATH.write_text(unchanged_text, encoding="utf-8")
    unchanged_valid, unchanged_error = parse_text(unchanged_text)

    source["watchlist"]["stock"] = ["SSE.600519"]
    replaced_sequence = source["watchlist"]["stock"]
    replaced_sequence_type = type(replaced_sequence).__name__
    parent_key_comment = repr(source["watchlist"].ca.items.get("stock"))
    replaced_text = dump_text(source)
    REPLACED_PATH.write_text(replaced_text, encoding="utf-8")
    replaced_valid, replaced_error = parse_text(replaced_text)

    plain = configured_yaml().load("watchlist:\n  stock:\n    - SSE.688825\n")
    plain["watchlist"]["stock"] = ["SSE.600519"]
    plain_text = dump_text(plain)
    PLAIN_CONTROL_PATH.write_text(plain_text, encoding="utf-8")
    plain_valid, plain_error = parse_text(plain_text)

    in_place = configured_yaml().load(source_text)
    in_place["watchlist"]["stock"][:] = ["SSE.600519"]
    in_place_text = dump_text(in_place)
    IN_PLACE_CONTROL_PATH.write_text(in_place_text, encoding="utf-8")
    in_place_valid, in_place_error = parse_text(in_place_text)

    causal_signature = (
        unchanged_valid
        and not replaced_valid
        and bool(BROKEN_SEQUENCE.search(replaced_text))
        and plain_valid
        and in_place_valid
        and "sequence entries are not allowed here" in replaced_error
    )
    lines = [
        f"ruamel_input={INPUT_PATH}",
        f"original_sequence_type={original_sequence_type}",
        f"original_sequence_comment={original_comment}",
        f"unchanged_valid={unchanged_valid}",
        f"unchanged_error={unchanged_error}",
        f"replaced_sequence_type={replaced_sequence_type}",
        f"parent_key_comment_after_replacement={parent_key_comment}",
        f"replaced_valid={replaced_valid}",
        f"replaced_broken_layout={bool(BROKEN_SEQUENCE.search(replaced_text))}",
        f"replaced_error={replaced_error}",
        f"plain_control_valid={plain_valid}",
        f"plain_control_error={plain_error}",
        f"in_place_control_valid={in_place_valid}",
        f"in_place_control_error={in_place_error}",
        f"causal_signature_match={causal_signature}",
        "replaced_excerpt_start",
        replaced_text.rstrip(),
        "replaced_excerpt_end",
    ]
    OUTPUT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    return 0 if causal_signature else 1


if __name__ == "__main__":
    raise SystemExit(main())
