# src/config_manager/config_node.py
from __future__ import annotations
from datetime import datetime

start_time = datetime.now()

import copy
from collections.abc import Iterable, Mapping
from typing import Any, Dict, List


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
            return data[name]
        raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")

    def __setattr__(self, name: str, value: Any):
        """通过属性设置值"""
        if name.startswith('_'):
            super().__setattr__(name, value)
            return

        if '_data' not in self.__dict__:
            super().__setattr__('_data', {})

        # 特殊处理debug_mode：不允许设置，因为它是动态属性
        if name == 'debug_mode':
            # 静默忽略debug_mode的设置，因为它应该总是动态获取
            return

        # 使用实例方法而不是类方法来构建值
        if hasattr(self, 'build'):
            built_value = self.build(value)
        else:
            built_value = ConfigNode.build(value)
        self._data[name] = built_value

        # 如果这是ConfigManager实例，触发自动保存
        if hasattr(self, '_schedule_autosave'):
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
        # 特殊处理debug_mode：不允许设置，因为它是动态属性
        if key == 'debug_mode':
            # 静默忽略debug_mode的设置，因为它应该总是动态获取
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

    def __deepcopy__(self, memo: Dict) -> ConfigNode:
        """深拷贝方法"""
        new_node = self.__class__()
        memo[id(self)] = new_node
        for key, value in self._data.items():
            new_node[key] = copy.deepcopy(value, memo)
        return new_node

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
                # 跳过debug_mode和_root，因为它们不应该保存到配置文件
                if key in ('debug_mode', '_root'):
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