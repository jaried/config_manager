# src/config_manager/core/cross_platform_paths.py
from __future__ import annotations
from datetime import datetime

import os
import sys
import platform
from pathlib import Path
from typing import Dict, Optional, Any, Union


class CrossPlatformPathManager:
    """跨平台路径管理器"""
    
    # 支持的操作系统
    SUPPORTED_OS = {
        'windows': ['win32', 'win64', 'windows'],
        'linux': ['linux', 'linux2'],
        'macos': ['darwin', 'macos'],
        'ubuntu': ['linux', 'linux2']  # Ubuntu是Linux的一个发行版
    }
    
    # 默认路径配置
    DEFAULT_PATHS = {
        'windows': {
            'base_dir': 'd:\\logs',
            'work_dir': 'd:\\work',
            'tensorboard_dir': 'd:\\tensorboard_logs',
            'temp_dir': 'd:\\temp'
        },
        'linux': {
            'base_dir': '/home/tony/logs',
            'work_dir': '/home/tony/work',
            'tensorboard_dir': '/home/tony/tensorboard_logs',
            'temp_dir': '/tmp'
        },
        'ubuntu': {
            'base_dir': '/home/tony/logs',
            'work_dir': '/home/tony/work',
            'tensorboard_dir': '/home/tony/tensorboard_logs',
            'temp_dir': '/tmp'
        },
        'macos': {
            'base_dir': '/Users/tony/logs',
            'work_dir': '/Users/tony/work',
            'tensorboard_dir': '/Users/tony/tensorboard_logs',
            'temp_dir': '/tmp'
        }
    }
    
    def __init__(self):
        """初始化跨平台路径管理器"""
        self._current_os = None
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
            elif system_name == 'darwin' or 'darwin' in sys_platform:
                self._current_os = 'macos'
            elif system_name == 'linux' or 'linux' in sys_platform:
                # 进一步检测是否为Ubuntu
                if self._is_ubuntu():
                    self._current_os = 'ubuntu'
                else:
                    self._current_os = 'linux'
            else:
                # 默认使用Linux
                self._current_os = 'linux'
            
            # 记录检测时间
            self._detection_time = datetime.now()
            
        except Exception as e:
            # 检测失败时使用默认值
            self._current_os = 'linux'
            self._detection_time = datetime.now()
    
    def _is_ubuntu(self) -> bool:
        """检测是否为Ubuntu系统"""
        try:
            # 方法1：检查/etc/os-release文件
            if os.path.exists('/etc/os-release'):
                with open('/etc/os-release', 'r', encoding='utf-8') as f:
                    content = f.read()
                    if 'NAME="Ubuntu"' in content or 'ID=ubuntu' in content:
                        return True
            
            # 方法2：检查/etc/lsb-release文件
            if os.path.exists('/etc/lsb-release'):
                with open('/etc/lsb-release', 'r', encoding='utf-8') as f:
                    content = f.read()
                    if 'DISTRIB_ID=Ubuntu' in content:
                        return True
            
            # 方法3：使用lsb_release命令
            try:
                import subprocess
                result = subprocess.run(['lsb_release', '-i'], 
                                      capture_output=True, text=True, timeout=5)
                if 'Ubuntu' in result.stdout:
                    return True
            except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
                pass
            
            return False
            
        except Exception:
            return False
    
    def get_current_os(self) -> str:
        """获取当前操作系统"""
        return self._current_os
    
    def get_os_family(self) -> str:
        """获取操作系统家族"""
        if self._current_os == 'windows':
            return 'windows'
        else:
            return 'unix'  # Linux, Ubuntu, macOS都属于Unix家族
    
    def get_default_path(self, path_type: str) -> str:
        """获取默认路径"""
        if self._current_os in self.DEFAULT_PATHS:
            return self.DEFAULT_PATHS[self._current_os].get(path_type, '')
        return ''
    
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
            
            # 优先级2：操作系统家族的路径
            os_family = self.get_os_family()
            if os_family in path_config:
                return path_config[os_family]
            
            # 优先级3：默认路径
            return self.get_default_path(path_type)
        
        # 其他情况返回默认路径
        return self.get_default_path(path_type)
    
    def convert_to_multi_platform_config(self, single_path: str, path_type: str) -> Dict[str, str]:
        """将单一路径转换为多平台配置"""
        if not single_path:
            # 空路径使用默认配置
            return {
                'windows': self.DEFAULT_PATHS['windows'].get(path_type, ''),
                'linux': self.DEFAULT_PATHS['linux'].get(path_type, ''),
                'ubuntu': self.DEFAULT_PATHS['ubuntu'].get(path_type, ''),
                'macos': self.DEFAULT_PATHS['macos'].get(path_type, '')
            }
        
        # 检测原始路径的平台
        original_platform = self._detect_path_platform(single_path)
        
        # 标准化路径
        normalized_path = self.normalize_path(single_path)
        
        # 创建多平台配置
        multi_platform_config = {
            'windows': self.DEFAULT_PATHS['windows'].get(path_type, ''),
            'linux': self.DEFAULT_PATHS['linux'].get(path_type, ''),
            'ubuntu': self.DEFAULT_PATHS['ubuntu'].get(path_type, ''),
            'macos': self.DEFAULT_PATHS['macos'].get(path_type, '')
        }
        
        # 将原始路径映射到对应平台
        if original_platform == 'windows':
            multi_platform_config['windows'] = normalized_path
        elif original_platform == 'linux':
            multi_platform_config['linux'] = normalized_path
            multi_platform_config['ubuntu'] = normalized_path
        elif original_platform == 'macos':
            multi_platform_config['macos'] = normalized_path
        else:
            # 相对路径或未知格式，使用当前操作系统
            multi_platform_config[self._current_os] = normalized_path
        
        return multi_platform_config
    
    def _detect_path_platform(self, path: str) -> str:
        """检测路径的平台类型"""
        if not path:
            return self._current_os
        
        # Windows路径特征
        if ':\\' in path or path.startswith('\\\\'):
            return 'windows'
        
        # Unix路径特征
        if path.startswith('/'):
            return 'linux'
        
        # macOS路径特征（通常与Linux相同，但可以进一步区分）
        if path.startswith('/Users/'):
            return 'macos'
        
        # 相对路径，使用当前操作系统
        return self._current_os
    
    def normalize_path(self, path: str) -> str:
        """标准化路径格式"""
        if not path:
            return path
        
        try:
            # 检测路径的平台类型
            path_platform = self._detect_path_platform(path)
            
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