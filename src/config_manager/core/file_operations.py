# src/config_manager/core/file_operations.py
from __future__ import annotations

from datetime import datetime
import os
import re
import tempfile
from typing import Any, Dict, Optional

from ..utils import lock_file, unlock_file
from ..yaml_codec import dump_yaml, load_yaml, semantically_equal


class FileOperations:
    """Load and transactionally persist configuration files."""

    @staticmethod
    def _repair_windows_paths(content: str) -> str:
        def fix_windows_path(match: re.Match[str]) -> str:
            path = match.group(1)
            return f'"{path.replace(chr(92) * 2, "/").replace(chr(92), "/")}"'

        content = re.sub(r'"([a-zA-Z]:[\\][^"]*)"', fix_windows_path, content)
        content = re.sub(r'"([\\][^"]*)"', fix_windows_path, content)
        return re.sub(r'"(\.[\\][^"]*)"', fix_windows_path, content)

    def load_config(
        self, config_path: str, auto_create: bool, call_chain_tracker
    ) -> Optional[Dict]:
        """Load a configuration file without retaining parser state."""
        from ..config_manager import ENABLE_CALL_CHAIN_DISPLAY

        if not os.path.exists(config_path):
            if not auto_create:
                print(f"配置文件不存在: {config_path}")
                return None
            print(f"配置文件不存在，创建新配置: {config_path}")
            if ENABLE_CALL_CHAIN_DISPLAY:
                try:
                    print(f"创建配置调用链: {call_chain_tracker.get_call_chain()}")
                except Exception as error:
                    print(f"获取创建调用链失败: {type(error).__name__}")
            empty_data = {"__data__": {}, "__type_hints__": {}}
            self.save_config(config_path, empty_data)
            return empty_data

        try:
            with open(config_path, "r", encoding="utf-8") as stream:
                lock_file(stream)
                try:
                    content = stream.read()
                finally:
                    unlock_file(stream)
            loaded_data = load_yaml(self._repair_windows_paths(content))
            if loaded_data is None:
                loaded_data = {}

            print(f"配置已从 {config_path} 加载")
            if ENABLE_CALL_CHAIN_DISPLAY:
                try:
                    print(f"加载配置调用链: {call_chain_tracker.get_call_chain()}")
                except Exception as error:
                    print(f"获取加载调用链失败: {type(error).__name__}")
            return loaded_data
        except Exception as error:
            print(f"⚠️  YAML解析失败: {type(error).__name__}")
            print("⚠️  为保护原始配置文件，不会自动创建新配置")
            print("⚠️  请检查配置文件格式，特别是Windows路径中的反斜杠")
            return None

    def save_config(
        self, config_path: str, data: Dict[str, Any], backup_path: str = None
    ) -> bool:
        """Commit the main target, then attempt an independent best-effort backup."""
        data_to_save = self._convert_paths_config_nodes(data)
        if not self._write_candidate(config_path, data_to_save, verify_reload=True):
            return False
        if backup_path:
            if self.create_backup_only(backup_path, data_to_save):
                print(f"配置已自动备份到 {backup_path}")
            else:
                print("备份保存失败（不影响主配置文件）")
        return True

    def save_config_only(self, config_path: str, data: Dict[str, Any]) -> bool:
        """Transactionally save the main file without creating a backup."""
        data_to_save = self._convert_paths_config_nodes(data)
        return self._write_candidate(config_path, data_to_save, verify_reload=True)

    def create_backup_only(self, backup_path: str, data: Dict[str, Any]) -> bool:
        """Create an independently replaceable backup candidate."""
        data_to_save = self._convert_paths_config_nodes(data)
        return self._write_candidate(backup_path, data_to_save, verify_reload=False)

    @staticmethod
    def _write_candidate(target_path: str, data: Any, verify_reload: bool) -> bool:
        candidate_path = None
        try:
            encoded = dump_yaml(data)
            target_path = os.path.abspath(target_path)
            target_dir = os.path.dirname(target_path)
            os.makedirs(target_dir, exist_ok=True)
            descriptor, candidate_path = tempfile.mkstemp(
                prefix=f".{os.path.basename(target_path)}.",
                suffix=".tmp",
                dir=target_dir,
            )
            os.close(descriptor)
            with open(candidate_path, "w", encoding="utf-8", newline="\n") as stream:
                stream.write(encoded)

            if verify_reload:
                with open(candidate_path, "r", encoding="utf-8") as stream:
                    candidate_data = load_yaml(stream.read())
                if not semantically_equal(candidate_data, data):
                    return False

            os.replace(candidate_path, target_path)
            candidate_path = None
            return True
        except Exception as error:
            print(f"保存配置失败: {type(error).__name__}")
            return False
        finally:
            if candidate_path and os.path.exists(candidate_path):
                try:
                    os.unlink(candidate_path)
                except OSError:
                    pass

    def _convert_paths_config_nodes(self, data: Any) -> Any:
        """Recursively convert exact PathsConfigNode instances to plain dicts."""
        from .dynamic_paths import PathsConfigNode

        if isinstance(data, PathsConfigNode):
            return self._convert_paths_config_nodes(dict(data._data))
        if type(data) is dict:
            return {
                key: self._convert_paths_config_nodes(value)
                for key, value in data.items()
            }
        if type(data) is list:
            return [self._convert_paths_config_nodes(item) for item in data]
        return data

    def get_backup_path(
        self, config_path: str, base_time: datetime, config_manager=None
    ) -> str:
        """Get a timestamped backup path using configured or fallback storage."""
        date_str = base_time.strftime("%Y%m%d")
        time_str = base_time.strftime("%H%M%S")
        config_name = os.path.basename(config_path)
        name_without_ext = os.path.splitext(config_name)[0]
        backup_filename = f"{name_without_ext}_{date_str}_{time_str}.yaml"

        if config_manager:
            try:
                backup_dir = config_manager.get("paths.backup_dir")
                if backup_dir:
                    return os.path.join(backup_dir, backup_filename)
            except (AttributeError, KeyError):
                pass

        config_dir = os.path.dirname(config_path)
        backup_dir = os.path.join(config_dir, "backup", date_str, time_str)
        return os.path.join(backup_dir, backup_filename)
