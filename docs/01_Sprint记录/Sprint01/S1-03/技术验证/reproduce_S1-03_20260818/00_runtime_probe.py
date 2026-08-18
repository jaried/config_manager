"""Verify the interpreter and bind imports to the S1-03 worktree source."""

from __future__ import annotations

import importlib.metadata
import os
from pathlib import Path
import sys


WORKTREE = Path(__file__).resolve().parents[6]
SOURCE_ROOT = WORKTREE / "src"
sys.path.insert(0, str(SOURCE_ROOT))

import config_manager  # noqa: E402


OUTPUT_PATH = Path(__file__).resolve().with_name("00_runtime_probe_output.txt")
lines = [
    f"sys.executable={sys.executable}",
    f"os.name={os.name}",
    f"python_version={sys.version.split()[0]}",
    f"worktree={WORKTREE}",
    f"source_root={SOURCE_ROOT}",
    f"config_manager_file={Path(config_manager.__file__).resolve()}",
    f"ruamel_yaml_version={importlib.metadata.version('ruamel.yaml')}",
    f"is_debug_version={importlib.metadata.version('is-debug')}",
]
OUTPUT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
print("\n".join(lines))

if SOURCE_ROOT.resolve() not in Path(config_manager.__file__).resolve().parents:
    raise RuntimeError("config_manager import did not resolve to the S1-03 worktree")
