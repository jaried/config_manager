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
import json
from pathlib import Path
from typing import Any, Dict, Optional, Type, Union
from multiprocessing import Lock as ProcessLock
from .config_node import ConfigNode
from .utils import lock_file, unlock_file


class ConfigManager(ConfigNode):
    """配置管理器类，支持自动保存和类型提示"""
    _instance = None
    _process_lock = ProcessLock()
    _global_listeners = []

    def __new__(cls, config_path: str = None,
                watch: bool = False, auto_create: bool = True,
                autosave_delay: float = 0.1):
        if cls._instance is None:
            with cls._process_lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    initialized = cls._instance._initialize(
                        config_path, watch, auto_create, autosave_delay
                    )
                    if not initialized:
                        return None
        return cls._instance

    def __init__(self, config_path: str = None,
                 watch: bool = False, auto_create: bool = True,
                 autosave_delay: float = 0.1):
        """覆写父类 __init__，避免将多余参数传入 ConfigNode.__init__"""
        pass

    def _initialize(self, config_path: str, watch: bool,
                    auto_create: bool, autosave_delay: float):
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

    def _resolve_config_path(self, config_path: str) -> str:
        """解析配置文件路径"""
        if config_path is not None:
            return os.path.abspath(config_path)

        # 获取项目根目录
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        return os.path.join(project_root, 'src', 'config', 'config.yaml')

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
            saved = self.save()
            if saved:
                print(f"配置已自动保存到 {self._config_path}")
        except Exception as e:
            print(f"自动保存失败: {e}")
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
            with open(self._config_path, 'r') as f:
                lock_file(f)
                loaded_data = yaml.safe_load(f) or {}
                unlock_file(f)

            # 分离数据和类型提示
            self._data = loaded_data.get('__data__', {})
            self._type_hints = loaded_data.get('__type_hints__', {})

            self._last_mtime = os.path.getmtime(self._config_path)
            print(f"配置已从 {self._config_path} 加载")
            return True
        except Exception as e:
            print(f"加载配置失败: {e}")
            # 即使加载失败，也要初始化数据，避免递归错误
            self._data = {}
            return False

    def save(self):
        """保存配置到文件（原子替换，兼容 Windows 临时文件占用）"""
        try:
            dir_path = os.path.dirname(self._config_path)
            if dir_path:
                os.makedirs(dir_path, exist_ok=True)

            save_data = {
                '__data__': self.to_dict(),
                '__type_hints__': self._type_hints
            }

            tmp_path = f"{self._config_path}.tmp"
            with open(tmp_path, 'w') as f:
                lock_file(f)
                yaml.dump(save_data, f, default_flow_style=False)
                unlock_file(f)

            os.replace(tmp_path, self._config_path)
            self._last_mtime = os.path.getmtime(self._config_path)
            return True
        except Exception as e:
            print(f"保存配置失败: {e}")
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
                print(f"监视配置出错: {e}")
                time.sleep(5)
        return

    def _cleanup(self):
        """清理资源"""
        self._stop_watcher.set()
        if self._autosave_timer:
            self._autosave_timer.cancel()
            self._perform_autosave()
        return

    def _convert_type(self, value: Any, target_type: Type) -> Any:
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
            if not hasattr(current, k):
                return self._convert_type(default, as_type)
            current = getattr(current, k)

        return self._convert_type(current, as_type)

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

        setattr(current, keys[-1], value)

        if autosave:
            self._schedule_autosave()
        return

    def get_type_hint(self, key: str) -> Optional[str]:
        """获取配置项的类型提示"""
        return self._type_hints.get(key)

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
        return Path(path_str)

    def update(self, updates: Dict[str, Any], autosave: bool = True):
        """批量更新配置值"""
        for key, value in updates.items():
            self.set(key, value, autosave=False)

        if autosave:
            self._schedule_autosave()
        return

    def get_config_path(self) -> str:
        """获取配置文件路径"""
        return self._config_path

    def generate_config_id(self) -> str:
        """生成唯一配置ID"""
        config_id = str(uuid.uuid4())
        return config_id

    def snapshot(self) -> Dict:
        """创建配置快照"""
        snapshot_data = {
            'data': self.to_dict(),
            'type_hints': self._type_hints.copy()
        }
        return snapshot_data

    def restore(self, snapshot: Dict):
        """从快照恢复配置"""
        self.from_dict(snapshot.get('data', {}))
        self._type_hints = snapshot.get('type_hints', {}).copy()
        self.save()
        return

    def temporary(self, changes: Dict[str, Any]):
        """临时修改配置的上下文管理器"""

        class TemporaryContext:
            def __init__(self, config, changes):
                self.config = config
                self.changes = changes
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

        return TemporaryContext(self, changes)


def get_config_manager(config_path: str = None,
                       watch: bool = False,
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
