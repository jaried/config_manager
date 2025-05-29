# src/config_manager/config_node.py
from __future__ import annotations
from datetime import datetime

start_time = datetime.now()

import copy
from collections.abc import Iterable, Mapping
from typing import Any, Dict, Optional, Type, Union, List


class ConfigNode:
    """配置节点类，支持点操作访问"""

    def __init__(self, *args, **kwargs):
        """初始化配置节点"""
        self._data = {}
        self.update(*args, **kwargs)
        return

    def __dir__(self) -> Iterable[str]:
        """返回属性列表以支持IDE自动补全"""
        default_attrs = list(super().__dir__())
        dict_keys = list(self._data.keys())
        return unique_list_order_preserved(default_attrs + dict_keys)

    def __repr__(self) -> str:
        """返回对象的字符串表示形式"""
        return f"{self.__class__.__name__}({self._data})"

    def __getattr__(self, name: str) -> Any:
        """通过属性访问值（属性不存在时抛出AttributeError）"""
        if name in self._data:
            return self._data[name]
        raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")

    def __setattr__(self, name: str, value: Any):
        """通过属性设置值"""
        if name.startswith('_'):
            super().__setattr__(name, value)
            return
        self._data[name] = self.build(value)
        return

    def __delattr__(self, name: str):
        """通过属性删除值"""
        if name in self._data:
            del self._data[name]
            return
        raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")

    def __getitem__(self, key: str) -> Any:
        """通过键访问值"""
        return self._data[key]

    def __setitem__(self, key: str, value: Any):
        """通过键设置值"""
        self._data[key] = self.build(value)
        return

    def __delitem__(self, key: str):
        """通过键删除值"""
        del self._data[key]
        return

    def __contains__(self, key: str) -> bool:
        """检查键是否存在"""
        return key in self._data

    def __len__(self) -> int:
        """返回节点包含的属性数量"""
        return len(self._data)

    def __iter__(self):
        """返回迭代器（返回自身）"""
        return iter([self])

    def __deepcopy__(self, memo: Dict) -> ConfigNode:
        """深拷贝方法"""
        new_node = self.__class__()
        memo[id(self)] = new_node
        for key, value in self._data.items():
            new_node[key] = copy.deepcopy(value, memo)
        return new_node

    def get(self, key: str, default: Any = None) -> Any:
        """安全获取值"""
        return self._data.get(key, default)

    def update(self, *args, **kwargs):
        """更新节点内容"""
        for key, value in dict(*args, **kwargs).items():
            self[key] = self.build(value)
        return

    @classmethod
    def build(cls, obj: Any) -> Any:
        """构建对象，递归转换嵌套结构"""
        if isinstance(obj, Mapping):
            return cls(obj)
        if not isinstance(obj, str) and isinstance(obj, Iterable):
            return obj.__class__(cls.build(x) for x in obj)
        return obj

    def to_dict(self) -> Dict:
        """转换为普通字典"""
        result = {}
        for key, value in self._data.items():
            if isinstance(value, ConfigNode):
                result[key] = value.to_dict()
            else:
                result[key] = value
        return result

    def from_dict(self, data: Dict):
        """从字典加载"""
        self._data.clear()
        for key, value in data.items():
            self[key] = value
        return