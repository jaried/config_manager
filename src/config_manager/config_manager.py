# src/config_manager/config_manager.py
from __future__ import annotations
from datetime import datetime

start_time = datetime.now()

import os
import yaml
import threading
import atexit
import time
import uuid
from pathlib import Path
from typing import Any, Dict, Optional, Type
from collections.abc import Iterable, Mapping
from .config_node import ConfigNode
from .utils import lock_file, unlock_file


class ConfigManager(ConfigNode):
    """配置管理器类，支持自动保存和类型提示"""
    _instances = {}
    _thread_lock = threading.Lock()
    _global_listeners = []

    def __new__(cls, config_path: str = None,
                watch: bool = False, auto_create: bool = True,
                autosave_delay: float = 0.1):
        # 使用配置文件路径作为实例键，支持多个配置文件
        resolved_path = cls._resolve_config_path(config_path)

        if resolved_path not in cls._instances:
            with cls._thread_lock:
                if resolved_path not in cls._instances:
                    instance = super().__new__(cls)
                    initialized = instance._initialize(
                        config_path, watch, auto_create, autosave_delay
                    )
                    if not initialized:
                        return None
                    cls._instances[resolved_path] = instance
        return cls._instances[resolved_path]

    def __init__(self, config_path: str = None,
                 watch: bool = False, auto_create: bool = True,
                 autosave_delay: float = 0.1):
        """覆写父类 __init__，避免将多余参数传入 ConfigNode.__init__"""
        pass

    def _initialize(self, config_path: str, watch: bool,
                    auto_create: bool, autosave_delay: float):
        # 先初始化ConfigNode的_data
        super(ConfigManager, self).__setattr__('_data', {})

        self._config_path = self._resolve_config_path(config_path)
        self._watch = watch
        self._auto_create = auto_create
        self._autosave_delay = autosave_delay
        self._last_mtime = 0
        self._watcher_thread = None
        self._stop_watcher = threading.Event()
        self._type_hints = {}
        self._autosave_timer = None
        self._autosave_lock = threading.Lock()

        loaded = self._load()
        if not loaded and not self._auto_create:
            return False

        atexit.register(self._cleanup)

        if watch:
            self._start_watcher()

        return True

    @staticmethod
    def _resolve_config_path(config_path: str) -> str:
        """解析配置文件路径"""
        if config_path is not None:
            resolved_path = os.path.abspath(config_path)
            return resolved_path

        # 修正路径解析逻辑 - 确保在 src/config 下
        current_file = os.path.abspath(__file__)
        src_dir = os.path.dirname(os.path.dirname(current_file))  # 从 config_manager 目录向上到 src
        config_dir = os.path.join(src_dir, 'config')
        os.makedirs(config_dir, exist_ok=True)
        resolved_path = os.path.join(config_dir, 'config.yaml')
        return resolved_path

    def _schedule_autosave(self):
        """安排自动保存任务"""
        with self._autosave_lock:
            if self._autosave_timer:
                self._autosave_timer.cancel()

            self._autosave_timer = threading.Timer(
                self._autosave_delay,
                self._perform_autosave
            )
            self._autosave_timer.daemon = True
            self._autosave_timer.start()
        return

    def _perform_autosave(self):
        """执行自动保存"""
        try:
            # 确保有数据才保存
            if hasattr(self, '_data') and self._data:
                saved = self.save()
                if saved:
                    print(f"配置已自动保存到 {self._config_path}")
            else:
                print("自动保存跳过：无数据")
        except Exception as e:
            print(f"自动保存失败: {str(e)}")
        finally:
            with self._autosave_lock:
                self._autosave_timer = None
        return

    def _load(self):
        """从文件加载配置"""
        if not os.path.exists(self._config_path):
            if self._auto_create:
                print(f"配置文件不存在，创建新配置: {self._config_path}")
                self._data = {}
                saved = self.save()
                if not saved:
                    return False
                return True
            else:
                print(f"配置文件不存在: {self._config_path}")
                self._data = {}
                return False

        try:
            with open(self._config_path, 'r', encoding='utf-8') as f:
                lock_file(f)
                try:
                    loaded_data = yaml.safe_load(f) or {}
                finally:
                    unlock_file(f)

            # 获取原始数据
            raw_data = loaded_data.get('__data__', {})

            # 清空当前数据并重新构建
            self._data.clear()

            # 使用 from_dict 重新构建数据结构，但要确保正确处理
            if raw_data:
                for key, value in raw_data.items():
                    if isinstance(value, dict):
                        # 对于字典值，创建ConfigNode
                        self._data[key] = ConfigNode(value)
                    else:
                        # 对于其他值，直接设置
                        self._data[key] = value

            self._type_hints = loaded_data.get('__type_hints__', {})

            self._last_mtime = os.path.getmtime(self._config_path)
            print(f"配置已从 {self._config_path} 加载")
            return True
        except Exception as e:
            print(f"加载配置失败: {str(e)}")
            self._data = {}
            return False

    def save(self):
        """保存配置到文件（原子替换）"""
        try:
            dir_path = os.path.dirname(self._config_path)
            if dir_path:
                os.makedirs(dir_path, exist_ok=True)

            # 在保存时加锁，确保线程安全
            with self._autosave_lock:
                # 构建保存数据，使用 to_dict 方法
                data_to_save = self.to_dict()

                save_data = {
                    '__data__': data_to_save,
                    '__type_hints__': self._type_hints
                }

            tmp_path = f"{self._config_path}.tmp"
            with open(tmp_path, 'w', encoding='utf-8') as f:
                yaml.dump(save_data, f, default_flow_style=False, allow_unicode=True)

            os.replace(tmp_path, self._config_path)
            self._last_mtime = os.path.getmtime(self._config_path)
            return True
        except Exception as e:
            print(f"保存配置失败: {str(e)}")
            return False

    def reload(self):
        """重新加载配置"""
        print("重新加载配置...")
        reloaded = self._load()
        return reloaded

    def _start_watcher(self):
        """启动文件监视线程"""
        if self._watcher_thread is not None and self._watcher_thread.is_alive():
            return

        self._stop_watcher.clear()
        self._watcher_thread = threading.Thread(
            target=self._watch_file,
            daemon=True
        )
        self._watcher_thread.start()
        print("配置文件监视器已启动")
        return

    def _watch_file(self):
        """监视配置文件变化"""
        while not self._stop_watcher.is_set():
            try:
                if os.path.exists(self._config_path):
                    current_mtime = os.path.getmtime(self._config_path)
                    if current_mtime > self._last_mtime:
                        print("检测到配置文件变化，重新加载...")
                        self.reload()
                        self._last_mtime = current_mtime
                time.sleep(1)
            except Exception as e:
                print(f"监视配置出错: {str(e)}")
                time.sleep(5)
        return

    def _cleanup(self):
        """清理资源"""
        self._stop_watcher.set()
        if self._autosave_timer:
            self._autosave_timer.cancel()
            self._perform_autosave()
        return

    @classmethod
    def build(cls, obj: Any) -> Any:
        """构建对象，递归转换嵌套结构（ConfigManager 版本）"""
        # 如果已经是ConfigNode，直接返回，避免递归
        if isinstance(obj, ConfigNode):
            return obj

        # 如果是Mapping类型（字典等），转换为ConfigNode（不是ConfigManager）
        if isinstance(obj, Mapping):
            built_obj = ConfigNode(obj)
            return built_obj

        # 如果是可迭代对象但不是字符串，递归处理元素
        if not isinstance(obj, str) and isinstance(obj, Iterable):
            try:
                if hasattr(obj, '__iter__'):
                    built_items = []
                    for x in obj:
                        built_items.append(ConfigNode.build(x))
                    # 保持原始类型
                    built_obj = obj.__class__(built_items)
                    return built_obj
            except (TypeError, ValueError):
                # 如果无法构建，直接返回原对象
                return obj

        # 其他情况直接返回
        return obj

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

    def get(self, key: str, default: Any = None, as_type: Type = None) -> Any:
        """获取配置值，支持类型转换"""
        keys = key.split('.')
        current = self

        for k in keys:
            # 检查属性是否存在
            if hasattr(current, '_data') and k in current._data:
                current = current._data[k]
            elif hasattr(current, k):
                current = getattr(current, k)
            else:
                converted_default = self._convert_type(default, as_type)
                return converted_default

        converted_value = self._convert_type(current, as_type)
        return converted_value

    def set(self, key: str, value: Any, autosave: bool = True, type_hint: Type = None):
        """设置配置值并自动保存，支持类型提示"""
        keys = key.split('.')
        current = self

        for k in keys[:-1]:
            if not hasattr(current, k):
                setattr(current, k, ConfigNode())
            current = getattr(current, k)

        if type_hint is not None:
            self._type_hints[key] = type_hint.__name__

        if isinstance(value, Path):
            value = str(value)

        # 直接设置值，避免通过build方法
        final_key = keys[-1]
        if isinstance(value, dict):
            setattr(current, final_key, ConfigNode(value))
        else:
            # 直接设置到_data中，避免触发__setattr__的build过程
            if hasattr(current, '_data'):
                current._data[final_key] = value
            else:
                setattr(current, final_key, value)

        if autosave:
            # 确保自动保存被触发
            print(f"调试：触发自动保存，key={key}, value={value}")
            self._schedule_autosave()
        return

    def get_type_hint(self, key: str) -> Optional[str]:
        """获取配置项的类型提示"""
        type_hint = self._type_hints.get(key)
        return type_hint

    def set_type_hint(self, key: str, type_hint: Type):
        """设置配置项的类型提示"""
        self._type_hints[key] = type_hint.__name__
        self._schedule_autosave()
        return

    def get_path(self, key: str, default: Path = None) -> Path:
        """获取路径类型的配置值"""
        path_str = self.get(key)
        if path_str is None:
            return default
        path_obj = Path(path_str)
        return path_obj

    def update(self, *args, **kwargs):
        """批量更新配置值（重写以兼容ConfigNode签名）"""
        if args and isinstance(args[0], dict):
            updates = args[0]
            autosave = kwargs.get('autosave', True)
        else:
            updates = dict(*args, **kwargs)
            autosave = True

        for key, value in updates.items():
            self.set(key, value, autosave=False)

        if autosave:
            self._schedule_autosave()
        return

    def get_config_path(self) -> str:
        """获取配置文件路径"""
        return self._config_path

    @staticmethod
    def generate_config_id() -> str:
        """生成唯一配置ID"""
        config_id = str(uuid.uuid4())
        return config_id

    def snapshot(self) -> Dict:
        """创建配置快照，避免递归"""
        data_dict = {}
        for key, value in self._data.items():
            if isinstance(value, ConfigNode):
                if value is not self:
                    data_dict[key] = value.to_dict()
                else:
                    data_dict[key] = "<self-reference>"
            else:
                data_dict[key] = value

        snapshot_data = {
            'data': data_dict,
            'type_hints': self._type_hints.copy()
        }
        return snapshot_data

    def restore(self, snapshot: Dict):
        """从快照恢复配置"""
        # 清空当前数据
        self._data.clear()

        # 恢复数据
        snapshot_data = snapshot.get('data', {})
        for key, value in snapshot_data.items():
            if isinstance(value, dict):
                self._data[key] = ConfigNode(value)
            else:
                self._data[key] = value

        # 恢复类型提示
        self._type_hints = snapshot.get('type_hints', {}).copy()

        # 保存到文件
        self.save()
        return

    def temporary(self, temp_changes: Dict[str, Any]):
        """临时修改配置的上下文管理器"""

        class TemporaryContext:
            def __init__(self, config, changes_dict):
                self.config = config
                self.changes = changes_dict
                self.original = {}
                self.snapshot = None

            def __enter__(self):
                self.snapshot = self.config.snapshot()
                for path, value in self.changes.items():
                    self.original[path] = self.config.get(path)
                    self.config.set(path, value)
                return self.config

            def __exit__(self, exc_type, exc_val, exc_tb):
                self.config.restore(self.snapshot)

        context = TemporaryContext(self, temp_changes)
        return context


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
    return