# src/config_manager/core/path_configuration.py
from __future__ import annotations
from datetime import datetime

start_time = datetime.now()

import os
from pathlib import Path
from typing import Dict, Tuple, Optional, Any


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
    
    def generate_work_directory(
        self, 
        base_dir: str, 
        project_name: str, 
        experiment_name: str, 
        debug_mode: bool
    ) -> str:
        """生成工作目录路径
        
        Args:
            base_dir: 基础目录
            project_name: 项目名称
            experiment_name: 实验名称
            debug_mode: 是否为调试模式
            
        Returns:
            str: 工作目录路径
        """
        # 标准化路径分隔符
        base_path = Path(base_dir)
        
        # 构建路径组件
        path_components = [base_path]
        
        # 调试模式添加debug标识
        if debug_mode:
            path_components.append('debug')
        
        # 添加项目名称和实验名称
        path_components.extend([project_name, experiment_name])
        
        # 生成最终路径
        work_dir = Path(*path_components)
        
        return str(work_dir)
    
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


class PathValidator:
    """路径验证器"""
    
    @staticmethod
    def validate_base_dir(base_dir: str) -> bool:
        """验证基础目录
        
        Args:
            base_dir: 基础目录路径
            
        Returns:
            bool: 验证结果
        """
        if not base_dir or not isinstance(base_dir, str):
            return False
        
        try:
            path = Path(base_dir)
            # 检查路径格式是否有效
            str(path.resolve())
            return True
        except (OSError, ValueError):
            return False
    
    @staticmethod
    def validate_path_format(path: str) -> bool:
        """验证路径格式
        
        Args:
            path: 路径字符串
            
        Returns:
            bool: 验证结果
        """
        if not path or not isinstance(path, str):
            return False
        
        try:
            Path(path)
            return True
        except (OSError, ValueError):
            return False
    
    @staticmethod
    def validate_directory_permissions(path: str) -> bool:
        """验证目录权限
        
        Args:
            path: 目录路径
            
        Returns:
            bool: 权限验证结果
        """
        try:
            path_obj = Path(path)
            parent_dir = path_obj.parent
            
            # 如果父目录存在，检查写权限
            if parent_dir.exists():
                return os.access(str(parent_dir), os.W_OK)
            
            # 如果父目录不存在，递归检查上级目录
            return PathValidator.validate_directory_permissions(str(parent_dir))
        except (OSError, ValueError):
            return False


class DirectoryCreator:
    """目录创建器"""
    
    @staticmethod
    def create_directory(path: str, exist_ok: bool = True) -> bool:
        """创建目录
        
        Args:
            path: 目录路径
            exist_ok: 目录已存在时是否报错
            
        Returns:
            bool: 创建结果
        """
        try:
            Path(path).mkdir(parents=True, exist_ok=exist_ok)
            return True
        except (OSError, PermissionError):
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
            if path and isinstance(path, str):
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
        self._directory_creator = DirectoryCreator()
    
    def update_path_configurations(self, path_configs: Dict[str, str]) -> None:
        """更新路径配置并自动创建目录
        
        Args:
            path_configs: 路径配置字典
        """
        # 首先创建所有目录
        creation_results = self._directory_creator.create_path_structure(path_configs)
        
        # 记录目录创建结果
        for key, success in creation_results.items():
            if not success:
                print(f"警告: 目录创建失败 {key}: {path_configs.get(key)}")
        
        # 然后设置配置值，使用autosave=False避免递归调用
        for key, value in path_configs.items():
            self._config_manager.set(key, value, autosave=False)
    
    def update_debug_mode(self, debug_mode: bool) -> None:
        """更新调试模式
        
        Args:
            debug_mode: 调试模式状态
        """
        # ConfigUpdater 不直接管理 debug_mode，这应该由 PathConfigurationManager 处理
        # 这个方法主要是为了兼容性，实际的 debug_mode 管理在 PathConfigurationManager 中
        pass


class PathConfigurationManager:
    """路径配置管理器"""
    
    # 默认配置
    DEFAULT_PATH_CONFIG = {
        'base_dir': 'd:\\logs',  # Windows默认
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
        
        # 缓存相关
        self._path_cache = {}
        self._cache_valid = False
    
    def initialize_path_configuration(self) -> None:
        """初始化路径配置"""
        try:
            # 设置默认值（如果不存在）
            self._set_default_values()
            
            # debug_mode现在是动态属性，不需要存储到配置中
            # 直接从配置管理器获取（会自动调用is_debug()）
            current_debug_mode = self._config_manager.debug_mode
            
            # 确保first_start_time存在
            self._ensure_first_start_time()
            
            # 清除缓存，确保使用最新的调试模式设置
            self.invalidate_cache()
            
            # 生成路径配置
            path_configs = self.generate_all_paths()
            
            # 验证路径配置
            if not self.validate_path_configuration():
                raise PathConfigurationError("路径配置验证失败")
            
            # 更新配置
            self._config_updater.update_path_configurations(path_configs)
            
        except ImportError:
            # is_debug模块不可用，使用默认值
            self._handle_is_debug_import_error()
        except (OSError, PermissionError) as e:
            # 路径相关错误
            raise DirectoryCreationError(f"目录操作失败: {e}")
        except ValueError as e:
            # 时间解析错误
            raise TimeParsingError(f"时间解析失败: {e}")
    
    def _set_default_values(self) -> None:
        """设置默认配置值"""
        # 为必需的配置项设置默认值，如果它们不存在
        try:
            self._config_manager.base_dir
        except AttributeError:
            self._config_manager.set('base_dir', 'd:\\logs')
            
        try:
            self._config_manager.project_name
        except AttributeError:
            self._config_manager.set('project_name', 'project_name')
        
        try:
            self._config_manager.experiment_name
        except AttributeError:
            self._config_manager.set('experiment_name', 'experiment_name')
    
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
        # debug_mode现在是动态属性，不需要设置
        # 继续初始化其他路径配置
        path_configs = self.generate_all_paths()
        self._config_updater.update_path_configurations(path_configs)
    
    def update_debug_mode(self) -> None:
        """更新调试模式状态"""
        # debug_mode现在是动态属性，不需要设置
        # 只需要使缓存失效，重新生成路径
        self.invalidate_cache()
    
    def generate_all_paths(self) -> Dict[str, str]:
        """生成所有路径配置"""
        if self._cache_valid and self._path_cache:
            return self._path_cache.copy()
        
        path_configs = self._generate_paths_internal()
        
        # 更新缓存
        self._path_cache = path_configs.copy()
        self._cache_valid = True
        
        return path_configs
    
    def _generate_paths_internal(self) -> Dict[str, str]:
        """内部路径生成方法"""
        # 获取基础配置，使用属性访问，让错误自然抛出
        base_dir = self._config_manager.base_dir
        project_name = self._config_manager.project_name
        experiment_name = self._config_manager.experiment_name
        debug_mode = self._config_manager.debug_mode
        first_start_time = self._config_manager.first_start_time
        
        # 生成工作目录
        work_dir = self._path_generator.generate_work_directory(
            base_dir, project_name, experiment_name, debug_mode
        )
        
        # 生成检查点目录
        checkpoint_dirs = self._path_generator.generate_checkpoint_directories(work_dir)
        
        # 生成调试目录
        debug_dirs = self._path_generator.generate_debug_directory(work_dir)
        
        # 解析时间组件
        if first_start_time:
            date_str, time_str = self._time_processor.parse_first_start_time(first_start_time)
        else:
            date_str, time_str = self._time_processor.get_current_time_components()
        
        # 生成日志目录
        log_dirs = self._path_generator.generate_log_directories(work_dir, date_str, time_str)
        
        # 合并所有路径配置
        path_configs = {
            'paths.work_dir': work_dir,
            **checkpoint_dirs,
            **debug_dirs,
            **log_dirs
        }
        
        return path_configs
    
    def validate_path_configuration(self) -> bool:
        """验证路径配置"""
        # 验证基础目录，使用属性访问
        if not self._path_validator.validate_base_dir(self._config_manager.base_dir):
            return False
        
        # 验证生成的路径
        path_configs = self.generate_all_paths()
        for path in path_configs.values():
            if not self._path_validator.validate_path_format(path):
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
        debug_info = self._debug_detector.get_debug_status_info()
        path_configs = self.generate_all_paths()
        
        return {
            'debug_info': debug_info,
            'path_configs': path_configs,
            'cache_status': {
                'cache_valid': self._cache_valid,
                'cache_size': len(self._path_cache)
            }
        } 