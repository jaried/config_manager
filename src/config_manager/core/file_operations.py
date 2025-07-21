# src/config_manager/core/file_operations.py
from __future__ import annotations
from datetime import datetime

import os
import logging
from ruamel.yaml import YAML
from typing import Dict, Any, Optional
from ..utils import lock_file, unlock_file

logger = logging.getLogger(__name__)


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
            # 检测是否是原始格式到标准格式的转换
            is_raw_to_standard = ('__data__' not in original and '__data__' in new_data)
            
            if is_raw_to_standard:
                # 特殊处理：原始格式转标准格式，采用保守策略保留注释
                # print("🔧 检测到原始格式到标准格式转换，采用注释保留策略")
                return self._convert_raw_to_standard_preserving_comments(original, new_data)
            else:
                # 标准的深度合并，保留ruamel.yaml的注释信息
                for key, value in new_data.items():
                    if key in original and isinstance(original[key], dict) and isinstance(value, dict):
                        # 递归合并嵌套字典
                        self._deep_update_yaml_data(original[key], value)
                    else:
                        # 直接更新值（包括新键）
                        original[key] = value
                
                # 移除顶层重复键
                if '__data__' in new_data and isinstance(new_data['__data__'], dict):
                    self._remove_all_duplicate_keys_from_top_level(original, new_data['__data__'])
            
            return original
        elif isinstance(original, list) and isinstance(new_data, list):
            # 对于列表，直接替换（保持简单）
            return new_data
        else:
            # 对于其他类型，直接替换
            return new_data
    
    def _convert_raw_to_standard_preserving_comments(self, original: dict, new_data: dict) -> dict:
        """将原始格式转换为标准格式，最大程度保留注释"""
        # 策略：保持原始结构，只更新值，在末尾添加新节点
        
        # 获取新数据中的 __data__ 内容
        data_section = new_data.get('__data__', {})
        type_hints_section = new_data.get('__type_hints__', {})
        
        # 更新原始结构中已存在的键值
        for key, value in data_section.items():
            if key in original:
                if isinstance(original[key], dict) and isinstance(value, dict):
                    # 递归更新嵌套字典
                    self._deep_update_yaml_data(original[key], value)
                else:
                    # 更新值
                    original[key] = value
        
        # 添加新的键到原始结构（这些键在原始文件中不存在，但排除系统键）
        system_keys = {'__data__', '__type_hints__'}
        for key, value in data_section.items():
            if key not in original and key not in system_keys:
                original[key] = value
        
        # 在末尾添加 __data__ 节点（只包含非系统键的配置数据）
        # 过滤掉系统键，避免数据结构污染
        system_keys = {'__data__', '__type_hints__'}
        clean_data_section = {k: v for k, v in data_section.items() if k not in system_keys}
        original['__data__'] = clean_data_section
        
        # 添加 __type_hints__ 节点
        if type_hints_section:
            original['__type_hints__'] = type_hints_section
        elif '__type_hints__' not in original:
            original['__type_hints__'] = {}
        
        # print(f"🔧 原始格式转换完成，保留了原始键顺序和注释")
        return original
    
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
        """移除YAML锚点别名展开产生的重复键，保留锚点定义
        
        专门处理YAML锚点别名(&id001, *id001)展开产生的重复键：
        - 保留锚点定义（__data__中的，第1个）
        - 删除别名展开（顶层的，第2个及后续）
        - 其他非锚点相关的重复键不删除，可能有特殊用途
        
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
            
            # 检查是否在__data__中存在
            if key in data_section:
                top_level_value = original_data[key]
                data_section_value = data_section[key]
                
                # 只有当值完全相同时才可能是锚点别名展开产生的重复
                if self._are_values_identical(top_level_value, data_section_value):
                    # 这是锚点别名展开产生的重复：
                    # 保留锚点定义(__data__中的，第1个)，删除别名展开(顶层的，第2个)
                    keys_to_remove.append(key)
                    print(f"删除锚点别名展开重复: '{key}' (保留__data__中的锚点定义)")
                else:
                    # 值不同，保留顶层的键（非锚点别名重复，可能有特殊用途）
                    print(f"保留顶层键 '{key}': 值与__data__中的不同，非锚点别名重复")
        
        # 移除确认的锚点别名重复键
        for key in keys_to_remove:
            del original_data[key]
            
        # 记录移除的键用于调试
        if keys_to_remove:
            print(f"移除锚点别名重复键: {keys_to_remove}")
        else:
            print("未发现锚点别名重复键需要删除")
    
    def _are_values_identical(self, value1: Any, value2: Any) -> bool:
        """比较两个值是否完全相同，用于判断是否为真正的重复
        
        Args:
            value1: 第一个值
            value2: 第二个值
            
        Returns:
            bool: 如果值完全相同返回True，否则返回False
        """
        try:
            # 首先检查是否是同一个对象引用（锚点别名情况）
            if value1 is value2:
                return True
            
            # 检查基本类型的相等性
            if type(value1) is not type(value2):
                return False
            
            # 对于字典类型，递归比较
            if isinstance(value1, dict) and isinstance(value2, dict):
                if set(value1.keys()) != set(value2.keys()):
                    return False
                for key in value1.keys():
                    if not self._are_values_identical(value1[key], value2[key]):
                        return False
                return True
            
            # 对于列表类型，逐一比较元素
            if isinstance(value1, list) and isinstance(value2, list):
                if len(value1) != len(value2):
                    return False
                for i in range(len(value1)):
                    if not self._are_values_identical(value1[i], value2[i]):
                        return False
                return True
            
            # 对于基本类型，直接比较值
            return value1 == value2
            
        except Exception:
            # 比较出现异常时，保守起见认为不相同
            return False
    
    def _remove_duplicate_keys_from_yaml_file(self, file_path: str) -> None:
        """直接编辑YAML文件，删除重复键，特别处理__data__和顶层的重复情况"""
        # 检查是否为测试模式，如果是则减少详细日志输出
        is_test_mode = '/tests/' in file_path or '/tmp/' in file_path
        # if not is_test_mode:
        #     print(f"🔧 开始YAML文件后处理: {file_path}")
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # if not is_test_mode:
            #     print(f"🔧 读取到 {len(lines)} 行内容")
            
            # 记录键的出现情况：键名 -> [(行号, 层级, 所在段)]
            key_occurrences = {}
            lines_to_remove = set()
            current_section = None
            protected_keys = {'__data__', '__type_hints__'}
            
            # 第一轮：收集所有键的出现信息，构建完整的层级路径
            path_stack = []  # 维护当前的路径栈
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
                    
                    # 跳过锚点和别名定义行
                    if '&' in key or '*' in key:
                        # if not is_test_mode:
                        #     print(f"🔧 跳过锚点/别名键: {key} (第{i+1}行)")
                        continue
                    
                    # 检查值部分是否包含别名引用
                    colon_pos = stripped_line.find(':')
                    if colon_pos != -1 and colon_pos + 1 < len(stripped_line):
                        value_part = stripped_line[colon_pos + 1:].strip()
                        if value_part.startswith('*'):
                            # if not is_test_mode:
                            #     print(f"🔧 跳过别名引用: {key}: {value_part} (第{i+1}行)")
                            continue
                    
                    # 根据缩进级别调整路径栈
                    target_depth = indent_level // 2  # 假设每级缩进2个空格
                    path_stack = path_stack[:target_depth]
                    path_stack.append(key)
                    
                    # 构建完整的键路径
                    full_key_path = '.'.join(path_stack)
                    
                    # 更新当前段（只用于向后兼容）
                    if indent_level == 0:
                        current_section = key
                    
                    # 使用完整路径作为键标识
                    if full_key_path not in key_occurrences:
                        key_occurrences[full_key_path] = []
                    
                    key_occurrences[full_key_path].append((i, indent_level, current_section, key))
                    # if not is_test_mode:
                    #     print(f"🔧 发现键路径: '{full_key_path}' -> '{key}' (第{i+1}行, 缩进{indent_level})")
            
            # 第二轮：分析重复情况并标记删除
            for full_key_path, occurrences in key_occurrences.items():
                if len(occurrences) <= 1:
                    continue  # 没有重复
                
                # 提取基础键名（路径的最后一部分）
                base_key = full_key_path.split('.')[-1]
                
                # 跳过受保护的系统键在顶层的保护
                if base_key in protected_keys:
                    # 但是要检查是否有__data__内部和顶层的重复
                    data_occurrences = [(line_no, indent, section, key) for line_no, indent, section, key in occurrences 
                                      if section == '__data__' and indent > 0]
                    top_level_occurrences = [(line_no, indent, section, key) for line_no, indent, section, key in occurrences 
                                           if indent == 0 and section != '__data__']
                    
                    if data_occurrences and top_level_occurrences:
                        # __data__内部和顶层都有__type_hints__，删除__data__内部的（这是数据结构污染）
                        for line_no, indent, section, key in data_occurrences:
                            lines_to_remove.add(line_no)
                            self._mark_key_block_for_removal(lines, line_no, indent, lines_to_remove)
                            # print(f"❌ 删除__data__内部的系统键: {key} (第{line_no+1}行) - 保留顶层版本，修复数据结构污染")
                    continue
                
                # print(f"🔧 分析重复路径 '{full_key_path}': {len(occurrences)} 次出现")
                
                # 特殊处理first_start_time：如果出现在__data__直接子层和__data__.__type_hints__中，这是正常的
                if base_key == 'first_start_time':
                    # 检查是否是数据值和类型提示的合理组合
                    data_value_occurrences = [(line_no, indent, section, key) for line_no, indent, section, key in occurrences 
                                            if section == '__data__' and indent == 2]
                    type_hint_occurrences = [(line_no, indent, section, key) for line_no, indent, section, key in occurrences 
                                           if section == '__data__' and indent == 4]
                    top_level_occurrences = [(line_no, indent, section, key) for line_no, indent, section, key in occurrences 
                                           if indent == 0 and section != '__data__']
                    
                    # print(f"🔧 first_start_time分析: 数据值{len(data_value_occurrences)}个, 类型提示{len(type_hint_occurrences)}个, 顶层{len(top_level_occurrences)}个")
                    
                    # 删除顶层的first_start_time，保留__data__中的数据值和类型提示
                    if top_level_occurrences:
                        for line_no, indent, section, key in top_level_occurrences:
                            lines_to_remove.add(line_no)
                            self._mark_key_block_for_removal(lines, line_no, indent, lines_to_remove)
                            # print(f"❌ 删除顶层重复键: {key} (第{line_no+1}行) - 保留__data__中的版本")
                    
                    # 如果只有__data__内的数据值和类型提示，这是正常情况，不删除任何内容
                    if data_value_occurrences and type_hint_occurrences and not top_level_occurrences:
                        # print(f"✅ 保留 {base_key} 的数据值和类型提示 - 这是正常配置结构")
                        pass
                    elif data_value_occurrences and type_hint_occurrences and top_level_occurrences:
                        # print(f"✅ 保留 {base_key} 的数据值和类型提示，删除顶层重复")
                        pass
                    
                    continue
                
                # 检查是否包含YAML锚点别名标记
                has_anchor_alias = False
                for line_no, indent, section, key in occurrences:
                    line_content = lines[line_no].strip()
                    if '&' in line_content or '*' in line_content:
                        # 检查是否是真正的YAML锚点或别名标记
                        import re
                        if re.search(r'&\w+|:\s*\*\w+', line_content):
                            has_anchor_alias = True
                            print(f"🔍 检测到锚点别名标记: {line_content.strip()} (第{line_no+1}行)")
                            break
                
                if not has_anchor_alias:
                    # 非锚点别名重复，不删除，可能有特殊用途
                    print(f"🛡️  保留非锚点别名重复键: '{base_key}' - 可能有特殊用途")
                    continue
                
                # 只有检测到锚点别名标记才进行重复删除
                print(f"🎯 处理锚点别名重复键: '{base_key}'")
                
                # 检查是否存在 __data__ 内部和顶层的重复
                data_occurrences = [(line_no, indent, section, key) for line_no, indent, section, key in occurrences 
                                  if section == '__data__' and indent > 0]
                top_level_occurrences = [(line_no, indent, section, key) for line_no, indent, section, key in occurrences 
                                       if indent == 0 and section != '__data__']
                
                if data_occurrences and top_level_occurrences:
                    # __data__内部和顶层都有锚点别名：
                    # 1. 处理__data__内部的锚点定义：去掉&id001标记，保留数据
                    # 2. 删除顶层的别名引用*id001
                    
                    # 处理__data__内部的锚点定义
                    for line_no, indent, section, key in data_occurrences:
                        line_content = lines[line_no]
                        if '&' in line_content:
                            # 去掉锚点标记 &id001，保留数据
                            import re
                            cleaned_line = re.sub(r'\s*&\w+', '', line_content)
                            lines[line_no] = cleaned_line
                            # print(f"🔧 清理__data__内锚点标记: 第{line_no+1}行 去掉&标记，保留数据")
                    
                    # 删除顶层的别名引用
                    for line_no, indent, section, key in top_level_occurrences:
                        lines_to_remove.add(line_no)
                        self._mark_key_block_for_removal(lines, line_no, indent, lines_to_remove)
                        # print(f"❌ 删除顶层别名引用: {key} (第{line_no+1}行) - 删除*id001引用")
                
                elif len(occurrences) > 1:
                    # 锚点别名路径重复处理：
                    # 1. 保留第1个（锚点定义&id001），但去掉&id001标记  
                    # 2. 删除第2个及后续（别名引用*id001）
                    sorted_occurrences = sorted(occurrences, key=lambda x: x[0])  # 按行号排序
                    
                    # 处理第1个（锚点定义）：去掉&id001标记，保留数据
                    first_line_no = sorted_occurrences[0][0]
                    first_line = lines[first_line_no]
                    if '&' in first_line:
                        # 去掉锚点标记 &id001，保留数据
                        import re
                        cleaned_line = re.sub(r'\s*&\w+', '', first_line)
                        lines[first_line_no] = cleaned_line
                        # print(f"🔧 清理锚点标记: 第{first_line_no+1}行 去掉&标记，保留数据")
                    
                    # 删除第2个及后续（别名引用）
                    for line_no, indent, section, key in sorted_occurrences[1:]:
                        lines_to_remove.add(line_no)
                        self._mark_key_block_for_removal(lines, line_no, indent, lines_to_remove)
                        # print(f"❌ 删除别名引用: {key} 在路径 '{full_key_path}' (第{line_no+1}行) - 删除*id001引用")
            
            # if not is_test_mode:
            #     print(f"🔧 标记删除 {len(lines_to_remove)} 行: {sorted(lines_to_remove)}")
            
            # 删除标记的行
            if lines_to_remove:
                filtered_lines = [line for i, line in enumerate(lines) if i not in lines_to_remove]
                
                # 写回文件
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.writelines(filtered_lines)
                
                # if not is_test_mode:
                #     print(f"✅ 成功删除 {len(lines_to_remove)} 行重复内容")
            else:
                # if not is_test_mode:
                #     print(f"ℹ️  没有发现需要删除的重复键")
                pass
                
        except Exception as e:
            # print(f"❌ 删除重复键时发生错误: {e}")
            import traceback
            traceback.print_exc()
    
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