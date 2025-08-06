# tests/utils/path_test_helper.py
from __future__ import annotations
from typing import Optional
import platform


class PathTestHelper:
    """路径测试辅助工具类，提供平台无关的路径比较和验证功能"""
    
    @staticmethod
    def normalize_path(path: str) -> str:
        """规范化路径为统一格式（使用正斜杠）
        
        Args:
            path: 需要规范化的路径
            
        Returns:
            规范化后的路径（正斜杠格式）
        """
        if not path:
            return path
        return path.replace('\\', '/')
    
    @staticmethod
    def assert_path_equal(actual: str, expected: str, message: Optional[str] = None):
        """平台无关的路径相等性断言
        
        Args:
            actual: 实际路径
            expected: 期望路径
            message: 可选的错误消息
        """
        actual_norm = PathTestHelper.normalize_path(actual)
        expected_norm = PathTestHelper.normalize_path(expected)
        
        if actual_norm != expected_norm:
            error_msg = message or f"路径不匹配"
            raise AssertionError(f"{error_msg}\n期望: {expected_norm}\n实际: {actual_norm}")
    
    @staticmethod
    def assert_path_contains(path: str, substring: str, message: Optional[str] = None):
        """平台无关的路径包含检查
        
        Args:
            path: 要检查的路径
            substring: 期望包含的子字符串
            message: 可选的错误消息
        """
        path_norm = PathTestHelper.normalize_path(path)
        substring_norm = PathTestHelper.normalize_path(substring)
        
        if substring_norm not in path_norm:
            error_msg = message or f"路径不包含期望的子字符串"
            raise AssertionError(f"{error_msg}\n路径: {path_norm}\n期望包含: {substring_norm}")
    
    @staticmethod
    def assert_path_not_contains(path: str, substring: str, message: Optional[str] = None):
        """平台无关的路径不包含检查
        
        Args:
            path: 要检查的路径
            substring: 不应包含的子字符串
            message: 可选的错误消息
        """
        path_norm = PathTestHelper.normalize_path(path)
        substring_norm = PathTestHelper.normalize_path(substring)
        
        if substring_norm in path_norm:
            error_msg = message or f"路径包含了不应该有的子字符串"
            raise AssertionError(f"{error_msg}\n路径: {path_norm}\n不应包含: {substring_norm}")
    
    @staticmethod
    def assert_path_starts_with(path: str, prefix: str, message: Optional[str] = None):
        """平台无关的路径前缀检查
        
        Args:
            path: 要检查的路径
            prefix: 期望的前缀
            message: 可选的错误消息
        """
        path_norm = PathTestHelper.normalize_path(path)
        prefix_norm = PathTestHelper.normalize_path(prefix)
        
        if not path_norm.startswith(prefix_norm):
            error_msg = message or f"路径前缀不匹配"
            raise AssertionError(f"{error_msg}\n路径: {path_norm}\n期望前缀: {prefix_norm}")
    
    @staticmethod
    def assert_path_ends_with(path: str, suffix: str, message: Optional[str] = None):
        """平台无关的路径后缀检查
        
        Args:
            path: 要检查的路径
            suffix: 期望的后缀
            message: 可选的错误消息
        """
        path_norm = PathTestHelper.normalize_path(path)
        suffix_norm = PathTestHelper.normalize_path(suffix)
        
        if not path_norm.endswith(suffix_norm):
            error_msg = message or f"路径后缀不匹配"
            raise AssertionError(f"{error_msg}\n路径: {path_norm}\n期望后缀: {suffix_norm}")
    
    @staticmethod
    def extract_path_components(path: str) -> list[str]:
        """提取路径的各个组件
        
        Args:
            path: 要分解的路径
            
        Returns:
            路径组件列表
        """
        path_norm = PathTestHelper.normalize_path(path)
        # 分割路径并过滤空字符串
        return [c for c in path_norm.split('/') if c]
    
    @staticmethod
    def is_windows() -> bool:
        """检查当前是否为Windows平台
        
        Returns:
            True如果是Windows，否则False
        """
        return platform.system() == 'Windows'
    
    @staticmethod
    def is_linux() -> bool:
        """检查当前是否为Linux平台
        
        Returns:
            True如果是Linux，否则False
        """
        return platform.system() == 'Linux'
    
    @staticmethod
    def get_expected_separator() -> str:
        """获取当前平台期望的路径分隔符
        
        Returns:
            平台特定的路径分隔符
        """
        # 统一返回正斜杠，因为我们的实现统一使用正斜杠
        return '/'
    
    @staticmethod
    def compare_paths(path1: str, path2: str) -> bool:
        """比较两个路径是否相等（平台无关）
        
        Args:
            path1: 第一个路径
            path2: 第二个路径
            
        Returns:
            True如果路径相等，否则False
        """
        return PathTestHelper.normalize_path(path1) == PathTestHelper.normalize_path(path2)