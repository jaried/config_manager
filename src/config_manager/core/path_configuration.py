# src/config_manager/core/path_configuration.py
from __future__ import annotations
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple, Union
from pathlib import Path
import os
import re
from config_manager.config_node import ConfigNode

# 导入跨平台路径管理器
from .cross_platform_paths import get_cross_platform_manager, get_platform_path
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
            tuple: (日期字符串, 时间字符串)
        """
        try:
            dt = datetime.fromisoformat(first_start_time.replace('Z', '+00:00'))
            date_str = TimeProcessor.format_date(dt)
            time_str = TimeProcessor.format_time(dt)
            return date_str, time_str
        except (ValueError, AttributeError) as e:
            raise TimeParsingError(f"时间解析失败: {first_start_time}, 错误: {e}")
    
    @staticmethod
    def format_date(dt: datetime) -> str:
        """格式化日期
        
        Args:
            dt: datetime对象
            
        Returns:
            str: YYYY-MM-DD格式的日期字符串
        """
        return dt.strftime('%Y-%m-%d')
    
    @staticmethod
    def format_time(dt: datetime) -> str:
        """格式化时间
        
        Args:
            dt: datetime对象
            
        Returns:
            str: HHMMSS格式的时间字符串
        """
        return dt.strftime('%H%M%S')
    
    @staticmethod
    def get_current_time_components() -> Tuple[str, str]:
        """获取当前时间组件
        
        Returns:
            tuple: (日期字符串, 时间字符串)
        """
        now = datetime.now()
        return TimeProcessor.format_date(now), TimeProcessor.format_time(now)


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
        """生成工作目录，确保跨平台兼容性"""
        
        # 处理多平台基础目录
        if isinstance(base_dir, dict):
            current_os = get_cross_platform_manager().get_current_os()
            base_path = base_dir.get(current_os, base_dir.get('linux'))
        else:
            base_path = base_dir
            
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
        time_str: str
    ) -> Dict[str, str]:
        """生成日志目录路径
        
        Args:
            work_dir: 工作目录
            date_str: 日期字符串（YYYY-MM-DD）
            time_str: 时间字符串（HHMMSS）
            
        Returns:
            dict: 日志目录路径字典
        """
        work_path = Path(work_dir)
        
        log_dirs = {
            'paths.tsb_logs_dir': str(work_path / 'tsb_logs' / date_str / time_str),
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


class PathValidator:
    """路径验证器"""
    
    @staticmethod
    def validate_base_dir(base_dir: Union[str, Dict[str, str]]) -> bool:
        """验证基础目录
        
        Args:
            base_dir: 基础目录（字符串或多平台配置字典）
            
        Returns:
            bool: 验证结果
        """
        try:
            # 获取当前平台的路径
            platform_path = get_platform_path(base_dir, 'base_dir')
            
            if not platform_path:
                return False
            
            # 检查路径格式
            path_obj = Path(platform_path)
            
            # 检查是否为绝对路径
            if not path_obj.is_absolute():
                return False
            
            # 检查路径是否有效
            try:
                path_obj.resolve()
                return True
            except (OSError, RuntimeError):
                return False
                
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
        """创建目录
        
        Args:
            path: 目录路径
            exist_ok: 如果目录已存在是否不报错
            
        Returns:
            bool: 创建是否成功
        """
        try:
            Path(path).mkdir(parents=True, exist_ok=exist_ok)
            return True
        except (OSError, PermissionError, ValueError) as e:
            debug("目录创建失败: {}, 错误: {}", path, e)
            return False
    
    def create_path_structure(self, paths: Dict[str, str]) -> Dict[str, bool]:
        """创建路径结构
        
        Args:
            paths: 路径配置字典
            
        Returns:
            dict: 创建结果字典
        """
        results = {}
        
        for key, path in paths.items():
            if path:
                results[key] = self.create_directory(path)
            else:
                results[key] = False
        
        return results


class ConfigUpdater:
    """配置更新器"""
    
    def __init__(self, config_manager):
        """初始化配置更新器
        
        Args:
            config_manager: 配置管理器实例
        """
        self._config_manager = config_manager
    
    def update_path_configurations(self, path_configs: Dict[str, str]) -> None:
        """更新路径配置
        
        Args:
            path_configs: 路径配置字典
        """
        for key, value in path_configs.items():
            if key.startswith('paths.'):
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
            'windows': 'd:\\logs',
            'linux': '/home/tony/logs',
            'ubuntu': '/home/tony/logs',
            'macos': '/Users/tony/logs'
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
            
            # 创建目录结构
            creation_results = self._directory_creator.create_path_structure(path_configs)
            
            # 记录目录创建结果
            for key, success in creation_results.items():
                if not success:
                    debug("警告: 目录创建失败 {}: {}", key, path_configs.get(key))
            
            # 更新配置
            self._config_updater.update_path_configurations(path_configs)
            
            # 移除保存配置的调用，避免在初始化过程中重复保存
            # self._config_manager.save()
            
        except Exception as e:
            # 其他错误，不影响主流程
            debug("⚠️  路径配置初始化部分失败: {}", e)
            # 尝试使用最小配置
            try:
                current_os = self._cross_platform_manager.get_current_os()
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
        try:
            self._config_manager.base_dir
        except AttributeError:
            # 使用多平台默认配置
            self._config_manager.set('base_dir', self.DEFAULT_PATH_CONFIG['base_dir'])
            
        try:
            self._config_manager.project_name
        except AttributeError:
            self._config_manager.set('project_name', self.DEFAULT_PATH_CONFIG['project_name'])
        
        try:
            self._config_manager.experiment_name
        except AttributeError:
            self._config_manager.set('experiment_name', self.DEFAULT_PATH_CONFIG['experiment_name'])
    
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
        try:
            from is_debug import is_debug
        except ImportError:
            debug("⚠️  is_debug模块不可用，默认使用生产模式")
    
    def update_debug_mode(self) -> None:
        """更新调试模式"""
        debug_mode = self._debug_detector.detect_debug_mode()
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
        # test_mode下使用安全的默认值
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
            debug_mode = False
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
        log_dirs = self._path_generator.generate_log_directories(work_dir, date_str, time_str)
        
        # 合并所有路径配置
        path_configs = {
            'paths.work_dir': work_dir,
            **checkpoint_dirs,
            **debug_dirs,
            **tensorboard_dirs,
            **log_dirs
        }
        
        return path_configs
    
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
            for path in path_configs.values():
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