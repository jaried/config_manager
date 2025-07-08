# src/config_manager/core/cross_platform_paths.py
from __future__ import annotations
from datetime import datetime

import os
import sys
import platform
from pathlib import Path
from typing import Dict, Any, Union
import tempfile


class CrossPlatformPathManager:
    """跨平台路径管理器"""
    
    # 支持的操作系统
    SUPPORTED_OS = {
        'windows': ['win32', 'win64', 'windows'],
        'linux': ['linux', 'linux2', 'ubuntu']  # Linux包括各种发行版（Ubuntu等）
    }
    
    # 默认路径配置
    DEFAULT_PATHS = {
        'windows': {
            'base_dir': tempfile.gettempdir(),
            'work_dir': os.path.join(tempfile.gettempdir(), 'work'),
            'tensorboard_dir': os.path.join(tempfile.gettempdir(), 'tensorboard_logs'),
            'temp_dir': tempfile.gettempdir()
        },
        'linux': {
            'base_dir': tempfile.gettempdir(),
            'work_dir': os.path.join(tempfile.gettempdir(), 'work'),
            'tensorboard_dir': os.path.join(tempfile.gettempdir(), 'tensorboard_logs'),
            'temp_dir': tempfile.gettempdir()
        }
    }
    
    def __init__(self):
        """初始化跨平台路径管理器"""
        self._current_os: str = 'linux'  # 默认值，避免None
        self._platform_info = None
        self._detection_time = None
        self._cache = {}
        
        # 检测当前操作系统
        self._detect_current_os()
    
    def _detect_current_os(self) -> None:
        """检测当前操作系统"""
        try:
            # 主要检测方法：使用platform.system()
            system_name = platform.system().lower()
            
            # 备选检测方法：使用sys.platform
            sys_platform = sys.platform.lower()
            
            # 确定操作系统
            if system_name == 'windows' or 'win' in sys_platform:
                self._current_os = 'windows'
            elif system_name == 'linux' or 'linux' in sys_platform:
                # 所有Linux系统（包括Ubuntu）都归为linux
                self._current_os = 'linux'
            else:
                # 不支持的操作系统，直接抛错
                raise RuntimeError(f"不支持的操作系统: {system_name} (sys.platform: {sys_platform})")
            
            # 记录检测时间
            self._detection_time = datetime.now()
            
        except Exception as e:
            # 检测失败时直接抛错，不设置默认值
            raise RuntimeError(f"平台检测失败: {e}") from e
    
    def get_current_os(self) -> str:
        """获取当前操作系统"""
        return self._current_os
    
    def get_os_family(self) -> str:
        """获取操作系统家族"""
        if self._current_os == 'windows':
            return 'windows'
        else:
            return 'unix'  # Ubuntu属于Unix家族
    
    def get_default_path(self, path_type: str) -> str:
        """获取默认路径"""
        if self._current_os not in self.DEFAULT_PATHS:
            raise RuntimeError(f"不支持的操作系统: {self._current_os}")
        
        if path_type not in self.DEFAULT_PATHS[self._current_os]:
            raise ValueError(f"不支持的路径类型: {path_type}")
        
        result = self.DEFAULT_PATHS[self._current_os][path_type]
        if result is None:
            raise ValueError(f"路径类型 {path_type} 配置为空")
        
        return result
    
    def get_platform_path(self, path_config: Union[str, Dict[str, str]], path_type: str) -> str:
        """根据当前操作系统获取平台特定路径"""
        # 如果是字符串，直接返回
        if isinstance(path_config, str):
            return path_config
        
        # 如果是字典，根据当前操作系统选择路径
        if isinstance(path_config, dict):
            # 优先级1：当前操作系统名称的路径
            if self._current_os in path_config:
                return path_config[self._current_os]
            
            # 不支持ubuntu别名，严格要求使用linux
            # 如果配置中仍使用ubuntu键，直接报错
            if self._current_os == 'linux' and 'ubuntu' in path_config and 'linux' not in path_config:
                raise ValueError(f"配置错误：请将 'ubuntu' 改为 'linux'。当前平台: {self._current_os}")
            
            # 仅支持linux键，不支持ubuntu向后兼容
            if self._current_os == 'linux' and 'linux' in path_config:
                return path_config['linux']
            
            # 优先级2：操作系统家族的路径
            os_family = self.get_os_family()
            if os_family in path_config:
                return path_config[os_family]
            
            # 配置中没有当前平台的路径，直接抛错
            raise ValueError(f"配置中缺少平台 '{self._current_os}' 的路径配置。可用平台: {list(path_config.keys())}")
        
        # 其他情况直接抛错
        raise ValueError(f"无效的路径配置类型: {type(path_config)}")
    
    def _get_default_paths(self, key: str) -> Dict[str, str]:
        """获取默认路径配置"""
        return {
            'windows': self.DEFAULT_PATHS['windows'].get(key, ''),
            'linux': self.DEFAULT_PATHS['linux'].get(key, ''),
        }

    def convert_to_multi_platform_config(self, path: str, key: str) -> Dict[str, str]:
        """将单一路径转换为多平台配置"""
        if not path:
            return self._get_default_paths(key)
        
        # 检测路径的平台类型
        detected_platform = self._detect_path_platform(path)
        
        # 创建多平台配置
        multi_platform_config = {}
        
        # 为每个支持的平台设置路径
        for platform_name in ['windows', 'linux']:
            if platform_name == detected_platform:
                # 对于检测到的平台，使用原始路径
                multi_platform_config[platform_name] = path
            else:
                # 对于其他平台，生成对应的路径
                if platform_name == 'windows':
                    # Windows路径转换
                    if detected_platform in ['linux']:
                        # 从Unix路径转换为Windows路径，默认使用 d:\logs
                        multi_platform_config[platform_name] = 'd:\\logs'
                    else:
                        multi_platform_config[platform_name] = path
                elif platform_name == 'linux':
                    # Linux路径转换
                    if detected_platform == 'windows':
                        # 从Windows路径转换为Linux路径，保持原始路径转换逻辑
                        # 只有在没有配置或者需要默认值时才使用~/logs
                        if key == 'base_dir':
                            multi_platform_config[platform_name] = '~/logs'
                        else:
                            # 对于其他路径类型，尝试转换
                            multi_platform_config[platform_name] = path.replace('\\', '/').replace('d:', '/tmp')
                    else:
                        multi_platform_config[platform_name] = path
        
        return multi_platform_config
    
    def _detect_path_platform(self, path: str) -> str:
        """检测路径的平台类型"""
        if not path:
            return self._current_os
        
        # 优先检查路径分隔符
        # 1. 包含反斜杠且不包含正斜杠 - 一定是Windows
        if '\\' in path and '/' not in path:
            return 'windows'
        
        # 2. 包含正斜杠且不包含反斜杠 - 一定是Unix（linux）
        if '/' in path and '\\' not in path:
            # 进一步判断Unix类型
            if path.startswith('/'):
                # 所有Unix绝对路径都归为linux
                return 'linux'
            else:
                # 相对路径，根据当前操作系统判断
                if self._current_os == 'windows':
                    return 'windows'
                else:
                    return 'linux'
        
        # 3. 同时包含两种分隔符 - 根据当前操作系统判断
        if '\\' in path and '/' in path:
            if self._current_os == 'windows':
                return 'windows'
            else:
                return 'linux'
        
        # Windows路径特征检测
        # 1. 盘符格式 (C:, D:等)
        if len(path) >= 2 and path[1] == ':':
            return 'windows'
        
        # 2. UNC路径 (\\server\share)
        if path.startswith('\\\\'):
            return 'windows'
        
        # 相对路径，使用当前操作系统
        return self._current_os
    
    def normalize_path(self, path: str) -> str:
        """标准化路径格式"""
        if not path:
            return path
        
        try:
            # 检测路径的平台类型
            path_platform = self._detect_path_platform(path)
            
            # 处理~路径展开（仅在Linux/Unix系统上）
            if path_platform == 'linux' and '~' in path:
                path = os.path.expanduser(path)
            
            # 根据平台类型进行标准化
            if path_platform == 'windows':
                # Windows路径标准化
                normalized = Path(path)
                return str(normalized).replace('/', '\\')
            else:
                # Unix/Linux/macOS路径标准化
                normalized = Path(path)
                return str(normalized).replace('\\', '/')
                
        except Exception:
            # 标准化失败，返回原路径
            return path
    
    def get_platform_info(self) -> Dict[str, Any]:
        """获取平台详细信息"""
        if self._platform_info is None:
            self._platform_info = {
                'current_os': self._current_os,
                'os_family': self.get_os_family(),
                'platform_system': platform.system(),
                'platform_release': platform.release(),
                'platform_version': platform.version(),
                'platform_machine': platform.machine(),
                'sys_platform': sys.platform,
                'detection_time': self._detection_time.isoformat() if self._detection_time else None
            }
        
        return self._platform_info.copy()


# 全局单例实例
_cross_platform_manager = None


def get_cross_platform_manager() -> CrossPlatformPathManager:
    """获取跨平台路径管理器实例（单例模式）"""
    global _cross_platform_manager
    if _cross_platform_manager is None:
        _cross_platform_manager = CrossPlatformPathManager()
    return _cross_platform_manager


def convert_to_multi_platform_config(single_path: str, path_type: str) -> Dict[str, str]:
    """将单一路径转换为多平台配置（便捷函数）"""
    manager = get_cross_platform_manager()
    return manager.convert_to_multi_platform_config(single_path, path_type)


def get_platform_path(path_config: Union[str, Dict[str, str]], path_type: str) -> str:
    """根据当前操作系统获取平台特定路径（便捷函数）"""
    manager = get_cross_platform_manager()
    return manager.get_platform_path(path_config, path_type) 