from __future__ import annotations

import pickle
from typing import Any, Dict, Optional, Type
from pathlib import Path


class SerializableConfigData:
    """可序列化的配置数据类，用于多进程环境下传递配置数据"""
    
    def __init__(self, data: Dict[str, Any] = None, type_hints: Dict[str, str] = None, 
                 config_path: Optional[str] = None):
        """初始化可序列化配置数据
        
        Args:
            data: 配置数据字典
            type_hints: 类型提示字典
            config_path: 配置文件路径
        """
        self._data = data or {}
        self._type_hints = type_hints or {}
        self._config_path = config_path
        
    def __getattr__(self, name: str) -> Any:
        """通过属性访问配置值"""
        if name.startswith('_'):
            return super().__getattribute__(name)
        
        if name in self._data:
            value = self._data[name]
            # 如果值是字典，递归转换为SerializableConfigData
            if isinstance(value, dict):
                return SerializableConfigData(value)
            return value
        
        raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")
    
    def __setattr__(self, name: str, value: Any):
        """通过属性设置配置值"""
        if name.startswith('_'):
            super().__setattr__(name, value)
            return
        
        if not hasattr(self, '_data'):
            super().__setattr__('_data', {})
        
        self._data[name] = value
    
    def __getitem__(self, key: str) -> Any:
        """通过键访问配置值"""
        return self._data[key]
    
    def __setitem__(self, key: str, value: Any):
        """通过键设置配置值"""
        self._data[key] = value
    
    def __contains__(self, key: str) -> bool:
        """检查键是否存在"""
        return key in self._data
    
    def __len__(self) -> int:
        """返回配置项数量"""
        return len(self._data)
    
    def __iter__(self):
        """返回配置数据的键迭代器"""
        return iter(self._data)
    
    def __repr__(self) -> str:
        """返回字符串表示"""
        return f"SerializableConfigData({self._data})"
    
    def get(self, key: str, default: Any = None, as_type: Type = None) -> Any:
        """获取配置值，支持默认值和类型转换"""
        keys = key.split('.')
        current = self._data
        
        for k in keys:
            if isinstance(current, dict) and k in current:
                current = current[k]
            else:
                if as_type is not None:
                    return self._convert_type(default, as_type)
                return default
        
        if as_type is not None:
            return self._convert_type(current, as_type)
        return current
    
    def set(self, key: str, value: Any, type_hint: Type = None):
        """设置配置值，支持点号分隔的键"""
        keys = key.split('.')
        current = self._data
        
        # 创建嵌套结构
        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            current = current[k]
        
        # 设置最终值
        final_key = keys[-1]
        current[final_key] = value
        
        # 记录类型提示
        if type_hint is not None:
            self._type_hints[key] = type_hint.__name__
    
    def update(self, other: Dict[str, Any]):
        """更新配置数据"""
        self._data.update(other)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return self._data.copy()
    
    def get_type_hint(self, key: str) -> Optional[str]:
        """获取类型提示"""
        return self._type_hints.get(key)
    
    def get_config_path(self) -> Optional[str]:
        """获取配置文件路径"""
        return self._config_path
    
    @staticmethod
    def _convert_type(value: Any, target_type: Type) -> Any:
        """将值转换为目标类型"""
        if target_type is None:
            return value
        
        try:
            if target_type is Path and isinstance(value, str):
                return Path(value)
            return target_type(value)
        except (TypeError, ValueError):
            return value
    
    def is_serializable(self) -> bool:
        """检查对象是否可序列化"""
        try:
            pickle.dumps(self)
            return True
        except Exception:
            return False
    
    def clone(self) -> SerializableConfigData:
        """克隆配置数据"""
        import copy
        return SerializableConfigData(
            data=copy.deepcopy(self._data),
            type_hints=self._type_hints.copy(),
            config_path=self._config_path
        )
    
    def merge(self, other: SerializableConfigData):
        """合并另一个配置数据"""
        if not isinstance(other, SerializableConfigData):
            raise TypeError("只能合并SerializableConfigData对象")
        
        self._data.update(other._data)
        self._type_hints.update(other._type_hints)
    
    def keys(self):
        """返回配置键"""
        return self._data.keys()
    
    def values(self):
        """返回配置值"""
        return self._data.values()
    
    def items(self):
        """返回配置项"""
        return self._data.items()


def create_serializable_config(config_manager) -> SerializableConfigData:
    """从ConfigManager创建可序列化的配置数据
    
    Args:
        config_manager: ConfigManager实例
        
    Returns:
        SerializableConfigData: 可序列化的配置数据
    """
    # 获取配置数据
    data = config_manager.to_dict()
    
    # 获取类型提示
    type_hints = getattr(config_manager, '_type_hints', {})
    
    # 获取配置文件路径
    config_path = getattr(config_manager, '_config_path', None)
    
    return SerializableConfigData(
        data=data,
        type_hints=type_hints,
        config_path=config_path
    ) 