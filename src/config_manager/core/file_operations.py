# src/config_manager/core/file_operations.py
from __future__ import annotations
from datetime import datetime

import os
from ruamel.yaml import YAML
from typing import Dict, Any, Optional
from ..utils import lock_file, unlock_file


class FileOperations:
    """文件操作管理器"""

    def __init__(self):
        """初始化文件操作管理器"""
        # 创建YAML实例，配置为保留注释和格式
        self._yaml = YAML()
        self._yaml.preserve_quotes = True
        self._yaml.map_indent = 2
        self._yaml.sequence_indent = 4
        self._yaml.sequence_dash_offset = 2
        self._yaml.default_flow_style = False

        # 存储原始YAML结构以保留注释
        self._original_yaml_data = None
        self._config_path = None
        return

    def load_config(self, config_path: str, auto_create: bool, call_chain_tracker) -> Optional[Dict]:
        """加载配置文件"""
        # 检查调用链显示开关
        from ..config_manager import ENABLE_CALL_CHAIN_DISPLAY

        if not os.path.exists(config_path):
            if auto_create:
                print(f"配置文件不存在，创建新配置: {config_path}")

                # 根据开关决定是否显示调用链
                if ENABLE_CALL_CHAIN_DISPLAY:
                    try:
                        call_chain = call_chain_tracker.get_call_chain()
                        print(f"创建配置调用链: {call_chain}")
                    except Exception as e:
                        print(f"获取创建调用链失败: {e}")

                # 创建空配置并保存
                empty_data = {'__data__': {}, '__type_hints__': {}}
                self.save_config(config_path, empty_data)
                return empty_data
            else:
                print(f"配置文件不存在: {config_path}")
                return None

        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                lock_file(f)
                try:
                    # 读取文件内容
                    content = f.read()

                    # 处理Windows路径中的反斜杠转义问题
                    import re
                    def fix_windows_path(match):
                        path = match.group(1)
                        # 将双反斜杠替换为单斜杠，避免转义问题
                        # 先处理双反斜杠（\\\\），再处理单反斜杠（\\）
                        fixed_path = path.replace('\\\\', '/').replace('\\', '/')
                        return f'"{fixed_path}"'

                    # 修复常见的Windows路径转义问题
                    # 匹配双引号中的Windows路径（包括绝对路径和相对路径）
                    content = re.sub(r'"([a-zA-Z]:[\\\\][^"]*)"', fix_windows_path, content)
                    content = re.sub(r'"([\\\\][^"]*)"', fix_windows_path, content)  # 以反斜杠开头的路径
                    content = re.sub(r'"(\.[\\\\][^"]*)"', fix_windows_path, content)  # 相对路径如 ".\\logs"

                    # 加载修复后的YAML数据
                    loaded_data = self._yaml.load(content) or {}

                    # 保存原始YAML结构和路径，用于后续保存时保留注释
                    self._original_yaml_data = loaded_data
                    self._config_path = config_path
                finally:
                    unlock_file(f)

            # 根据开关决定是否显示加载调用链
            print(f"配置已从 {config_path} 加载")
            if ENABLE_CALL_CHAIN_DISPLAY:
                try:
                    call_chain = call_chain_tracker.get_call_chain()
                    print(f"加载配置调用链: {call_chain}")
                except Exception as e:
                    print(f"获取加载调用链失败: {e}")
                    # 尝试获取详细调试信息
                    try:
                        debug_info = call_chain_tracker.get_detailed_call_info()
                        print(f"调用链调试信息: {debug_info}")
                    except Exception as debug_e:
                        print(f"获取调试信息也失败: {debug_e}")

            return loaded_data
        except Exception as e:
            print(f"⚠️  YAML解析失败: {str(e)}")
            print(f"⚠️  为保护原始配置文件，不会自动创建新配置")
            print(f"⚠️  请检查配置文件格式，特别是Windows路径中的反斜杠")
            return None

    def save_config(self, config_path: str, data: Dict[str, Any], backup_path: str = None) -> bool:
        """保存配置到文件，保留注释和格式"""
        try:
            # 保存到主配置文件
            original_dir = os.path.dirname(config_path)
            if original_dir:
                os.makedirs(original_dir, exist_ok=True)

            # 准备要保存的数据
            data_to_save = self._prepare_data_for_save(config_path, data)

            tmp_original_path = f"{config_path}.tmp"
            with open(tmp_original_path, 'w', encoding='utf-8') as f:
                self._yaml.dump(data_to_save, f)

            os.replace(tmp_original_path, config_path)

            # 创建备份（如果提供了备份路径）
            if backup_path:
                try:
                    backup_dir = os.path.dirname(backup_path)
                    if backup_dir:
                        os.makedirs(backup_dir, exist_ok=True)

                    tmp_backup_path = f"{backup_path}.tmp"
                    with open(tmp_backup_path, 'w', encoding='utf-8') as f:
                        self._yaml.dump(data_to_save, f)

                    os.replace(tmp_backup_path, backup_path)
                    print(f"配置已自动备份到 {backup_path}")
                except Exception as backup_error:
                    print(f"备份保存失败（不影响主配置文件）: {str(backup_error)}")

            return True
        except Exception as e:
            print(f"保存配置失败: {str(e)}")
            return False

    def _prepare_data_for_save(self, config_path: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """准备要保存的数据，尽可能保留原始结构和注释"""
        # 如果有原始YAML数据且路径匹配，则更新原始结构
        if (self._original_yaml_data is not None and
                self._config_path == config_path and
                isinstance(self._original_yaml_data, dict)):

            # 深度更新原始数据结构
            updated_data = self._deep_update_yaml_data(self._original_yaml_data, data)
            return updated_data
        else:
            # 没有原始结构，直接返回新数据
            return data

    def _deep_update_yaml_data(self, original: Any, new_data: Any) -> Any:
        """深度更新YAML数据，保留原始结构和注释"""
        if isinstance(original, dict) and isinstance(new_data, dict):
            # 对于字典，逐个更新键值
            for key, value in new_data.items():
                if key in original:
                    # 递归更新已存在的键
                    original[key] = self._deep_update_yaml_data(original[key], value)
                else:
                    # 添加新键
                    original[key] = value
            return original
        elif isinstance(original, list) and isinstance(new_data, list):
            # 对于列表，直接替换（保持简单）
            return new_data
        else:
            # 对于其他类型，直接替换
            return new_data

    def get_backup_path(self, config_path: str, base_time: datetime) -> str:
        """获取备份路径，基于给定时间生成时间戳"""
        date_str = base_time.strftime('%Y%m%d')
        time_str = base_time.strftime('%H%M%S')

        # 基于当前配置文件路径生成备份路径
        config_dir = os.path.dirname(config_path)
        config_name = os.path.basename(config_path)
        name_without_ext = os.path.splitext(config_name)[0]

        # 生成备份文件名：filename_yyyymmdd_HHMMSS.yaml
        backup_filename = f"{name_without_ext}_{date_str}_{time_str}.yaml"

        # 生成备份目录结构：原目录/backup/yyyymmdd/HHMMSS/
        backup_dir = os.path.join(config_dir, 'backup', date_str, time_str)
        backup_path = os.path.join(backup_dir, backup_filename)
        return backup_path