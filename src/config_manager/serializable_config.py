from __future__ import annotations

import pickle
from typing import Any, Dict, Optional, Type
from pathlib import Path
from datetime import datetime


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
            
            # 特殊处理paths属性，创建SerializablePathsNode
            if name == 'paths' and isinstance(value, dict):
                return SerializablePathsNode(value, self)
            
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
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> SerializableConfigData:
        """从字典创建SerializableConfigData实例
        
        Args:
            data: 配置数据字典
            
        Returns:
            SerializableConfigData: 创建的实例
        """
        type_hints = data.get('__type_hints__', {})
        config_path = data.get('config_file_path')
        return cls(data=data, type_hints=type_hints, config_path=config_path)


class SerializablePathsNode:
    """可序列化的路径节点，提供动态路径生成功能"""
    
    def __init__(self, data: dict, root: Any = None):
        """初始化可序列化路径节点
        
        Args:
            data: 路径数据字典
            root: 根配置对象（SerializableConfigData）
        """
        self._data = dict(data) if data else {}
        self._root = root  # 直接存储引用，不使用weakref
        self._tsb_cache = None
        self._tsb_cache_time = None
        self._cache_duration = 1.0
    
    def __getattr__(self, name: str) -> Any:
        """获取属性值
        
        Args:
            name: 属性名
            
        Returns:
            属性值
        """
        # 处理动态路径属性
        if name == 'tsb_logs_dir':
            return self._generate_tsb_logs_dir()
        elif name == 'tensorboard_dir':
            # tensorboard_dir始终等于tsb_logs_dir
            return self._generate_tsb_logs_dir()
        
        # 返回_data中的值
        if name in self._data:
            return self._data[name]
        
        raise AttributeError(f"'SerializablePathsNode' object has no attribute '{name}'")
    
    def _generate_tsb_logs_dir(self) -> str:
        """生成TSB日志路径
        
        Returns:
            str: 生成的路径
        """
        # 检查缓存
        if self._tsb_cache is not None and self._tsb_cache_time is not None:
            current_time = datetime.now()
            if (current_time - self._tsb_cache_time).total_seconds() < self._cache_duration:
                return self._tsb_cache
        
        # 获取work_dir
        work_dir = self._data.get('work_dir')
        if not work_dir:
            raise ValueError("work_dir未设置，无法生成tsb_logs_dir")
        
        # 获取配置中的first_start_time
        timestamp = None
        if self._root:
            try:
                first_start_time = self._root.get('first_start_time')
                if isinstance(first_start_time, str):
                    timestamp = datetime.fromisoformat(first_start_time.replace("Z", "+00:00"))
                elif isinstance(first_start_time, datetime):
                    timestamp = first_start_time
            except (AttributeError, ValueError):
                pass
        
        # 使用PathResolver生成路径
        from config_manager.core.path_resolver import PathResolver
        generated_path = PathResolver.generate_tsb_logs_path(work_dir, timestamp)
        
        # 更新缓存
        self._tsb_cache = generated_path
        self._tsb_cache_time = datetime.now()
        
        return generated_path
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值
        
        Args:
            key: 配置键
            default: 默认值
            
        Returns:
            配置值或默认值
        """
        try:
            return getattr(self, key)
        except AttributeError:
            return default
    
    def __contains__(self, key: str) -> bool:
        """检查键是否存在
        
        Args:
            key: 配置键
            
        Returns:
            bool: 键是否存在
        """
        return key in self._data or key in ('tsb_logs_dir', 'tensorboard_dir')


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