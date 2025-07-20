# src/config_manager/config_node.py
from __future__ import annotations
from datetime import datetime

import copy
from collections.abc import Iterable, Mapping
from typing import Any, Dict, List

start_time = datetime.now()


class ConfigNode:
    """配置节点类，支持点操作访问"""

    def __init__(self, *args, **kwargs):
        """初始化配置节点"""
        super().__setattr__('_data', {})
        if args or kwargs:
            self.update(*args, **kwargs)
        return

    def __dir__(self) -> Iterable[str]:
        """返回属性列表以支持IDE自动补全"""
        default_attrs = list(super().__dir__())
        dict_keys = list(self._data.keys())
        unique_attrs = unique_list_order_preserved(default_attrs + dict_keys)
        return unique_attrs

    def __repr__(self) -> str:
        """返回对象的字符串表示形式"""
        class_name = self.__class__.__name__
        repr_str = f"{class_name}({self._data})"
        return repr_str

    def __getattr__(self, name: str) -> Any:
        """通过属性访问值（属性不存在时抛出AttributeError）"""
        if '_data' not in super().__getattribute__('__dict__'):
            raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")

        data = super().__getattribute__('_data')
        
        # 特殊处理debug_mode：总是动态调用is_debug()，不使用配置文件中的值
        if name == 'debug_mode':
            try:
                from is_debug import is_debug
                return is_debug()
            except ImportError:
                # 如果is_debug模块不可用，默认为生产模式
                return False

        if name in data:
            value = data[name]
            
            # 特殊处理first_start_time：根据类型注释进行类型转换
            if name == 'first_start_time':
                type_hints = data.get('__type_hints__', {})
                if type_hints.get('first_start_time') == 'datetime':
                    # 检查是否需要转换为datetime对象
                    from datetime import datetime
                    if not isinstance(value, datetime):
                        try:
                            # 尝试转换为datetime对象
                            time_str = str(value)
                            converted_value = datetime.fromisoformat(time_str)
                            return converted_value
                        except (ValueError, TypeError):
                            # 如果转换失败，返回原始值
                            pass
            
            # 确保嵌套字典被转换为ConfigNode对象
            if isinstance(value, dict) and not isinstance(value, ConfigNode):
                built_value = ConfigNode.build(value)
                data[name] = built_value
                return built_value
            return value
        raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")

    def __setattr__(self, name: str, value: Any):
        """通过属性设置值"""
        if name.startswith('_'):
            super().__setattr__(name, value)
            return

        if '_data' not in self.__dict__:
            super().__setattr__('_data', {})

        # 特殊处理系统键和保留键：不允许设置到_data中，避免数据结构污染
        if name in ('debug_mode', '__type_hints__', '__data__'):
            # 静默忽略这些系统键的设置，因为它们不应该存储在配置数据中
            return

        # 使用实例方法而不是类方法来构建值
        if hasattr(self, 'build'):
            built_value = self.build(value)
        else:
            built_value = ConfigNode.build(value)
        self._data[name] = built_value

        # 如果这是ConfigManager实例，触发自动保存
        if hasattr(self, '_schedule_autosave'):
            # 增加额外的保护，避免在保存过程中触发递归
            if (not getattr(self, '_saving', False) and 
                not getattr(self, '_delayed_saving', False) and
                not getattr(self, '_serializing', False)):
                self._schedule_autosave()
        return

    def __delattr__(self, name: str):
        """通过属性删除值"""
        if name in self._data:
            del self._data[name]
            return
        raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")

    def __getitem__(self, key: str) -> Any:
        """通过键访问值"""
        value = self._data[key]
        return value

    def __setitem__(self, key: str, value: Any):
        """通过键设置值"""
        # 特殊处理系统键和保留键：不允许设置到_data中，避免数据结构污染
        if key in ('debug_mode', '__type_hints__', '__data__'):
            # 静默忽略这些系统键的设置，因为它们不应该存储在配置数据中
            return
            
        # 使用实例方法而不是类方法来构建值
        if hasattr(self, 'build'):
            built_value = self.build(value)
        else:
            built_value = ConfigNode.build(value)
        self._data[key] = built_value
        return

    def __delitem__(self, key: str):
        """通过键删除值"""
        del self._data[key]
        return

    def __contains__(self, key: str) -> bool:
        """检查键是否存在"""
        result = key in self._data
        return result

    def __len__(self) -> int:
        """返回节点包含的属性数量"""
        length = len(self._data)
        return length

    def __iter__(self):
        """返回迭代器（返回自身）"""
        iterator = iter([self])
        return iterator

    def __float__(self) -> float:
        """将ConfigNode转换为float（如果包含单个数值）"""
        if len(self._data) == 1:
            value = next(iter(self._data.values()))
            if isinstance(value, (int, float)):
                return float(value)
        # 提供更详细的错误信息
        raise TypeError(
            f"无法将ConfigNode转换为float。ConfigNode内容: {self._data}\n"
            f"提示：ConfigNode应该包含单个数值才能进行数学运算。"
        )

    def __int__(self) -> int:
        """将ConfigNode转换为int（如果包含单个数值）"""
        if len(self._data) == 1:
            value = next(iter(self._data.values()))
            if isinstance(value, (int, float)):
                return int(value)
        # 提供更详细的错误信息
        raise TypeError(
            f"无法将ConfigNode转换为int。ConfigNode内容: {self._data}\n"
            f"提示：ConfigNode应该包含单个数值才能进行数学运算。"
        )

    def __mul__(self, other):
        """支持乘法运算"""
        try:
            return float(self) * other
        except TypeError as e:
            raise TypeError(
                f"ConfigNode乘法运算失败: {self._data} * {other}\n"
                f"原因: {str(e)}\n"
                f"提示：请检查配置值是否为正确的数值类型。"
            )

    def __rmul__(self, other):
        """支持右乘法运算"""
        return self.__mul__(other)

    def __add__(self, other):
        """支持加法运算"""
        try:
            return float(self) + other
        except TypeError as e:
            raise TypeError(
                f"ConfigNode加法运算失败: {self._data} + {other}\n"
                f"原因: {str(e)}\n"
                f"提示：请检查配置值是否为正确的数值类型。"
            )

    def __radd__(self, other):
        """支持右加法运算"""
        return self.__add__(other)

    def __sub__(self, other):
        """支持减法运算"""
        try:
            return float(self) - other
        except TypeError as e:
            raise TypeError(
                f"ConfigNode减法运算失败: {self._data} - {other}\n"
                f"原因: {str(e)}\n"
                f"提示：请检查配置值是否为正确的数值类型。"
            )

    def __rsub__(self, other):
        """支持右减法运算"""
        try:
            return other - float(self)
        except TypeError as e:
            raise TypeError(
                f"ConfigNode右减法运算失败: {other} - {self._data}\n"
                f"原因: {str(e)}\n"
                f"提示：请检查配置值是否为正确的数值类型。"
            )

    def __truediv__(self, other):
        """支持除法运算"""
        try:
            return float(self) / other
        except TypeError as e:
            raise TypeError(
                f"ConfigNode除法运算失败: {self._data} / {other}\n"
                f"原因: {str(e)}\n"
                f"提示：请检查配置值是否为正确的数值类型。"
            )

    def __rtruediv__(self, other):
        """支持右除法运算"""
        try:
            return other / float(self)
        except TypeError as e:
            raise TypeError(
                f"ConfigNode右除法运算失败: {other} / {self._data}\n"
                f"原因: {str(e)}\n"
                f"提示：请检查配置值是否为正确的数值类型。"
            )

    def __eq__(self, other) -> bool:
        """等值比较，支持自动解包"""
        # 如果是单值ConfigNode，尝试与解包后的值比较
        if len(self._data) == 1:
            value = next(iter(self._data.values()))
            if not isinstance(value, (dict, list, ConfigNode)):
                return value == other
        
        # 否则比较ConfigNode对象本身
        if isinstance(other, ConfigNode):
            return self._data == other._data
        
        return False

    def __deepcopy__(self, memo: Dict) -> ConfigNode:
        """深拷贝方法"""
        new_node = self.__class__()
        memo[id(self)] = new_node
        for key, value in self._data.items():
            new_node[key] = copy.deepcopy(value, memo)
        return new_node

    def _get_auto_unpacked_value(self) -> Any:
        """获取自动解包后的值
        
        仅当ConfigNode包含单个值且键名表示这是值包装器时才解包
        只有特定键名（如'single'）才会触发自动解包，避免破坏正常的嵌套结构
        """
        if len(self._data) == 1:
            key = next(iter(self._data.keys()))
            value = next(iter(self._data.values()))
            
            # 只有'single'键名才触发自动解包，避免破坏正常的嵌套结构
            # 'value'、'data'、'content'等键名应该保持为ConfigNode以支持嵌套结构
            auto_unpack_keys = {'single'}
            
            if key in auto_unpack_keys and not isinstance(value, (dict, list, ConfigNode)):
                return value
        
        # 否则返回自身（不解包）
        return self

    def get(self, key: str, default: Any = None) -> Any:
        """安全获取值"""
        value = self._data.get(key, default)
        return value

    def update(self, *args, **kwargs):
        """更新节点内容"""
        if args:
            updates = dict(*args, **kwargs)
        else:
            updates = kwargs

        for key, value in updates.items():
            # 使用实例方法而不是类方法来构建值
            if hasattr(self, 'build'):
                self[key] = self.build(value)
            else:
                self[key] = ConfigNode.build(value)
        return

    @classmethod
    def build(cls, obj: Any) -> Any:
        """构建对象，递归转换嵌套结构"""
        # 如果已经是ConfigNode，直接返回，避免递归
        if isinstance(obj, ConfigNode):
            return obj

        # 如果是Mapping类型（字典等），转换为ConfigNode
        if isinstance(obj, Mapping):
            # 确保创建的是ConfigNode而不是子类
            built_obj = ConfigNode(obj)
            return built_obj

        # 如果是可迭代对象但不是字符串，递归处理元素
        if not isinstance(obj, str) and isinstance(obj, Iterable):
            try:
                if hasattr(obj, '__iter__'):
                    built_items = []
                    for x in obj:
                        built_items.append(cls.build(x))
                    # 保持原始类型
                    built_obj = obj.__class__(built_items)
                    return built_obj
            except (TypeError, ValueError):
                # 如果无法构建，直接返回原对象
                return obj

        # 其他情况直接返回
        return obj

    def to_dict(self) -> Dict:
        """转换为普通字典，避免递归"""
        return self._to_dict_recursive(set())

    def _to_dict_recursive(self, visited: set) -> Dict:
        """递归转换为字典，使用visited集合避免循环引用"""
        if id(self) in visited:
            return "<circular-reference>"
        
        visited.add(id(self))
        result = {}
        
        # 直接访问_data避免递归
        if hasattr(self, '_data'):
            data = super().__getattribute__('_data')
            for key, value in data.items():
                # 跳过系统键和特殊键，因为它们不应该保存到__data__节点
                if key in ('debug_mode', '_root', '__type_hints__', '__data__'):
                    continue
                    
                if isinstance(value, ConfigNode):
                    result[key] = value._to_dict_recursive(visited)
                else:
                    result[key] = value
        
        visited.remove(id(self))
        return result

    def from_dict(self, data: Dict):
        """从字典加载"""
        # 直接访问_data避免递归
        if '_data' not in self.__dict__:
            super().__setattr__('_data', {})

        data_dict = super().__getattribute__('_data')
        data_dict.clear()

        for key, value in data.items():
            # 过滤掉系统键，避免数据结构污染
            if key in ('__type_hints__', '__data__', 'debug_mode'):
                continue
            # 直接设置到_data中，而不是通过属性访问
            if isinstance(value, dict):
                data_dict[key] = ConfigNode(value)
            else:
                data_dict[key] = value
        return

    def is_multi_platform_config(self) -> bool:
        """检查是否是多平台配置（包含windows、linux、ubuntu、macos键的字典）"""
        if not isinstance(self._data, dict):
            return False
        
        # 检查是否包含多平台配置的特征键
        platform_keys = {'windows', 'linux', 'ubuntu', 'macos'}
        return any(key in self._data for key in platform_keys)

    def get_platform_path(self, platform: str) -> str:
        """获取指定平台的路径"""
        if not self.is_multi_platform_config():
            return str(self._data) if self._data else ""
        
        return self._data.get(platform, "")


def unique_list_order_preserved(seq: Iterable) -> List[Any]:
    """返回保持原始顺序的唯一元素列表"""
    seen = set()
    seen_add = seen.add
    result = [x for x in seq if not (x in seen or seen_add(x))]
    return result