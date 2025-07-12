# src/config_manager/core/path_configuration.py
from __future__ import annotations
from datetime import datetime
from typing import Dict, Any, Tuple, Union
from pathlib import Path
import os
from ..config_node import ConfigNode
import tempfile

# 导入跨平台路径管理器
from .cross_platform_paths import get_cross_platform_manager
from ..logger import debug


class PathConfigurationError(Exception):
    """路径配置错误基类"""
    pass


class InvalidPathError(PathConfigurationError):
    """无效路径错误"""
    pass


class DirectoryCreationError(PathConfigurationError):
    """目录创建错误"""
    pass


class TimeParsingError(PathConfigurationError):
    """时间解析错误"""
    pass


class DebugDetector:
    """调试模式检测器"""
    
    @staticmethod
    def detect_debug_mode() -> bool:
        """检测当前是否为调试模式
        
        Returns:
            bool: True表示调试模式，False表示生产模式
        """
        # 首先检查环境变量
        if os.environ.get('CONFIG_MANAGER_DEBUG_MODE') == 'true':
            return True
            
        try:
            from is_debug import is_debug
            return is_debug()
        except ImportError:
            # 如果is_debug模块不可用，默认为生产模式
            return False
    
    @staticmethod
    def get_debug_status_info() -> Dict[str, Any]:
        """获取调试状态信息
        
        Returns:
            dict: 包含调试状态和相关信息的字典
        """
        debug_mode = DebugDetector.detect_debug_mode()
        return {
            'debug_mode': debug_mode,
            'is_debug_available': True,
            'detection_time': datetime.now().isoformat()
        }


class TimeProcessor:
    """时间处理器"""
    
    @staticmethod
    def parse_first_start_time(first_start_time: str) -> Tuple[str, str]:
        """解析首次启动时间
        
        Args:
            first_start_time: ISO格式的时间字符串
            
        Returns:
            tuple: (日期字符串YYYYMMDD, 时间字符串HHMMSS)
        """
        try:
            dt = datetime.fromisoformat(first_start_time.replace('Z', '+00:00'))
            return dt.strftime('%Y%m%d'), dt.strftime('%H%M%S')
        except (ValueError, AttributeError) as e:
            raise TimeParsingError(f"时间解析失败: {first_start_time}, 错误: {e}")
    
    @staticmethod
    def get_current_time_components() -> Tuple[str, str]:
        """获取当前时间组件
        
        Returns:
            tuple: (日期字符串YYYYMMDD, 时间字符串HHMMSS)
        """
        now = datetime.now()
        return now.strftime('%Y%m%d'), now.strftime('%H%M%S')
    
    @staticmethod
    def get_week_number(dt: datetime) -> str:
        """获取给定日期在一年中的第几周（两位数字格式）
        
        Args:
            dt: datetime对象
            
        Returns:
            str: 周数的两位数字字符串（如：01, 02, ..., 52）
        """
        year, week, _ = dt.isocalendar()
        return f"{week:02d}"
    
    @staticmethod
    def parse_time_with_week(time_str: str) -> Tuple[str, str, str, str, str]:
        """解析时间字符串，返回年、周、月、日、时间组件
        
        Args:
            time_str: ISO格式的时间字符串
            
        Returns:
            tuple: (年份YYYY, 周数WW, 月份MM, 日期DD, 时间HHMMSS)
        """
        try:
            dt = datetime.fromisoformat(time_str.replace('Z', '+00:00'))
            year = dt.strftime('%Y')
            week = TimeProcessor.get_week_number(dt)
            month = dt.strftime('%m')
            day = dt.strftime('%d')
            time = dt.strftime('%H%M%S')
            return year, week, month, day, time
        except (ValueError, AttributeError) as e:
            raise TimeParsingError(f"时间解析失败: {time_str}, 错误: {e}")


class PathGenerator:
    """路径生成器"""
    
    def __init__(self):
        """初始化路径生成器"""
        self._cross_platform_manager = get_cross_platform_manager()
    
    def generate_work_directory(
        self, 
        base_dir: Union[str, Dict[str, str]], 
        project_name: str, 
        experiment_name: str, 
        debug_mode: bool
    ) -> str:
        """生成工作目录路径
        
        Args:
            base_dir: 基础目录（字符串或多平台配置字典）
            project_name: 项目名称
            experiment_name: 实验名称
            debug_mode: 是否为调试模式
            
        Returns:
            str: 工作目录路径
        """
        # 处理多平台基础目录
        if isinstance(base_dir, dict):
            current_os = self._cross_platform_manager.get_current_os()
            base_path = base_dir.get(current_os, '')
            if not base_path:
                # 如果没有当前平台的路径，尝试使用ubuntu作为fallback
                base_path = base_dir.get('ubuntu', '')
            if not base_path:
                # 如果还是没有，使用第一个可用的路径
                base_path = next(iter(base_dir.values()), '')
        else:
            base_path = str(base_dir)
            
        # 标准化基础路径
        base_path = os.path.normpath(base_path)

        # 组合路径
        if debug_mode:
            work_dir = os.path.join(base_path, 'debug', project_name, experiment_name)
        else:
            work_dir = os.path.join(base_path, project_name, experiment_name)
            
        return work_dir
    
    def generate_checkpoint_directories(self, work_dir: str) -> Dict[str, str]:
        """生成检查点目录路径
        
        Args:
            work_dir: 工作目录
            
        Returns:
            dict: 检查点目录路径字典
        """
        work_path = Path(work_dir)
        
        checkpoint_dirs = {
            'paths.checkpoint_dir': str(work_path / 'checkpoint'),
            'paths.best_checkpoint_dir': str(work_path / 'checkpoint' / 'best')
        }
        
        return checkpoint_dirs
    
    def generate_log_directories(
        self, 
        work_dir: str, 
        date_str: str, 
        time_str: str,
        first_start_time_str: str = None
    ) -> Dict[str, str]:
        """生成日志目录路径
        
        Args:
            work_dir: 工作目录
            date_str: 日期字符串（YYYYMMDD）
            time_str: 时间字符串（HHMMSS）
            first_start_time_str: 原始时间字符串（ISO格式），用于计算tsb_logs_dir的周数路径
            
        Returns:
            dict: 日志目录路径字典
        """
        work_path = Path(work_dir)
        
        # 为tsb_logs_dir使用新的周数格式: yyyy/ww/mm/dd/HHMMSS
        if first_start_time_str:
            try:
                year, week, month, day, time = TimeProcessor.parse_time_with_week(first_start_time_str)
                tsb_logs_path = str(work_path / 'tsb_logs' / year / week / month / day / time)
            except Exception:
                # 如果解析失败，使用原有格式
                tsb_logs_path = str(work_path / 'tsb_logs' / date_str / time_str)
        else:
            # 没有原始时间信息，使用原有格式
            tsb_logs_path = str(work_path / 'tsb_logs' / date_str / time_str)
        
        log_dirs = {
            'paths.tsb_logs_dir': tsb_logs_path,
            'paths.log_dir': str(work_path / 'logs' / date_str / time_str)
        }
        
        return log_dirs
    
    def generate_debug_directory(self, work_dir: str) -> Dict[str, str]:
        """生成调试目录路径
        
        Args:
            work_dir: 工作目录
            
        Returns:
            dict: 调试目录路径字典
        """
        work_path = Path(work_dir)
        
        debug_dirs = {
            'paths.debug_dir': str(work_path / 'debug')
        }
        
        return debug_dirs
    
    def generate_tensorboard_directory(self, work_dir: str) -> Dict[str, str]:
        """生成TensorBoard目录路径
        
        Args:
            work_dir: 工作目录
            
        Returns:
            dict: TensorBoard目录路径字典
        """
        work_path = Path(work_dir)
        
        tensorboard_dirs = {
            'paths.tensorboard_dir': str(work_path / 'tensorboard')
        }
        
        return tensorboard_dirs
    
    def generate_backup_directory(
        self, 
        work_dir: str, 
        date_str: str, 
        time_str: str
    ) -> Dict[str, str]:
        """生成备份目录路径
        
        Args:
            work_dir: 工作目录
            date_str: 日期字符串（YYYYMMDD）
            time_str: 时间字符串（HHMMSS）
            
        Returns:
            dict: 备份目录路径字典
        """
        work_path = Path(work_dir)
        
        backup_dirs = {
            'paths.backup_dir': str(work_path / 'backup' / date_str / time_str)
        }
        
        return backup_dirs


class PathValidator:
    """路径验证器"""
    
    @staticmethod
    def validate_base_dir(base_dir: str) -> bool:
        """验证基础目录"""
        if base_dir is None or base_dir == '':
            return False
        
        try:
            # 检查路径是否有效
            Path(base_dir)
            return True
        except Exception:
            return False
    
    @staticmethod
    def validate_path_format(path: str) -> bool:
        """验证路径格式
        
        Args:
            path: 路径字符串
            
        Returns:
            bool: 验证结果
        """
        if not path:
            return False
        
        try:
            path_obj = Path(path)
            # 检查路径是否有效
            path_obj.resolve()
            return True
        except (OSError, RuntimeError, ValueError):
            return False
    
    @staticmethod
    def validate_directory_permissions(path: str) -> bool:
        """验证目录权限
        
        Args:
            path: 路径字符串
            
        Returns:
            bool: 验证结果
        """
        if not path:
            return False
        
        try:
            path_obj = Path(path)
            
            # 如果目录不存在，检查父目录权限
            if not path_obj.exists():
                parent = path_obj.parent
                if parent.exists():
                    return os.access(parent, os.W_OK)
                else:
                    # 递归检查父目录权限
                    return PathValidator.validate_directory_permissions(str(parent))
            
            # 目录存在，检查读写权限
            return os.access(path_obj, os.R_OK | os.W_OK)
            
        except Exception:
            return False


class DirectoryCreator:
    """目录创建器"""
    
    @staticmethod
    def create_directory(path: str, exist_ok: bool = True) -> bool:
        """创建目录，仅允许被setup_project_paths调用"""
        try:
            os.makedirs(path, exist_ok=exist_ok)
            return True
        except Exception as e:
            raise DirectoryCreationError(f"目录创建失败: {path}, {e}")

    def create_path_structure(self, paths: Dict[str, str]) -> Dict[str, bool]:
        """批量创建路径结构，仅允许被setup_project_paths调用"""
        results = {}
        for key, path in paths.items():
            results[key] = self.create_directory(path)
        return results


class ConfigUpdater:
    """配置更新器"""
    
    def __init__(self, config_manager):
        """初始化配置更新器
        
        Args:
            config_manager: 配置管理器实例
        """
        self._config_manager = config_manager
    
    def update_path_configurations(self, path_configs: Dict[str, Any]) -> None:
        """更新路径配置"""
        for key, value in path_configs.items():
            # 这里的key现在是 'paths'
            self._config_manager.set(key, value, autosave=False)
    
    def update_debug_mode(self, debug_mode: bool) -> None:
        """更新调试模式配置
        
        Args:
            debug_mode: 调试模式标志
        """
        # debug_mode是动态属性，不需要更新到配置中
        pass


class PathConfigurationManager:
    """路径配置管理器"""
    
    # 默认配置
    DEFAULT_PATH_CONFIG = {
        'base_dir': {
            'windows': tempfile.gettempdir(),
            'ubuntu': tempfile.gettempdir()
        },
        'project_name': 'project_name',
        'experiment_name': 'experiment_name',
        'first_start_time': None,  # 自动生成
    }
    
    def __init__(self, config_manager):
        """初始化路径配置管理器
        
        Args:
            config_manager: 配置管理器实例
        """
        self._config_manager = config_manager
        self._debug_detector = DebugDetector()
        self._path_generator = PathGenerator()
        self._time_processor = TimeProcessor()
        self._path_validator = PathValidator()
        self._directory_creator = DirectoryCreator()
        self._config_updater = ConfigUpdater(config_manager)
        self._cross_platform_manager = get_cross_platform_manager()
        
        # 缓存相关
        self._path_cache = {}
        self._cache_valid = False
    
    def initialize_path_configuration(self) -> None:
        """初始化路径配置"""
        try:
            # 设置默认值
            self._set_default_values()
            
            # 确保first_start_time存在
            self._ensure_first_start_time()
            
            # 处理is_debug导入错误
            self._handle_is_debug_import_error()
            
            # 更新调试模式
            self.update_debug_mode()
            
            # 生成所有路径
            path_configs = self.generate_all_paths()
            
            # 修复：直接设置到_data中，避免触发__setattr__和自动保存
            if not hasattr(self._config_manager, 'paths'):
                # 如果paths属性不存在，直接创建
                self._config_manager._data['paths'] = ConfigNode(path_configs.get('paths', {}), _root=self._config_manager)
            else:
                # 如果paths属性已存在，直接更新其_data
                if hasattr(self._config_manager.paths, '_data'):
                    self._config_manager.paths._data.clear()
                    self._config_manager.paths._data.update(path_configs.get('paths', {}))
                else:
                    # 如果paths没有_data属性，重新创建
                    self._config_manager._data['paths'] = ConfigNode(path_configs.get('paths', {}), _root=self._config_manager)

        except Exception as e:
            # 其他错误，不影响主流程
            debug("⚠️  路径配置初始化部分失败: {}", e)
            # 尝试使用最小配置
            try:
                self._cross_platform_manager.get_current_os()
                default_base_dir = self._cross_platform_manager.get_default_path('base_dir')
                
                path_configs = {
                    'paths.work_dir': f'{default_base_dir}/default',
                    'paths.log_dir': f'{default_base_dir}/default/logs',
                    'paths.data_dir': f'{default_base_dir}/default/data'
                }
                self._config_updater.update_path_configurations(path_configs)
            except Exception as fallback_e:
                debug("⚠️  备用路径配置也失败: {}", fallback_e)
    
    def _set_default_values(self) -> None:
        """设置默认配置值"""
        # test_mode下不设置默认值
        if self._config_manager.is_test_mode():
            return
            
        # 为必需的配置项设置默认值，如果它们不存在
        # 修复：使用get方法检查而不是属性访问，避免覆盖已有值
        try:
            base_dir = self._config_manager.get('base_dir')
            if base_dir is None:
                # 使用多平台默认配置
                self._config_manager.set('base_dir', self.DEFAULT_PATH_CONFIG['base_dir'], autosave=False)
        except (AttributeError, KeyError):
            self._config_manager.set('base_dir', self.DEFAULT_PATH_CONFIG['base_dir'], autosave=False)
            
        try:
            project_name = self._config_manager.get('project_name')
            if project_name is None:
                self._config_manager.set('project_name', self.DEFAULT_PATH_CONFIG['project_name'], autosave=False)
        except (AttributeError, KeyError):
            self._config_manager.set('project_name', self.DEFAULT_PATH_CONFIG['project_name'], autosave=False)
        
        try:
            experiment_name = self._config_manager.get('experiment_name')
            if experiment_name is None:
                self._config_manager.set('experiment_name', self.DEFAULT_PATH_CONFIG['experiment_name'], autosave=False)
        except (AttributeError, KeyError):
            self._config_manager.set('experiment_name', self.DEFAULT_PATH_CONFIG['experiment_name'], autosave=False)
    
    def _ensure_first_start_time(self) -> None:
        """确保first_start_time存在"""
        try:
            # 尝试访问first_start_time属性
            self._config_manager.first_start_time
        except AttributeError:
            # 属性不存在，设置当前时间
            current_time = datetime.now().isoformat()
            self._config_manager.set('first_start_time', current_time)
    
    def _handle_is_debug_import_error(self) -> None:
        """处理is_debug模块导入错误"""
        import importlib.util
        if importlib.util.find_spec("is_debug") is None:
            debug("⚠️  is_debug模块不可用，默认使用生产模式")
    
    def update_debug_mode(self) -> None:
        """更新调试模式"""
        self._debug_detector.detect_debug_mode()
        # debug_mode是动态属性，不需要更新到配置中
    
    def generate_all_paths(self) -> Dict[str, str]:
        """生成所有路径配置
        
        Returns:
            dict: 路径配置字典
        """
        if self._cache_valid:
            return self._path_cache.copy()
        
        path_configs = self._generate_paths_internal()
        self._path_cache = path_configs.copy()
        self._cache_valid = True
        
        return path_configs
    
    def _generate_paths_internal(self) -> Dict[str, str]:
        """内部路径生成方法"""
        # 安全获取基础配置，使用get方法提供默认值
        if self._config_manager.is_test_mode():
            try:
                base_dir = self._config_manager.base_dir
            except AttributeError:
                base_dir = '/tmp/tests'
            try:
                project_name = self._config_manager.project_name
            except AttributeError:
                project_name = 'test_project'
            try:
                experiment_name = self._config_manager.experiment_name
            except AttributeError:
                experiment_name = 'test_experiment'
            # 在test_mode下也使用DebugDetector检测debug_mode
            debug_mode = self._debug_detector.detect_debug_mode()
            try:
                first_start_time = self._config_manager.first_start_time
            except AttributeError:
                first_start_time = datetime.now().isoformat()
        else:
            # 安全获取基础配置，使用get方法提供默认值
            try:
                base_dir = self._config_manager.base_dir
            except AttributeError:
                base_dir = self.DEFAULT_PATH_CONFIG['base_dir']
            
            try:
                project_name = self._config_manager.project_name
            except AttributeError:
                project_name = 'default_project'
            
            try:
                experiment_name = self._config_manager.experiment_name
            except AttributeError:
                experiment_name = 'default_experiment'
            
            try:
                debug_mode = self._config_manager.debug_mode
            except AttributeError:
                debug_mode = False
            
            try:
                first_start_time = self._config_manager.first_start_time
            except AttributeError:
                first_start_time = datetime.now().isoformat()
        
        # 处理base_dir，确保它是字符串
        if hasattr(base_dir, 'get_platform_path'):
            # 如果是ConfigNode对象，获取当前平台的路径
            current_os = self._cross_platform_manager.get_current_os()
            base_dir = base_dir.get_platform_path(current_os)
        elif isinstance(base_dir, dict):
            # 如果是字典，获取当前平台的路径
            current_os = self._cross_platform_manager.get_current_os()
            base_dir = base_dir.get(current_os, '')
            if not base_dir:
                base_dir = base_dir.get('ubuntu', '')
            if not base_dir:
                base_dir = next(iter(base_dir.values()), '')
        
        # 生成工作目录
        work_dir = self._path_generator.generate_work_directory(
            base_dir, project_name, experiment_name, debug_mode
        )
        
        # 生成检查点目录
        checkpoint_dirs = self._path_generator.generate_checkpoint_directories(work_dir)
        
        # 生成调试目录
        debug_dirs = self._path_generator.generate_debug_directory(work_dir)
        
        # 生成TensorBoard目录
        tensorboard_dirs = self._path_generator.generate_tensorboard_directory(work_dir)
        
        # 解析时间组件
        if first_start_time:
            try:
                date_str, time_str = self._time_processor.parse_first_start_time(first_start_time)
            except Exception:
                # 如果时间解析失败，使用当前时间
                date_str, time_str = self._time_processor.get_current_time_components()
        else:
            date_str, time_str = self._time_processor.get_current_time_components()
        
        # 生成日志目录
        log_dirs = self._path_generator.generate_log_directories(work_dir, date_str, time_str, first_start_time)
        
        # 生成备份目录
        backup_dirs = self._path_generator.generate_backup_directory(work_dir, date_str, time_str)
        
        # 合并所有路径配置
        path_configs = {
            'work_dir': work_dir,
            **{k.replace('paths.', ''): v for k, v in checkpoint_dirs.items()},
            **{k.replace('paths.', ''): v for k, v in debug_dirs.items()},
            **{k.replace('paths.', ''): v for k, v in tensorboard_dirs.items()},
            **{k.replace('paths.', ''): v for k, v in log_dirs.items()},
            **{k.replace('paths.', ''): v for k, v in backup_dirs.items()}
        }
        
        return {'paths': path_configs}
    
    def validate_path_configuration(self) -> bool:
        """验证路径配置"""
        # 安全验证基础目录
        try:
            base_dir = self._config_manager.base_dir
        except AttributeError:
            base_dir = self.DEFAULT_PATH_CONFIG['base_dir']
            
        if not self._path_validator.validate_base_dir(base_dir):
            return False
        
        # 验证生成的路径
        try:
            path_configs = self.generate_all_paths()
            if 'paths' not in path_configs:
                return False
            for path in path_configs['paths'].values():
                if not self._path_validator.validate_path_format(path):
                    return False
        except Exception as e:
            print(f"路径配置验证失败: {e}")
            return False
        
        return True
    
    def create_directories(self, create_all: bool = False) -> Dict[str, bool]:
        """创建目录结构
        
        Args:
            create_all: 是否创建所有目录
            
        Returns:
            dict: 创建结果字典
        """
        if create_all:
            path_configs = self.generate_all_paths()
            return self._directory_creator.create_path_structure(path_configs)
        else:
            # 只创建工作目录
            work_dir = self.generate_all_paths().get('paths.work_dir', '')
            if work_dir:
                success = self._directory_creator.create_directory(work_dir)
                return {'paths.work_dir': success}
            return {}
    
    def invalidate_cache(self) -> None:
        """使缓存失效"""
        self._cache_valid = False
        self._path_cache.clear()
    
    def get_path_info(self) -> Dict[str, Any]:
        """获取路径配置信息
        
        Returns:
            dict: 路径配置信息
        """
        try:
            base_dir = self._config_manager.base_dir
        except AttributeError:
            base_dir = self.DEFAULT_PATH_CONFIG['base_dir']
            
        try:
            project_name = self._config_manager.project_name
        except AttributeError:
            project_name = 'default_project'
            
        try:
            experiment_name = self._config_manager.experiment_name
        except AttributeError:
            experiment_name = 'default_experiment'
            
        try:
            debug_mode = self._config_manager.debug_mode
        except AttributeError:
            debug_mode = False
        
        return {
            'current_os': self._cross_platform_manager.get_current_os(),
            'os_family': self._cross_platform_manager.get_os_family(),
            'base_dir': base_dir,
            'project_name': project_name,
            'experiment_name': experiment_name,
            'debug_mode': debug_mode,
            'platform_info': self._cross_platform_manager.get_platform_info(),
            'generated_paths': self.generate_all_paths()
        }
    
    def setup_project_paths(self) -> None:
        """生成所有路径并自动创建目录，仅对'_dir'结尾的字段自动创建目录"""
        
        # 1. 确保向后兼容性：同步work_dir字段并创建目录
        self._config_manager.work_dir = self._config_manager.paths.work_dir
        # 创建work_dir目录
        os.makedirs(self._config_manager.paths.work_dir, exist_ok=True)
        
        def _create_dirs_for_fields(node, visited=None):
            if visited is None:
                visited = set()
            node_id = id(node)
            if node_id in visited:
                return
            visited.add(node_id)
            if isinstance(node, dict):
                items = node.items()
            elif hasattr(node, '_data') and isinstance(node._data, dict):
                items = node._data.items()
            else:
                return
            for key, value in items:
                if isinstance(key, str) and key.endswith('_dir') and isinstance(value, str) and value:
                    try:
                        os.makedirs(value, exist_ok=True)
                    except PermissionError:
                        # 权限错误时记录警告但不抛出异常
                        print(f"⚠️  跳过目录创建 (权限不足): {value}")
                    except Exception as e:
                        # 其他错误仍然抛出异常
                        raise DirectoryCreationError(f"目录创建失败: {value}, {e}")
                elif isinstance(value, dict):
                    _create_dirs_for_fields(value, visited)
                elif hasattr(value, '_data') and isinstance(value._data, dict):
                    _create_dirs_for_fields(value, visited)
        # 递归入口直接指向config.paths._data
        if hasattr(self._config_manager, 'paths') and hasattr(self._config_manager.paths, '_data'):
            _create_dirs_for_fields(self._config_manager.paths._data)
        
        # 2. 路径创建完成后，再次确保work_dir字段同步（防止paths.work_dir在过程中被更新）
        self._config_manager.work_dir = self._config_manager.paths.work_dir 