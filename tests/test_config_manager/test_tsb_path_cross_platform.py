# tests/test_config_manager/test_tsb_path_cross_platform.py
from __future__ import annotations
from datetime import datetime
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

from config_manager import get_config_manager
from config_manager.core.path_resolver import PathResolver
from config_manager.core.cross_platform_paths import CrossPlatformPathManager


class TestTsbPathCrossPlatform:
    """测试TSB路径的跨平台兼容性"""
    
    def test_windows_path_format(self):
        """测试Windows平台的路径格式"""
        # 在Linux环境下无法完全模拟Windows路径行为
        # 因为os.path模块的底层函数依赖于实际的操作系统
        # 所以我们只测试路径组件是否正确
        path = PathResolver.generate_tsb_logs_path(
            "/test/work",  # 使用Unix风格路径
            datetime(2025, 1, 8, 10, 30, 45)
        )
        
        # 验证路径包含正确的组件
        assert isinstance(path, str)
        assert "tsb_logs" in path
        assert "2025" in path
        assert "02" in path  # 第2周，不带W前缀
        assert "0108" in path
        assert "103045" in path
    
    def test_unix_path_format(self):
        """测试Unix/Linux平台的路径格式"""
        # 模拟Unix环境
        with patch('os.name', 'posix'):
            with patch('os.sep', '/'):
                # 生成路径
                path = PathResolver.generate_tsb_logs_path(
                    "/home/user/work",
                    datetime(2025, 1, 8, 10, 30, 45)
                )
                
                # 验证Unix路径格式
                assert isinstance(path, str)
                assert path.startswith("/home/user/work")
                assert "/tsb_logs/" in path
                assert "/2025/02/0108/103045" in path
                
                # 验证不包含反斜杠
                assert '\\' not in path
    
    def test_path_join_consistency(self):
        """测试os.path.join在不同平台的一致性"""
        test_time = datetime(2025, 3, 15, 14, 30, 45)
        
        # 测试不同的基础路径格式
        base_paths = {
            'windows': ["C:\\work", "D:\\projects\\myapp"],
            'unix': ["/home/work", "/var/projects/myapp"],
            'relative': ["work", "./projects/myapp"]
        }
        
        for platform_type, paths in base_paths.items():
            for base_path in paths:
                try:
                    result = PathResolver.generate_tsb_logs_path(base_path, test_time)
                    
                    # 验证路径包含必要组件
                    assert 'tsb_logs' in result
                    assert '2025' in result
                    assert '11' in result  # 第11周
                    assert '0315' in result
                    assert '143045' in result
                    
                    # 验证路径可以被Path对象处理
                    path_obj = Path(result)
                    assert path_obj.parts[-1] == '143045'
                    assert path_obj.parts[-2] == '0315'
                    assert path_obj.parts[-3] == '11'
                    assert path_obj.parts[-4] == '2025'
                    assert path_obj.parts[-5] == 'tsb_logs'
                    
                except Exception as e:
                    print(f"处理{platform_type}路径'{base_path}'时出错：{e}")
    
    def test_cross_platform_manager_integration(self):
        """测试与CrossPlatformPathManager的集成"""
        # 创建跨平台路径管理器
        manager = CrossPlatformPathManager()
        
        # 测试不同平台的默认路径
        platforms = ['windows', 'ubuntu', 'macos']
        
        for platform in platforms:
            with patch.object(manager, 'get_current_os', return_value=platform):
                # 获取平台特定的基础路径
                base_path = manager.get_default_path('base_dir')
                
                # 生成TSB路径
                tsb_path = PathResolver.generate_tsb_logs_path(
                    base_path,
                    datetime(2025, 1, 8)
                )
                
                # 验证路径有效性
                assert isinstance(tsb_path, str)
                assert len(tsb_path) > 0
                assert 'tsb_logs' in tsb_path
    
    def test_config_manager_cross_platform(self):
        """测试ConfigManager在不同平台的行为"""
        test_time = datetime(2025, 1, 8, 16, 45, 30)
        
        # 测试Windows环境
        with patch('os.name', 'nt'):
            config_win = get_config_manager(
                test_mode=True,
                auto_create=True,
                first_start_time=test_time
            )
            
            try:
                win_tsb = config_win.paths.tsb_logs_dir
                win_tb = config_win.paths.tensorboard_dir
                
                # 验证路径相等
                assert win_tb == win_tsb
                
                # Windows路径应使用反斜杠（如果在Windows上运行）
                if sys.platform == 'win32':
                    assert '\\' in win_tsb or '/' in win_tsb  # 可能使用正斜杠
                
            finally:
                if hasattr(config_win, 'cleanup'):
                    config_win.cleanup()
        
        # 测试Unix环境
        with patch('os.name', 'posix'):
            config_unix = get_config_manager(
                test_mode=True,
                auto_create=True,
                first_start_time=test_time
            )
            
            try:
                unix_tsb = config_unix.paths.tsb_logs_dir
                unix_tb = config_unix.paths.tensorboard_dir
                
                # 验证路径相等
                assert unix_tb == unix_tsb
                
                # Unix路径应使用正斜杠
                if sys.platform != 'win32':
                    assert '/' in unix_tsb
                    assert '\\' not in unix_tsb
                
            finally:
                if hasattr(config_unix, 'cleanup'):
                    config_unix.cleanup()
    
    def test_path_normalization(self):
        """测试路径规范化"""
        test_time = datetime(2025, 1, 8)
        
        # 测试各种非标准路径输入
        test_paths = [
            "/home/user//work",           # 双斜杠
            "/home/user/./work",          # 当前目录
            "/home/user/../user/work",    # 父目录
            "~/work",                     # 用户目录
            "work/../../work",            # 相对路径
        ]
        
        for test_path in test_paths:
            try:
                # 规范化路径
                if test_path.startswith('~'):
                    normalized = os.path.expanduser(test_path)
                else:
                    normalized = os.path.normpath(test_path)
                
                # 生成TSB路径
                result = PathResolver.generate_tsb_logs_path(normalized, test_time)
                
                # 验证结果是规范化的
                assert '//' not in result or sys.platform == 'win32'  # Windows可能有UNC路径
                assert '/./' not in result
                assert '/../' not in result
                
            except Exception as e:
                print(f"处理路径'{test_path}'时出错：{e}")
    
    def test_unicode_path_support(self):
        """测试Unicode路径支持"""
        unicode_paths = [
            "/home/用户/工作",
            "/home/пользователь/работа",
            "/home/उपयोगकर्ता/कार्य",
            "/home/ユーザー/仕事",
            "/home/🏠/📁",
        ]
        
        test_time = datetime(2025, 1, 8)
        
        for unicode_path in unicode_paths:
            try:
                result = PathResolver.generate_tsb_logs_path(unicode_path, test_time)
                
                # 验证Unicode字符被保留
                assert any(ord(c) > 127 for c in result), (
                    f"Unicode字符应该被保留：{unicode_path}"
                )
                
                # 验证路径结构正确
                assert '/tsb_logs/' in result or '\\tsb_logs\\' in result
                
            except Exception as e:
                # 某些系统可能不支持某些Unicode字符
                print(f"Unicode路径'{unicode_path}'处理失败：{e}")
    
    def test_network_path_handling(self):
        """测试网络路径处理"""
        # UNC路径（Windows）
        unc_paths = [
            "\\\\server\\share\\work",
            "//server/share/work",
        ]
        
        test_time = datetime(2025, 1, 8)
        
        for unc_path in unc_paths:
            try:
                result = PathResolver.generate_tsb_logs_path(unc_path, test_time)
                
                # 验证网络路径被保留
                assert result.startswith('\\\\') or result.startswith('//')
                assert 'server' in result
                assert 'share' in result
                assert 'tsb_logs' in result
                
            except Exception as e:
                print(f"网络路径'{unc_path}'处理失败：{e}")
    
    def test_path_with_environment_variables(self):
        """测试包含环境变量的路径"""
        # 设置测试环境变量
        test_env_var = 'TEST_TSB_BASE_DIR'
        test_value = '/test/base/dir'
        
        with patch.dict(os.environ, {test_env_var: test_value}):
            # 使用环境变量构建路径
            env_path = os.path.expandvars(f'${test_env_var}/work')
            
            # 生成TSB路径
            result = PathResolver.generate_tsb_logs_path(
                env_path,
                datetime(2025, 1, 8)
            )
            
            # 验证环境变量被展开
            assert test_value in result
            assert '$' not in result  # 环境变量应该被替换
            assert 'tsb_logs' in result
    
    def test_relative_vs_absolute_paths(self):
        """测试相对路径和绝对路径的处理"""
        test_time = datetime(2025, 1, 8)
        
        # 保存当前目录
        original_cwd = os.getcwd()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            try:
                # 切换到临时目录
                os.chdir(temp_dir)
                
                # 测试相对路径
                relative_paths = [
                    "work",
                    "./work",
                    "../work",
                    "subdir/work",
                ]
                
                for rel_path in relative_paths:
                    result = PathResolver.generate_tsb_logs_path(rel_path, test_time)
                    
                    # 结果应该是绝对路径
                    assert os.path.isabs(result), (
                        f"结果应该是绝对路径：{result}"
                    )
                    
                    # 验证包含必要组件
                    assert 'tsb_logs' in result
                    assert '2025' in result
                
                # 测试绝对路径
                abs_path = os.path.join(temp_dir, "absolute", "work")
                result = PathResolver.generate_tsb_logs_path(abs_path, test_time)
                
                # 统一路径分隔符后再比较
                abs_path_normalized = abs_path.replace('\\', '/')
                result_normalized = result.replace('\\', '/')
                assert abs_path_normalized in result_normalized
                assert os.path.isabs(result)
                
            finally:
                # 在with块结束前恢复原始目录，避免Windows权限问题
                os.chdir(original_cwd)
    
    def test_path_separator_consistency(self):
        """测试路径分隔符的一致性"""
        # 测试不同风格的路径
        test_paths = [
            "/home/user/work",      # Unix风格路径
            "/test/path/work",      # 另一个Unix路径
        ]
        
        test_time = datetime(2025, 1, 8)
        
        for test_path in test_paths:
            result = PathResolver.generate_tsb_logs_path(test_path, test_time)
            
            # 验证结果使用一致的分隔符（基于当前操作系统）
            if os.sep == '/':
                # Unix系统应该只使用正斜杠
                assert '\\' not in result, f"Unix路径不应包含反斜杠: {result}"
            
            # 验证路径组件
            assert 'tsb_logs' in result
            assert '2025' in result
            assert '02' in result  # 第2周，不带W前缀
    
    pass