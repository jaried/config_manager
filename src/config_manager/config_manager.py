# src/config_manager/config_manager.py
from __future__ import annotations
from datetime import datetime

start_time = datetime.now()

import os
import threading
import uuid
from typing import Any, Dict
from .config_node import ConfigNode
from .core.manager import ConfigManagerCore
from .core.path_resolver import PathResolver

# 全局调用链显示开关 - 手工修改这个值来控制调用链显示
ENABLE_CALL_CHAIN_DISPLAY = False  # 改为 False 可关闭调用链显示


class ConfigManager(ConfigManagerCore):
    """配置管理器类，支持自动保存和类型提示"""
    _instances = {}
    _thread_lock = threading.Lock()
    _global_listeners = []

    def __new__(cls, config_path: str = None,
                watch: bool = False, auto_create: bool = True,
                autosave_delay: float = 0.1):
        # 生成缓存键
        cache_key = cls._generate_cache_key(config_path)

        if cache_key not in cls._instances:
            with cls._thread_lock:
                if cache_key not in cls._instances:
                    # 创建新实例，直接调用object.__new__避免递归
                    instance = object.__new__(cls)

                    # 手动初始化ConfigNode的_data属性
                    instance.__dict__['_data'] = {}

                    # 初始化ConfigManagerCore
                    ConfigManagerCore.__init__(instance)

                    # 执行配置管理器的初始化
                    initialized = instance.initialize(
                        config_path, watch, auto_create, autosave_delay
                    )
                    if not initialized:
                        return None
                    cls._instances[cache_key] = instance
        return cls._instances[cache_key]

    def __init__(self, config_path: str = None,
                 watch: bool = False, auto_create: bool = True,
                 autosave_delay: float = 0.1):
        """初始化配置管理器，单例模式下可能被多次调用"""
        # 单例模式下，__init__可能被多次调用，但只有第一次有效
        pass

    @classmethod
    def _generate_cache_key(cls, config_path: str) -> str:
        """生成缓存键"""
        if config_path is None:
            cwd = os.getcwd()
            cache_key = f"auto:{cwd}"
        else:
            resolved_path = PathResolver.resolve_config_path(config_path)
            cache_key = resolved_path
        return cache_key

    @staticmethod
    def generate_config_id() -> str:
        """生成唯一配置ID"""
        config_id = str(uuid.uuid4())
        return config_id


def get_config_manager(config_path: str = None,
                       watch: bool = True,
                       auto_create: bool = True,
                       autosave_delay: float = 0.1) -> ConfigManager:
    """
    获取配置管理器单例

    Args:
        config_path: 配置文件路径
        watch: 是否监视文件变化并自动重载
        auto_create: 配置文件不存在时是否自动创建
        autosave_delay: 自动保存延迟时间（秒）

    Returns:
        ConfigManager 实例
    """
    manager = ConfigManager(config_path, watch, auto_create, autosave_delay)
    return manager


def _clear_instances_for_testing():
    """清理所有实例，仅用于测试"""
    with ConfigManager._thread_lock:
        for instance in ConfigManager._instances.values():
            if hasattr(instance, '_cleanup'):
                instance._cleanup()
        ConfigManager._instances.clear()

    # 强制垃圾回收
    import gc
    gc.collect()
    return