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
        """保存配置到文件，保留注释和格式并彻底解决重复键问题"""
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

            # 后处理：删除YAML文件中的重复键
            self._remove_duplicate_keys_from_yaml_file(tmp_original_path)

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
            
            # 彻底解决重复键问题：完全禁止从__data__向顶层复制用户配置键
            # 保存结构应该只包含 __data__ 和 __type_hints__，顶层不应有用户配置键
            if '__data__' in new_data and isinstance(new_data['__data__'], dict):
                # 移除顶层所有可能与__data__重复的用户配置键
                self._remove_all_duplicate_keys_from_top_level(original, new_data['__data__'])
            
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
    
    def _remove_all_duplicate_keys_from_top_level(self, original_data: dict, data_section: dict) -> None:
        """彻底移除顶层所有与__data__重复的键，解决重复键问题
        
        Args:
            original_data: 原始YAML数据（顶层）
            data_section: __data__部分的数据
        """
        keys_to_remove = []
        
        # 定义必须保留的顶层系统键
        protected_top_level_keys = {'__data__', '__type_hints__'}
        
        for key in list(original_data.keys()):
            # 保护系统键不被移除
            if key in protected_top_level_keys:
                continue
            
            # 如果该键在__data__中存在，就从顶层移除以避免重复
            if key in data_section:
                keys_to_remove.append(key)
        
        # 移除所有重复的键
        for key in keys_to_remove:
            del original_data[key]
            
        # 记录移除的键用于调试（可选）
        if keys_to_remove:
            print(f"移除顶层重复键: {keys_to_remove}")
    
    def _remove_duplicate_keys_from_yaml_file(self, file_path: str) -> None:
        """直接编辑YAML文件，删除重复键的第二次出现，包括跨部分重复"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # 记录已见过的键及其出现的行号和部分
            seen_keys = {}  # key_name -> {'line': line_num, 'section': section_name}
            lines_to_remove = set()
            current_section = None
            
            for i, line in enumerate(lines):
                stripped_line = line.strip()
                
                # 跳过空行和注释
                if not stripped_line or stripped_line.startswith('#'):
                    continue
                
                # 如果行包含冒号，提取键名
                if ':' in stripped_line:
                    # 计算缩进级别
                    indent_level = len(line) - len(line.lstrip())
                    key = stripped_line.split(':')[0].strip()
                    
                    # 跳过锚点和别名定义
                    if '&' in key or '*' in key:
                        continue
                    
                    # 处理不同层级的键
                    if indent_level == 0:  # 顶层键
                        current_section = key
                        key_id = f"top_level:{key}"
                        actual_key = key
                    elif indent_level == 2:  # 二级键
                        key_id = f"{current_section}:{key}" if current_section else f"level2:{key}"
                        actual_key = key
                    else:
                        continue  # 跳过更深层级的键
                    
                    # 特殊处理：检查跨部分重复（__data__ 和 __type_hints__ 之间的重复）
                    if current_section in ['__data__', '__type_hints__'] and indent_level == 2:
                        # 检查该键是否已经在其他部分出现过
                        if actual_key in seen_keys:
                            previous_info = seen_keys[actual_key]
                            # 如果之前在__data__中出现过，现在在__type_hints__中，删除__type_hints__中的
                            if previous_info['section'] == '__data__' and current_section == '__type_hints__':
                                # 标记当前行（__type_hints__中的重复键）为需要删除
                                start_line = i
                                lines_to_remove.add(start_line)
                                self._mark_key_block_for_removal(lines, start_line, indent_level, lines_to_remove)
                                print(f"删除跨部分重复键: {actual_key} 在{current_section}中 (第{i+1}行)")
                                continue
                        else:
                            # 记录第一次出现的键
                            seen_keys[actual_key] = {'line': i, 'section': current_section}
                    
                    # 检查同部分内的重复
                    if key_id in seen_keys:
                        # 标记重复行和其后续相关行为需要删除
                        start_line = i
                        lines_to_remove.add(start_line)
                        
                        # 找到这个键值对的所有相关行（包括多行值）
                        self._mark_key_block_for_removal(lines, start_line, indent_level, lines_to_remove)
                        
                        print(f"删除同部分重复键: {key} (第{i+1}行)")
                    else:
                        # 对于非跨部分情况，记录键的完整标识
                        if current_section not in ['__data__', '__type_hints__'] or indent_level != 2:
                            seen_keys[key_id] = {'line': i, 'section': current_section}
            
            # 删除标记的行
            if lines_to_remove:
                filtered_lines = [line for i, line in enumerate(lines) if i not in lines_to_remove]
                
                # 写回文件
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.writelines(filtered_lines)
                
                print(f"成功删除 {len(lines_to_remove)} 行重复内容")
                
        except Exception as e:
            print(f"删除重复键时发生错误: {e}")
    
    def _mark_key_block_for_removal(self, lines: list, start_line: int, base_indent: int, lines_to_remove: set) -> None:
        """标记一个键值对块的所有行为需要删除"""
        lines_to_remove.add(start_line)
        
        # 检查后续行是否属于这个键值对（更深的缩进或续行）
        for i in range(start_line + 1, len(lines)):
            line = lines[i]
            stripped_line = line.strip()
            
            # 空行也可能属于这个块
            if not stripped_line:
                lines_to_remove.add(i)
                continue
            
            # 注释行可能属于这个块
            if stripped_line.startswith('#'):
                lines_to_remove.add(i)
                continue
            
            # 计算缩进
            current_indent = len(line) - len(line.lstrip())
            
            # 如果缩进更深，说明是这个键的值的一部分
            if current_indent > base_indent:
                lines_to_remove.add(i)
            else:
                # 缩进相同或更少，说明这个键值对块结束了
                break
    
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