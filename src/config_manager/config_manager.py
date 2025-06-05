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
ENABLE_CALL_CHAIN_DISPLAY = False  # 默认关闭调用链显示


class ConfigManager(ConfigManagerCore):
    """配置管理器类，支持自动保存和类型提示"""
    _instances = {}
    _thread_lock = threading.Lock()
    _global_listeners = []

    def __new__(cls, config_path: str = None,
                watch: bool = False, auto_create: bool = False,
                autosave_delay: float = 0.1, first_start_time: datetime = None):
        # 生成缓存键 - 修复：基于实际解析的路径
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
                    # 修复：不管初始化是否成功，都返回实例，确保不返回None
                    try:
                        instance.initialize(
                            config_path, watch, auto_create, autosave_delay, first_start_time=first_start_time
                        )
                    except Exception as e:
                        # 即使初始化失败，也要确保实例可用（用于测试环境）
                        print(f"配置管理器初始化警告: {e}")
                        # 设置基本的默认状态
                        if not hasattr(instance, '_data') or instance._data is None:
                            instance._data = {}
                        if not hasattr(instance, '_config_path'):
                            instance._config_path = cache_key.replace('auto:', '') if cache_key.startswith(
                                'auto:') else cache_key

                    cls._instances[cache_key] = instance
        return cls._instances[cache_key]

    def __init__(self, config_path: str = None,
                 watch: bool = False, auto_create: bool = False,
                 autosave_delay: float = 0.1, first_start_time: datetime = None):
        """初始化配置管理器，单例模式下可能被多次调用"""
        # 单例模式下，__init__可能被多次调用，但只有第一次有效
        pass

    @classmethod
    def _generate_cache_key(cls, config_path: str) -> str:
        """生成缓存键 - 修复版本：基于当前工作目录和配置路径"""
        try:
            # 修复：不在缓存键生成时调用路径解析，避免循环依赖
            cwd = os.getcwd()
            
            if config_path is not None:
                # 显式路径：使用绝对路径
                abs_path = os.path.abspath(config_path)
                cache_key = f"explicit:{abs_path}"
            else:
                # 自动路径：基于当前工作目录
                cache_key = f"auto:{cwd}"
            
            return cache_key
        except Exception as e:
            # 如果路径解析失败，生成一个基于输入参数的缓存键
            if config_path is not None:
                return f"explicit:{config_path}"
            else:
                return f"default:{os.getcwd()}"

    @staticmethod
    def generate_config_id() -> str:
        """生成唯一配置ID"""
        config_id = str(uuid.uuid4())
        return config_id


def get_config_manager(
        config_path: str = None,
        watch: bool = False,
        auto_create: bool = False,
        autosave_delay: float = None,
        first_start_time: datetime = None
) -> ConfigManager:
    """
    获取配置管理器单例

    Args:
        config_path: 配置文件路径
        watch: 是否监视文件变化并自动重载
        auto_create: 配置文件不存在时是否自动创建
        autosave_delay: 自动保存延迟时间（秒）
        first_start_time: 首次启动时间

    Returns:
        ConfigManager 实例（永远不返回None）
    """
    manager = ConfigManager(config_path, watch, auto_create, autosave_delay, first_start_time=first_start_time)
    return manager


def _clear_instances_for_testing():
    """清理所有实例，仅用于测试"""
    with ConfigManager._thread_lock:
        for instance in ConfigManager._instances.values():
            if hasattr(instance, '_cleanup'):
                try:
                    instance._cleanup()
                except:
                    pass  # 忽略清理过程中的错误
        ConfigManager._instances.clear()

    # 强制垃圾回收
    import gc
    gc.collect()
    return


if __name__ == '__main__':
    get_config_manager(auto_create=True, first_start_time=start_time)
