# src/config_manager/core/manager.py
from __future__ import annotations
from datetime import datetime

import os
import threading
import atexit
import uuid
from pathlib import Path
from typing import Any, Dict, Optional, Type, Union
from collections.abc import Iterable, Mapping
from ..config_node import ConfigNode
from .path_resolver import PathResolver
from .file_operations import FileOperations
from .autosave_manager import AutosaveManager
from .watcher import FileWatcher
from .call_chain import CallChainTracker
from .path_configuration import PathConfigurationManager
from .cross_platform_paths import convert_to_multi_platform_config, get_platform_path
from ..logger import debug


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
        self._path_config_manager = None

        # 基本属性
        self._original_config_path = None
        self._config_path = None
        self._watch = False
        self._auto_create = True
        self._type_hints = {}
        self._first_start_time = None
        self._is_main_program = False  # 新增：标记是否为主程序
        
        # 多平台和测试模式支持
        self._base_dir = None  # 内部实际使用的 base_dir
        self._test_unique_id = None  # 测试模式唯一标识符
        self._test_mode = False  # 测试模式标志
        
        # 新增：重复初始化检测
        self._initialized = False
        self._initialization_lock = threading.Lock()

    def initialize(self, config_path: str, watch: bool, auto_create: bool, autosave_delay: float,
                   first_start_time: datetime = None) -> bool:
        """初始化配置管理器"""
        # 重复初始化检测
        with self._initialization_lock:
            if self._initialized:
                debug("配置管理器已经初始化过，跳过重复初始化")
                return True
            
            # 标记开始初始化
            self._initialized = True
        
        # 检查调用链显示开关
        from ..config_manager import ENABLE_CALL_CHAIN_DISPLAY

        # 确保_data已经存在（防御性编程）
        if not hasattr(self, '_data') or self._data is None:
            self._data = {}

        # 确保_type_hints也存在
        if not hasattr(self, '_type_hints'):
            self._type_hints = {}

        # 判断是否为主程序（传入了first_start_time参数）
        self._is_main_program = first_start_time is not None

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

        # 加载配置
        loaded = self._load()

        # 如果加载失败且配置文件存在，说明是解析错误，不应该覆盖
        if not loaded and os.path.exists(self._config_path):
            print(f"⚠️  配置文件存在但解析失败: {self._config_path}")
            print(f"⚠️  为保护原始配置，初始化失败")
            return False

        # 设置首次启动时间（无论配置是否加载成功都要设置）
        self._setup_first_start_time(first_start_time)

        # 将配置文件的绝对路径作为配置数据的一部分存储
        self._data['config_file_path'] = self._config_path

        if not loaded and not self._auto_create:
            return False

        # 注册清理函数
        atexit.register(self._cleanup)

        # 启动文件监视
        if watch and self._watcher:
            self._watcher.start(self._config_path, self._on_file_changed)

        # 自动初始化路径配置
        self.setup_project_paths()
        
        return True

    def setup_project_paths(self) -> None:
        """
        根据核心配置（base_dir, project_name等）生成并设置所有派生路径。
        这是一个明确的步骤，应在配置加载后由用户调用。
        """
        if not hasattr(self, '_path_config_manager') or self._path_config_manager is None:
            self._path_config_manager = PathConfigurationManager(self)
        self._path_config_manager.initialize_path_configuration()
        # 生成所有路径并自动创建目录
        self._path_config_manager.setup_project_paths()

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

        # 修复：None表示加载失败，空字典{}表示成功加载空配置
        if loaded is not None:
            self._data.clear()

            # 检查是否为标准格式（包含__data__节点）
            if '__data__' in loaded:
                # 标准格式：使用__data__节点下的数据
                raw_data = loaded.get('__data__', {})
                self._type_hints = loaded.get('__type_hints__', {})
                if ENABLE_CALL_CHAIN_DISPLAY:
                    print("检测到标准格式，加载__data__节点")
            else:
                # 原始格式：直接使用整个loaded数据，但排除内部键
                raw_data = {}
                for key, value in loaded.items():
                    # 排除ConfigManager的内部键
                    if not key.startswith('__'):
                        raw_data[key] = value
                self._type_hints = {}
                if ENABLE_CALL_CHAIN_DISPLAY:
                    print("检测到原始格式，直接加载配置数据")

            # 重建数据结构
            if raw_data:
                for key, value in raw_data.items():
                    if isinstance(value, dict):
                        self._data[key] = ConfigNode(value)
                    else:
                        self._data[key] = value

            if ENABLE_CALL_CHAIN_DISPLAY:
                print("配置加载完成")

            # 标记配置加载成功
            self._config_loaded_successfully = True
            
            # 更新 _base_dir
            self._update_base_dir()
            
            return True

        if ENABLE_CALL_CHAIN_DISPLAY:
            print("配置加载失败")

        # 标记配置加载失败
        self._config_loaded_successfully = False
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

        # 设置内部保存标志，避免文件监视器触发重新加载
        if self._watcher:
            self._watcher.set_internal_save_flag(True)

        data_to_save = {
            '__data__': self.to_dict(),
            '__type_hints__': self._type_hints
        }

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
            self._first_start_time if hasattr(self, '_first_start_time') and self._first_start_time else datetime.now(),
            self  # 传递配置管理器实例
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

        # 只有在成功加载过配置的情况下才安排自动保存
        if hasattr(self, '_config_loaded_successfully') and self._config_loaded_successfully:
            self._autosave_manager.schedule_save(self.save)
        return

    def _get_current_platform(self) -> str:
        """获取当前平台"""
        from .cross_platform_paths import get_cross_platform_manager
        manager = get_cross_platform_manager()
        return manager.get_current_os()

    def _generate_test_unique_id(self) -> str:
        """生成测试模式唯一标识符"""
        import uuid
        return uuid.uuid4().hex[:8]

    def _generate_test_base_dir(self) -> str:
        """生成跨平台测试模式的 base_dir 路径
        
        格式：
        - Windows: {系统临时目录}\\tests\\{YYYYMMDD}\\{HHMMSS}_{唯一标识符}
          例如: d:\\temp\\tests\\20250703\\143025_a1b2c3d4
        - Linux: {系统临时目录}/tests/{YYYYMMDD}/{HHMMSS}_{唯一标识符}
          例如: /tmp/tests/20250703/143025_a1b2c3d4
        """
        import tempfile
        from datetime import datetime
        
        # 获取系统临时目录（自动跨平台）
        temp_base = tempfile.gettempdir()
        
        # 生成时间标识
        now = datetime.now()
        date_str = now.strftime('%Y%m%d') 
        time_str = now.strftime('%H%M%S')
        
        # 生成唯一标识符（确保并发安全）
        if not self._test_unique_id:
            self._test_unique_id = self._generate_test_unique_id()
        
        # 跨平台路径组装：{系统临时目录}/tests/{日期}/{时间}_{UUID}
        test_path = os.path.join(
            temp_base, 'tests', date_str,
            f"{time_str}_{self._test_unique_id}"
        )
        
        # 使用 os.path.normpath 确保路径格式正确
        return os.path.normpath(test_path)

    def _update_base_dir(self):
        """更新内部 _base_dir（跨平台支持）"""
        if self._test_mode:
            # 测试模式：使用跨平台临时路径
            self._base_dir = self._generate_test_base_dir()
            
            # 设置测试环境变量
            os.environ['CONFIG_MANAGER_TEST_MODE'] = 'true'
            os.environ['CONFIG_MANAGER_TEST_BASE_DIR'] = self._base_dir
            
            # 创建测试目录（跨平台）
            os.makedirs(self._base_dir, exist_ok=True)
            
            debug(f"测试模式路径: {self._base_dir}")
        else:
            # 生产模式：从多平台配置选择当前平台
            base_dir_config = self._data.get('base_dir')
            if isinstance(base_dir_config, dict) or hasattr(base_dir_config, 'to_dict'):
                # 如果是 ConfigNode，转换为普通字典
                if hasattr(base_dir_config, 'to_dict'):
                    config_dict = base_dir_config.to_dict()
                else:
                    config_dict = base_dir_config
                platform_path = get_platform_path(config_dict, 'base_dir')
                current_platform = self._get_current_platform()
                
                # 如果当前平台路径为空，使用默认值
                if not platform_path:
                    if current_platform in ['ubuntu', 'linux']:
                        self._base_dir = os.path.expanduser('~/logs')
                    elif current_platform == 'windows':
                        self._base_dir = 'd:\\logs'
                    else:
                        self._base_dir = None
                else:
                    # 展开 ~ 路径（如果是 Linux/Ubuntu）
                    if current_platform in ['ubuntu', 'linux'] and platform_path.startswith('~'):
                        self._base_dir = os.path.expanduser(platform_path)
                    else:
                        self._base_dir = platform_path
            else:
                # 如果不是字典格式，直接使用原始值
                self._base_dir = base_dir_config
        
        # debug_mode 时在 _base_dir 后面加一层 'debug' 路径
        if hasattr(self, 'debug_mode') and self.debug_mode and self._base_dir:
            self._base_dir = os.path.join(self._base_dir, 'debug')

    def _regenerate_paths(self):
        """重新生成 config.paths 下的所有路径"""
        if hasattr(self, '_path_config_manager') and self._path_config_manager:
            # 重新设置项目路径
            self._path_config_manager.setup_project_paths()

    def _cleanup(self):
        """清理资源"""
        if self._watcher:
            self._watcher.stop()

        if self._autosave_manager:
            self._autosave_manager.cleanup()

        # 执行最后一次保存（只有在成功加载过配置的情况下才保存）
        try:
            if (hasattr(self, '_data') and self._data and
                    hasattr(self, '_config_loaded_successfully') and self._config_loaded_successfully):
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

        # 特殊处理base_dir：总是返回 _base_dir
        if key == 'base_dir':
            # 动态更新_base_dir以反映debug_mode变化
            self._update_base_dir()
            
            if hasattr(self, '_base_dir') and self._base_dir is not None:
                current = self._base_dir
            elif isinstance(current, dict) or hasattr(current, 'to_dict'):
                # 如果_base_dir未设置但有多平台配置，临时解析
                if hasattr(current, 'to_dict'):
                    config_dict = current.to_dict()
                else:
                    config_dict = current
                current = get_platform_path(config_dict, 'base_dir')
            # 如果都没有，返回原始值

        converted_value = self._convert_type(current, as_type)
        return converted_value

    def set(self, key: str, value: Any, autosave: bool = True, type_hint: Type = None):
        """设置配置值并自动保存，支持类型提示"""
        # 特殊处理debug_mode：不允许设置，因为它是动态属性
        if key == 'debug_mode':
            # 静默忽略debug_mode的设置，因为它应该总是动态获取
            return

        # 特殊处理first_start_time：如果只是first_start_time变化，不应该触发自动保存
        if key == 'first_start_time':
            # 检查是否只是first_start_time的变化
            existing_value = self._data.get('first_start_time')
            if existing_value == value:
                # 值没有变化，直接返回
                return
            # 值有变化，但first_start_time不应该触发自动保存
            autosave = False

        if key == 'base_dir' and isinstance(value, str):
            # 智能更新base_dir：只更新当前平台的值
            current_platform = self._get_current_platform()
            existing_base_dir = self._data.get('base_dir')
            
            if isinstance(existing_base_dir, dict) or hasattr(existing_base_dir, 'to_dict'):
                # 已有多平台配置，只更新当前平台
                if hasattr(existing_base_dir, 'to_dict'):
                    config_dict = existing_base_dir.to_dict()
                else:
                    config_dict = dict(existing_base_dir)
                
                # 更新当前平台的值
                config_dict[current_platform] = value
                value = ConfigNode(config_dict, _root=self)
            else:
                # 没有多平台配置，创建多平台配置
                try:
                    # 为当前平台设置新值，其他平台使用默认值
                    if current_platform in ['ubuntu', 'linux']:
                        config_dict = {'ubuntu': value, 'windows': 'd:\\logs'}
                    elif current_platform == 'windows':
                        config_dict = {'windows': value, 'ubuntu': '~/logs'}
                    else:
                        config_dict = {current_platform: value}
                    
                    value = ConfigNode(config_dict, _root=self)
                except Exception as e:
                    debug(f"创建多平台base_dir配置失败: {e}, 将其保留为字符串。")

        keys = key.split('.')
        current = self
        for k in keys[:-1]:
            if k not in current or not isinstance(current[k], ConfigNode):
                current[k] = ConfigNode(_root=self)
            current = current[k]
        
        current[keys[-1]] = value
        
        # base_dir 变化时同步更新 _base_dir 和重新生成路径
        if key == 'base_dir':
            # 更新内部 _base_dir（测试模式下忽略）
            if not self._test_mode:
                self._update_base_dir()
            
            # 重新生成 config.paths 下的所有路径
            self._regenerate_paths()
        
        if type_hint:
            self.set_type_hint(key, type_hint)
        
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

    def get_config_file_path(self) -> str:
        """获取配置文件的绝对路径（从配置数据中获取）"""
        config_file_path = self._data.get('config_file_path', self._config_path)
        return config_file_path

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

    def _setup_first_start_time(self, first_start_time: datetime = None):
        """设置首次启动时间"""
        from ..config_manager import ENABLE_CALL_CHAIN_DISPLAY

        # 检查配置中是否已经有first_start_time
        existing_time_str = self._data.get('first_start_time')

        if existing_time_str and first_start_time is None:
            # 如果配置中已经有时间，解析并使用它
            try:
                self._first_start_time = datetime.fromisoformat(existing_time_str)
                if ENABLE_CALL_CHAIN_DISPLAY:
                    print(f"从配置中读取首次启动时间: {self._first_start_time}")
                return
            except (ValueError, TypeError) as e:
                if ENABLE_CALL_CHAIN_DISPLAY:
                    print(f"解析配置中的首次启动时间失败: {e}")

        # 如果没有现有时间，使用传入的时间或当前时间
        if first_start_time is not None:
            # 如果传入的是字符串，先解析为datetime对象
            if isinstance(first_start_time, str):
                try:
                    self._first_start_time = datetime.fromisoformat(first_start_time)
                except (ValueError, TypeError):
                    # 如果解析失败，使用当前时间
                    self._first_start_time = datetime.now()
            else:
                self._first_start_time = first_start_time
            if ENABLE_CALL_CHAIN_DISPLAY:
                print(f"使用传入的首次启动时间: {self._first_start_time}")
        else:
            self._first_start_time = datetime.now()
            if ENABLE_CALL_CHAIN_DISPLAY:
                print(f"使用当前时间作为首次启动时间: {self._first_start_time}")

        # 保存到配置中
        self._data['first_start_time'] = self._first_start_time.isoformat()

        # 移除立即保存配置的调用，避免在初始化过程中重复保存
        # self.save()

        return

    def _initialize_path_configuration(self) -> None:
        """初始化路径配置"""
        # 此方法的内容已移至 setup_project_paths
        pass

    def _should_update_path_config(self, key: str) -> bool:
        """判断是否需要更新路径配置"""
        path_related_keys = [
            'base_dir', 'project_name', 'experiment_name',
            'debug_mode'
        ]
        return key in path_related_keys

    def _update_path_configuration(self) -> None:
        """更新路径配置"""
        if self._path_config_manager:
            try:
                # 清除缓存，确保使用最新配置
                self._path_config_manager.invalidate_cache()
                path_configs = self._path_config_manager.generate_all_paths()

                # 更新配置
                for key, value in path_configs.items():
                    self.set(key, value, autosave=False)

            except Exception as e:
                debug("警告: 路径配置更新失败: {}", e)

    def get_path_configuration_info(self) -> Dict[str, Any]:
        """获取路径配置信息"""
        if self._path_config_manager:
            return self._path_config_manager.get_path_info()
        return {}

    def create_path_directories(self, create_all: bool = False) -> Dict[str, bool]:
        """创建路径目录结构（已废弃，统一由setup_project_paths自动处理）"""
        return {}

    def update_debug_mode(self) -> None:
        """更新调试模式"""
        if self._path_config_manager:
            self._path_config_manager.update_debug_mode()

    def _is_path_configuration(self, key: str, value: Any) -> bool:
        """判断是否为路径配置

        Args:
            key: 配置键
            value: 配置值

        Returns:
            bool: 是否为路径配置
        """
        # 检查是否为字符串类型
        if not isinstance(value, str):
            return False

        # 检查是否为paths命名空间
        if key.startswith('paths.'):
            return True

        # 检查字段名是否包含路径关键词
        path_keywords = ['dir', 'path', 'directory', 'folder', 'location', 'root', 'base']
        key_lower = key.lower()
        if any(keyword in key_lower for keyword in path_keywords):
            # 进一步检查值是否像路径
            return self._looks_like_path(value)

        return False

    def _looks_like_path(self, value: str) -> bool:
        """判断字符串是否像路径

        Args:
            value: 字符串值

        Returns:
            bool: 是否像路径
        """
        if not value:
            return False

        # 检查是否包含路径分隔符
        if '/' in value or '\\' in value:
            return True

        # 检查是否为Windows盘符格式
        if len(value) >= 2 and value[1] == ':':
            return True

        return False

    def get_serializable_data(self):
        """获取可序列化的配置数据，用于多进程环境

        Returns:
            SerializableConfigData: 可序列化的配置数据对象
        """
        from ..serializable_config import create_serializable_config
        return create_serializable_config(self)

    def create_serializable_snapshot(self):
        """创建可序列化的配置快照

        Returns:
            SerializableConfigData: 可序列化的配置快照
        """
        return self.get_serializable_data()

    def is_pickle_serializable(self) -> bool:
        """检查配置管理器是否可以被pickle序列化

        Returns:
            bool: 是否可序列化（通常返回False，因为包含不可序列化的组件）
        """
        try:
            import pickle
            pickle.dumps(self)
            return True
        except Exception:
            return False

    def _convert_to_multi_platform_config(self, value: str) -> str:
        """将路径转换为多平台格式"""
        return convert_to_multi_platform_config(value)

    def _get_platform_path(self, key: str) -> str:
        """获取平台特定路径"""
        return get_platform_path(key)
