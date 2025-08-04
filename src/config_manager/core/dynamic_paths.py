# src/config_manager/core/dynamic_paths.py
from __future__ import annotations
from datetime import datetime
from typing import Any, Optional
import os
from weakref import ref

from .path_resolver import PathResolver


class TensorBoardDirDescriptor:
    """确保tensorboard_dir始终等于tsb_logs_dir的描述符"""
    
    def __get__(self, obj: Any, objtype: type = None) -> str:
        """获取tensorboard_dir的值（总是等于tsb_logs_dir）
        
        Args:
            obj: PathsConfigNode实例
            objtype: PathsConfigNode类型
            
        Returns:
            str: tsb_logs_dir的值
        """
        if obj is None:
            return self
        
        # 直接访问tsb_logs_dir属性，触发其动态生成
        return obj.tsb_logs_dir
    
    def __set__(self, obj: Any, value: Any) -> None:
        """设置tensorboard_dir的值（禁止操作）
        
        Args:
            obj: PathsConfigNode实例
            value: 尝试设置的值
            
        Raises:
            AttributeError: 总是抛出，因为tensorboard_dir是只读的
        """
        raise AttributeError("tensorboard_dir是只读属性，其值自动等于tsb_logs_dir")


class DynamicPathProperty:
    """动态路径属性，支持缓存和动态生成"""
    
    def __init__(self, cache_duration: float = 1.0):
        """初始化动态路径属性
        
        Args:
            cache_duration: 缓存持续时间（秒），默认1秒
        """
        self.cache_duration = cache_duration
        self._cache = {}  # 格式: {id(obj): (value, timestamp)}
    
    def __get__(self, obj: Any, objtype: type = None) -> str:
        """获取动态路径值
        
        Args:
            obj: PathsConfigNode实例
            objtype: PathsConfigNode类型
            
        Returns:
            str: 生成的路径
        """
        if obj is None:
            return self
        
        # 获取对象ID用于缓存
        obj_id = id(obj)
        
        # 检查缓存
        if obj_id in self._cache:
            cached_value, cache_time = self._cache[obj_id]
            current_time = datetime.now()
            
            # 如果缓存未过期，返回缓存值
            if (current_time - cache_time).total_seconds() < self.cache_duration:
                return cached_value
        
        # 生成新的路径
        value = self._generate_path(obj)
        
        # 更新缓存
        self._cache[obj_id] = (value, datetime.now())
        
        # 清理过期的缓存条目
        self._cleanup_cache()
        
        return value
    
    def _generate_path(self, obj: Any) -> str:
        """生成TSB日志路径
        
        Args:
            obj: PathsConfigNode实例
            
        Returns:
            str: 生成的路径
        """
        # 获取work_dir
        work_dir = getattr(obj, 'work_dir', None)
        if not work_dir:
            raise ValueError("work_dir未设置，无法生成tsb_logs_dir")
        
        # 获取配置管理器的first_start_time
        config_manager = self._get_config_manager(obj)
        if config_manager:
            try:
                first_start_time = config_manager.first_start_time
                if isinstance(first_start_time, str):
                    timestamp = datetime.fromisoformat(first_start_time.replace("Z", "+00:00"))
                elif isinstance(first_start_time, datetime):
                    timestamp = first_start_time
                else:
                    timestamp = None
            except (AttributeError, ValueError):
                timestamp = None
        else:
            timestamp = None
        
        # 使用PathResolver生成路径
        return PathResolver.generate_tsb_logs_path(work_dir, timestamp)
    
    def _get_config_manager(self, obj: Any) -> Optional[Any]:
        """获取配置管理器实例
        
        Args:
            obj: PathsConfigNode实例
            
        Returns:
            ConfigManager实例或None
        """
        # 尝试通过_root属性获取
        if hasattr(obj, '_root'):
            root = obj._root
            # 如果是弱引用，获取实际对象
            if isinstance(root, ref):
                root = root()
            # 继续向上查找，直到找到ConfigManager
            while root and hasattr(root, '_root'):
                parent = root._root
                if isinstance(parent, ref):
                    parent = parent()
                if parent is None:
                    break
                root = parent
            return root
        return None
    
    def _cleanup_cache(self) -> None:
        """清理过期的缓存条目"""
        current_time = datetime.now()
        expired_keys = []
        
        for obj_id, (value, cache_time) in self._cache.items():
            if (current_time - cache_time).total_seconds() > self.cache_duration * 2:
                expired_keys.append(obj_id)
        
        for key in expired_keys:
            del self._cache[key]


class PathsConfigNode:
    """路径配置节点，支持动态路径生成"""
    
    # 定义属性描述符
    tsb_logs_dir = DynamicPathProperty(cache_duration=1.0)
    tensorboard_dir = TensorBoardDirDescriptor()
    
    def __init__(self, data: dict, root: Any = None):
        """初始化路径配置节点
        
        Args:
            data: 路径数据字典
            root: 根配置管理器引用
        """
        # 如果data是ConfigNode，提取其_data
        if hasattr(data, '_data'):
            self._data = dict(data._data)
        else:
            self._data = dict(data) if data else {}
        self._root = ref(root) if root else None
    
    def __getattr__(self, name: str) -> Any:
        """获取属性值
        
        Args:
            name: 属性名
            
        Returns:
            属性值
            
        Raises:
            AttributeError: 属性不存在时
        """
        # 检查是否是动态属性
        if name in ('tsb_logs_dir', 'tensorboard_dir'):
            # 使用描述符处理
            return getattr(type(self), name).__get__(self, type(self))
        
        # 检查_data中的值
        if name in self._data:
            return self._data[name]
        
        raise AttributeError(f"'PathsConfigNode' object has no attribute '{name}'")
    
    def __setattr__(self, name: str, value: Any) -> None:
        """设置属性值
        
        Args:
            name: 属性名
            value: 属性值
        """
        # 特殊属性直接设置
        if name.startswith('_'):
            super().__setattr__(name, value)
            return
        
        # 检查是否是只读属性
        if name == 'tensorboard_dir':
            # 使用描述符的__set__方法，会抛出AttributeError
            getattr(type(self), name).__set__(self, value)
            return
        
        # 其他属性设置到_data
        self._data[name] = value
    
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
    
    def __repr__(self) -> str:
        """返回字符串表示
        
        Returns:
            str: 对象的字符串表示
        """
        return f"PathsConfigNode({self._data})"