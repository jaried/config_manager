# src/config_manager/core/manager.py
from __future__ import annotations
from datetime import datetime

import os
import threading
import atexit
import uuid
from pathlib import Path
from typing import Any, Dict, Optional, Type
from collections.abc import Iterable, Mapping
from ..config_node import ConfigNode
from .path_resolver import PathResolver
from .file_operations import FileOperations
from .autosave_manager import AutosaveManager
from .watcher import FileWatcher
from .call_chain import CallChainTracker


class ConfigManagerCore(ConfigNode):
    """配置管理器核心实现类"""

    def __init__(self):
        # 正确初始化ConfigNode，确保_data属性存在
        super().__init__()

        # 初始化组件（延迟初始化）
        self._path_resolver = None
        self._file_ops = None
        self._autosave_manager = None
        self._watcher = None
        self._call_chain_tracker = None

        # 基本属性
        self._original_config_path = None
        self._config_path = None
        self._watch = False
        self._auto_create = True
        self._type_hints = {}
        self._first_start_time = None

    def initialize(self, config_path: str, watch: bool, auto_create: bool, autosave_delay: float) -> bool:
        """初始化配置管理器"""
        # 检查调用链显示开关
        from ..config_manager import ENABLE_CALL_CHAIN_DISPLAY

        # 确保_data已经存在（防御性编程）
        if not hasattr(self, '_data'):
            self._data = {}

        # 确保_type_hints也存在
        if not hasattr(self, '_type_hints'):
            self._type_hints = {}

        # 初始化各个组件
        self._path_resolver = PathResolver()
        self._file_ops = FileOperations()
        self._autosave_manager = AutosaveManager(autosave_delay)
        self._watcher = FileWatcher() if watch else None
        self._call_chain_tracker = CallChainTracker()

        # 根据开关决定是否测试调用链追踪器
        if ENABLE_CALL_CHAIN_DISPLAY:
            print("=== 调用链追踪器测试 ===")
            try:
                test_chain = self._call_chain_tracker.get_call_chain()
                print(f"初始化时调用链: {test_chain}")
            except Exception as e:
                print(f"调用链追踪器测试失败: {e}")
                import traceback
                traceback.print_exc()

        # 设置基本属性
        self._original_config_path = config_path
        self._config_path = self._path_resolver.resolve_config_path(config_path)
        self._watch = watch
        self._auto_create = auto_create

        print(f"配置路径解析: {config_path} -> {self._config_path}")

        # 加载配置
        loaded = self._load()
        if not loaded and not self._auto_create:
            return False

        # 设置首次启动时间
        self._setup_first_start_time()

        # 注册清理函数
        atexit.register(self._cleanup)

        # 启动文件监视
        if watch and self._watcher:
            self._watcher.start(self._config_path, self._on_file_changed)

        return True

    def _setup_first_start_time(self):
        """设置或获取首次启动时间"""
        from ..config_manager import ENABLE_CALL_CHAIN_DISPLAY

        if ENABLE_CALL_CHAIN_DISPLAY:
            print("=== 设置首次启动时间 ===")

        # 尝试从配置中获取first_start_time
        if hasattr(self, '_data') and 'first_start_time' in self._data:
            try:
                time_str = self._data['first_start_time']
                self._first_start_time = datetime.fromisoformat(time_str)
                if ENABLE_CALL_CHAIN_DISPLAY:
                    print(f"从配置加载首次启动时间: {self._first_start_time}")
                return
            except (ValueError, TypeError):
                if ENABLE_CALL_CHAIN_DISPLAY:
                    print("配置中的首次启动时间格式错误")

        # 获取调用模块的start_time
        if not hasattr(self, '_first_start_time') or self._first_start_time is None:
            try:
                self._first_start_time = self._call_chain_tracker.get_caller_start_time()
                if ENABLE_CALL_CHAIN_DISPLAY:
                    print(f"从调用链获取首次启动时间: {self._first_start_time}")
            except Exception as e:
                if ENABLE_CALL_CHAIN_DISPLAY:
                    print(f"获取调用模块start_time失败: {e}")
                self._first_start_time = datetime.now()
                if ENABLE_CALL_CHAIN_DISPLAY:
                    print(f"使用当前时间作为首次启动时间: {self._first_start_time}")

        # 保存到配置中
        if hasattr(self, '_data'):
            self._data['first_start_time'] = self._first_start_time.isoformat()
            if ENABLE_CALL_CHAIN_DISPLAY:
                print(f"首次启动时间已保存到配置")
        return

    def _load(self):
        """加载配置文件"""
        from ..config_manager import ENABLE_CALL_CHAIN_DISPLAY

        if ENABLE_CALL_CHAIN_DISPLAY:
            print(f"=== 开始加载配置文件: {self._config_path} ===")

        # 根据开关决定是否显示调用链
        if ENABLE_CALL_CHAIN_DISPLAY:
            try:
                load_call_chain = self._call_chain_tracker.get_call_chain()
                print(f"加载配置时的调用链: {load_call_chain}")
            except Exception as e:
                print(f"获取加载调用链失败: {e}")

        loaded = self._file_ops.load_config(
            self._config_path,
            self._auto_create,
            self._call_chain_tracker
        )

        if loaded:
            self._data.clear()
            raw_data = loaded.get('__data__', {})
            if ENABLE_CALL_CHAIN_DISPLAY:
                print(f"加载的原始数据: {raw_data}")

            # 重建数据结构
            if raw_data:
                for key, value in raw_data.items():
                    if isinstance(value, dict):
                        self._data[key] = ConfigNode(value)
                    else:
                        self._data[key] = value

            self._type_hints = loaded.get('__type_hints__', {})
            if ENABLE_CALL_CHAIN_DISPLAY:
                print(f"配置加载完成，_data内容: {self._data}")
            return True

        if ENABLE_CALL_CHAIN_DISPLAY:
            print("配置加载失败")
        return False

    def save(self):
        """保存配置到文件"""
        from ..config_manager import ENABLE_CALL_CHAIN_DISPLAY

        if ENABLE_CALL_CHAIN_DISPLAY:
            print("=== 开始保存配置 ===")

        # 根据开关决定是否显示保存时的调用链
        if ENABLE_CALL_CHAIN_DISPLAY:
            try:
                save_call_chain = self._call_chain_tracker.get_call_chain()
                print(f"保存配置时的调用链: {save_call_chain}")
            except Exception as e:
                print(f"获取保存调用链失败: {e}")

        data_to_save = {
            '__data__': self.to_dict(),
            '__type_hints__': self._type_hints
        }

        if ENABLE_CALL_CHAIN_DISPLAY:
            print(f"准备保存的数据: {data_to_save}")

        saved = self._file_ops.save_config(
            self._config_path,
            data_to_save,
            self._get_backup_path()
        )

        if ENABLE_CALL_CHAIN_DISPLAY:
            print(f"保存结果: {saved}")
        return saved

    def reload(self):
        """重新加载配置"""
        from ..config_manager import ENABLE_CALL_CHAIN_DISPLAY

        if ENABLE_CALL_CHAIN_DISPLAY:
            print("=== 重新加载配置 ===")

        # 根据开关决定是否显示重新加载时的调用链
        if ENABLE_CALL_CHAIN_DISPLAY:
            try:
                reload_call_chain = self._call_chain_tracker.get_call_chain()
                print(f"重新加载配置时的调用链: {reload_call_chain}")
            except Exception as e:
                print(f"获取重新加载调用链失败: {e}")

        reloaded = self._load()
        if ENABLE_CALL_CHAIN_DISPLAY:
            print(f"重新加载结果: {reloaded}")
        return reloaded

    def _get_backup_path(self) -> str:
        """获取备份路径"""
        return self._file_ops.get_backup_path(
            self._config_path,
            self._first_start_time if hasattr(self, '_first_start_time') and self._first_start_time else datetime.now()
        )

    def _on_file_changed(self):
        """文件变化回调"""
        from ..config_manager import ENABLE_CALL_CHAIN_DISPLAY

        print("检测到配置文件变化，重新加载...")

        # 根据开关决定是否显示文件变化时的调用链
        if ENABLE_CALL_CHAIN_DISPLAY:
            try:
                change_call_chain = self._call_chain_tracker.get_call_chain()
                print(f"文件变化回调的调用链: {change_call_chain}")
            except Exception as e:
                print(f"获取文件变化调用链失败: {e}")

        self.reload()
        return

    def _schedule_autosave(self):
        """安排自动保存"""
        from ..config_manager import ENABLE_CALL_CHAIN_DISPLAY

        # 根据开关决定是否显示自动保存调度时的调用链
        if ENABLE_CALL_CHAIN_DISPLAY:
            try:
                autosave_call_chain = self._call_chain_tracker.get_call_chain()
                print(f"安排自动保存时的调用链: {autosave_call_chain}")
            except Exception as e:
                print(f"获取自动保存调用链失败: {e}")

        self._autosave_manager.schedule_save(self.save)
        return

    def _cleanup(self):
        """清理资源"""
        if self._watcher:
            self._watcher.stop()

        if self._autosave_manager:
            self._autosave_manager.cleanup()

        # 执行最后一次保存
        try:
            if hasattr(self, '_data') and self._data:
                self.save()
        except Exception as e:
            print(f"清理时保存配置失败: {str(e)}")

        # 清理数据
        if hasattr(self, '_data'):
            self._data.clear()
        return

    # ========== 类型转换和配置访问方法 ==========

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

        # 设置值
        final_key = keys[-1]
        if isinstance(value, dict):
            setattr(current, final_key, ConfigNode(value))
        else:
            if hasattr(current, '_data'):
                current._data[final_key] = value
            else:
                setattr(current, final_key, value)

        if autosave:
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
        """批量更新配置值"""
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

    # ========== 快照和恢复功能 ==========

    def snapshot(self) -> Dict:
        """创建配置快照"""
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
        self._data.clear()

        snapshot_data = snapshot.get('data', {})
        for key, value in snapshot_data.items():
            if isinstance(value, dict):
                self._data[key] = ConfigNode(value)
            else:
                self._data[key] = value

        self._type_hints = snapshot.get('type_hints', {}).copy()
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
                return

        context = TemporaryContext(self, temp_changes)
        return context

    # ========== 构建方法 ==========

    @classmethod
    def build(cls, obj: Any) -> Any:
        """构建对象，递归转换嵌套结构"""
        # 如果已经是ConfigNode，直接返回，避免递归
        if isinstance(obj, ConfigNode):
            return obj

        # 如果是Mapping类型（字典等），转换为ConfigNode
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