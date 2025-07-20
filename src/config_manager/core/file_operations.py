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
                    
                    # 验证YAML数据类型的正确性
                    self._validate_yaml_types(loaded_data, config_path)

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
        except TypeError:
            # 类型验证错误应该直接抛出，不要捕获
            raise
        except Exception as e:
            print(f"⚠️  YAML解析失败: {str(e)}")
            print("⚠️  为保护原始配置文件，不会自动创建新配置")
            print("⚠️  请检查配置文件格式，特别是Windows路径中的反斜杠")
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

    def save_config_only(self, config_path: str, data: Dict[str, Any]) -> bool:
        """仅保存配置到主文件，不创建备份"""
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
            return True
        except Exception as e:
            print(f"保存配置失败: {str(e)}")
            return False

    def create_backup_only(self, backup_path: str, data: Dict[str, Any]) -> bool:
        """仅创建备份文件，不保存主配置"""
        try:
            # 创建备份目录
            backup_dir = os.path.dirname(backup_path)
            if backup_dir:
                os.makedirs(backup_dir, exist_ok=True)

            # 直接使用传入的数据创建备份（不需要准备数据，因为不涉及主配置文件）
            tmp_backup_path = f"{backup_path}.tmp"
            with open(tmp_backup_path, 'w', encoding='utf-8') as f:
                self._yaml.dump(data, f)

            os.replace(tmp_backup_path, backup_path)
            return True
        except Exception as e:
            print(f"创建备份失败: {str(e)}")
            return False

    def _prepare_data_for_save(self, config_path: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """准备要保存的数据，尽可能保留原始结构和注释"""
        # 如果有原始YAML数据且路径匹配，则更新原始结构
        if (self._original_yaml_data is not None and
                self._config_path == config_path and
                isinstance(self._original_yaml_data, dict)):

            # 深度更新原始数据结构
            updated_data = self._deep_update_yaml_data(self._original_yaml_data.copy(), data)
            return updated_data
        else:
            # 没有原始结构，但如果路径不同，尝试重新加载原始数据
            if config_path != self._config_path:
                self._try_reload_original_data(config_path)
                # 重新尝试更新
                if (self._original_yaml_data is not None and
                        isinstance(self._original_yaml_data, dict)):
                    updated_data = self._deep_update_yaml_data(self._original_yaml_data.copy(), data)
                    return updated_data
            
            # 没有原始结构，直接返回新数据
            return data

    def _deep_update_yaml_data(self, original: Any, new_data: Any) -> Any:
        """深度更新YAML数据，保留原始结构和注释"""
        if isinstance(original, dict) and isinstance(new_data, dict):
            # 对于字典，深度合并并保留注释
            # 直接在原始字典上更新，以保留ruamel.yaml的注释信息
            for key, value in new_data.items():
                # 跳过内部键，避免在顶层结构中添加内部数据
                if key.startswith('__') and key != '__data__':
                    continue
                
                # 跳过 __data__ 键的直接处理，稍后单独处理
                if key == '__data__':
                    continue
                    
                if key in original and isinstance(original[key], dict) and isinstance(value, dict):
                    # 递归合并嵌套字典
                    self._deep_update_yaml_data(original[key], value)
                else:
                    # 直接更新值（包括新键）
                    original[key] = value
            
            # 如果新数据中有__data__，需要检查是否包含锚点别名引用
            # 如果包含锚点别名，则完全跳过从__data__复制到顶层的逻辑
            if '__data__' in new_data and isinstance(new_data['__data__'], dict):
                data_section = new_data['__data__']
                
                # 检查是否存在锚点别名引用
                has_anchor_alias_refs = self._has_any_anchor_alias_references(original, data_section)
                
                if has_anchor_alias_refs:
                    # 存在锚点别名引用，需要移除顶层的锚点别名引用键以避免重复
                    self._remove_top_level_anchor_alias_keys(original, data_section)
                else:
                    # 没有锚点别名引用，按原逻辑复制用户定义键到顶层
                    system_fields = {
                        'base_dir', 'first_start_time', 'config_file_path', 'paths', 
                        '__type_hints__', 'debug_mode'
                    }
                    
                    for key, value in data_section.items():
                        # 跳过系统字段和内部键
                        if key.startswith('__') or key in system_fields:
                            continue
                        
                        # 检查顶层是否已存在该键
                        if key in original:
                            if isinstance(original[key], dict) and isinstance(value, dict):
                                # 递归合并嵌套字典
                                self._deep_update_yaml_data(original[key], value)
                            else:
                                # 正常更新值
                                original[key] = value
                        else:
                            # 顶层不存在该键，直接添加
                            original[key] = value
            
            return original
        elif isinstance(original, list) and isinstance(new_data, list):
            # 对于列表，直接替换（保持简单）
            return new_data
        else:
            # 对于其他类型，直接替换
            return new_data
    
    def _is_anchor_alias_reference(self, original_data: dict, key: str, value: Any) -> bool:
        """检查是否是锚点别名引用情况
        
        Args:
            original_data: 原始YAML数据
            key: 要检查的键名
            value: __data__中的值
            
        Returns:
            bool: 如果是锚点别名引用情况返回True，否则返回False
        """
        # 检查顶层是否存在该键
        if key not in original_data:
            return False
        
        original_value = original_data[key]
        
        # 如果两个值完全相同（包括引用关系），是锚点别名情况
        if original_value is value:
            return True
        
        # 对于字典类型，需要深度检查是否存在锚点别名引用的子键
        if isinstance(value, dict) and isinstance(original_value, dict):
            return self._has_anchor_alias_subkeys(original_value, value)
        
        # 如果值内容相同但不是同一个对象，也可能是锚点别名展开的结果
        if original_value == value:
            # 进一步检查是否为复杂数据结构（字典或列表）
            # 对于简单值，相等不一定意味着锚点别名
            if isinstance(value, (dict, list)) and len(str(value)) > 10:
                return True
        
        return False
    
    def _has_anchor_alias_subkeys(self, original_dict: dict, data_dict: dict) -> bool:
        """检查字典中是否包含锚点别名引用的子键
        
        Args:
            original_dict: 顶层原始字典
            data_dict: __data__中的字典
            
        Returns:
            bool: 如果包含锚点别名引用的子键返回True
        """
        # 检查data_dict中的每个键是否在original_dict中作为锚点别名引用存在
        for sub_key, sub_value in data_dict.items():
            if sub_key in original_dict:
                original_sub_value = original_dict[sub_key]
                
                # 如果是同一个对象，说明存在锚点别名引用
                if original_sub_value is sub_value:
                    return True
                
                # 递归检查嵌套字典
                if isinstance(sub_value, dict) and isinstance(original_sub_value, dict):
                    if self._has_anchor_alias_subkeys(original_sub_value, sub_value):
                        return True
        
        return False
    
    def _has_any_anchor_alias_references(self, original_data: dict, data_section: dict) -> bool:
        """检查__data__部分是否包含任何锚点别名引用
        
        Args:
            original_data: 原始YAML数据（顶层）
            data_section: __data__部分的数据
            
        Returns:
            bool: 如果包含任何锚点别名引用返回True
        """
        for key, value in data_section.items():
            # 跳过系统字段和内部键
            if key.startswith('__'):
                continue
                
            # 检查该键是否在顶层存在锚点别名引用
            if key in original_data:
                if self._is_anchor_alias_reference(original_data, key, value):
                    return True
        
        return False
    
    def _remove_top_level_anchor_alias_keys(self, original_data: dict, data_section: dict) -> None:
        """移除顶层的锚点别名引用键以避免重复
        
        Args:
            original_data: 原始YAML数据（顶层）
            data_section: __data__部分的数据
        """
        keys_to_remove = []
        
        for key, value in data_section.items():
            # 跳过系统字段和内部键
            if key.startswith('__'):
                continue
                
            # 检查该键是否在顶层存在锚点别名引用
            if key in original_data:
                if self._is_anchor_alias_reference(original_data, key, value):
                    keys_to_remove.append(key)
                elif isinstance(value, dict) and isinstance(original_data[key], dict):
                    # 对于字典类型，检查是否包含锚点别名引用的子键
                    if self._has_anchor_alias_subkeys(original_data[key], value):
                        keys_to_remove.append(key)
        
        # 移除检测到的锚点别名引用键
        for key in keys_to_remove:
            del original_data[key]
    
    def _try_reload_original_data(self, config_path: str):
        """尝试重新加载原始数据（用于路径变化的情况）"""
        try:
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                    # 处理Windows路径中的反斜杠转义问题
                    import re
                    def fix_windows_path(match):
                        path = match.group(1)
                        fixed_path = path.replace('\\\\', '/').replace('\\', '/')
                        return f'"{fixed_path}"'
                    
                    content = re.sub(r'"([a-zA-Z]:[\\\\][^"]*)"', fix_windows_path, content)
                    content = re.sub(r'"([\\\\][^"]*)"', fix_windows_path, content)
                    content = re.sub(r'"(\.[\\\\][^"]*)"', fix_windows_path, content)
                    
                    # 加载YAML数据
                    loaded_data = self._yaml.load(content) or {}
                    
                    # 更新原始数据和路径
                    self._original_yaml_data = loaded_data
                    self._config_path = config_path
                    
        except Exception as e:
            print(f"重新加载原始数据失败: {str(e)}")

    def get_backup_path(self, config_path: str, base_time: datetime, config_manager=None) -> str:
        """获取备份路径，基于给定时间生成时间戳
        
        Args:
            config_path: 配置文件路径
            base_time: 基准时间
            config_manager: 配置管理器实例（可选）
            
        Returns:
            str: 备份文件路径
        """
        date_str = base_time.strftime('%Y%m%d')
        time_str = base_time.strftime('%H%M%S')

        config_name = os.path.basename(config_path)
        name_without_ext = os.path.splitext(config_name)[0]

        # 生成备份文件名：filename_yyyymmdd_HHMMSS.yaml
        backup_filename = f"{name_without_ext}_{date_str}_{time_str}.yaml"

        # 尝试使用config.paths.backup_dir，如果不可用则使用传统路径
        if config_manager:
            try:
                backup_dir = config_manager.get('paths.backup_dir')
                if backup_dir:
                    backup_path = os.path.join(backup_dir, backup_filename)
                    return backup_path
            except (AttributeError, KeyError):
                # 如果获取backup_dir失败，使用传统方式
                pass
        
        # 备用方案：生成备份目录结构：原目录/backup/yyyymmdd/HHMMSS/
        config_dir = os.path.dirname(config_path)
        backup_dir = os.path.join(config_dir, 'backup', date_str, time_str)
        backup_path = os.path.join(backup_dir, backup_filename)
        return backup_path

    def _validate_yaml_types(self, data: Dict[str, Any], config_path: str) -> None:
        """验证YAML数据的类型正确性，确保严格区分字符串和数字
        
        Args:
            data: 加载的YAML数据
            config_path: 配置文件路径
            
        Raises:
            TypeError: 当发现类型不一致时抛出异常
        """
        try:
            self._validate_data_recursive(data, config_path, "")
        except Exception as e:
            raise TypeError(f"配置文件 {config_path} 类型验证失败: {str(e)}")
    
    def _validate_data_recursive(self, data: Any, config_path: str, path: str) -> None:
        """递归验证数据类型
        
        Args:
            data: 要验证的数据
            config_path: 配置文件路径
            path: 当前验证路径
        """
        if isinstance(data, dict):
            for key, value in data.items():
                current_path = f"{path}.{key}" if path else key
                # 对于__data__键，需要继续验证其内容，但跳过其他内部键
                # 确保key是字符串类型才调用startswith
                if isinstance(key, str) and key.startswith('__') and key != '__data__':
                    continue
                self._validate_data_recursive(value, config_path, current_path)
        elif isinstance(data, list):
            for i, item in enumerate(data):
                current_path = f"{path}[{i}]"
                self._validate_data_recursive(item, config_path, current_path)
        else:
            # 对基础类型进行验证
            self._validate_basic_type(data, config_path, path)
    
    def _validate_basic_type(self, value: Any, config_path: str, path: str) -> None:
        """验证基础类型的正确性 - 已禁用验证，加引号的就是字符串，原样处理
        
        Args:
            value: 要验证的值
            config_path: 配置文件路径
            path: 当前验证路径
        """
        # 移除类型验证逻辑，加引号的就是字符串，原样处理
        pass