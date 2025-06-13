# tests/01_unit_tests/test_config_manager/test_auto_directory_creation.py
from __future__ import annotations
from datetime import datetime

start_time = datetime.now()

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch
from is_debug import is_debug

from src.config_manager import get_config_manager


class TestAutoDirectoryCreation:
    """测试自动目录创建功能"""
    
    def setup_method(self):
        """测试前设置"""
        self.temp_dir = tempfile.mkdtemp()
        self.test_time = datetime(2025, 1, 8, 10, 30, 0)
    
    def teardown_method(self):
        """测试后清理"""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_paths_namespace_auto_creation(self):
        """测试paths命名空间下的路径自动创建目录"""
        # 创建测试配置管理器
        config = get_config_manager(test_mode=True, first_start_time=self.test_time)
        
        # 设置paths命名空间下的路径
        test_log_dir = os.path.join(self.temp_dir, 'test_logs')
        config.set('paths.log_dir', test_log_dir)
        
        # 验证目录已创建
        assert os.path.exists(test_log_dir), f"目录应该被自动创建: {test_log_dir}"
        assert os.path.isdir(test_log_dir), f"应该是一个目录: {test_log_dir}"
    
    def test_nested_path_auto_creation(self):
        """测试嵌套路径的自动创建"""
        config = get_config_manager(test_mode=True, first_start_time=self.test_time)
        
        # 设置深层嵌套路径
        nested_path = os.path.join(self.temp_dir, 'level1', 'level2', 'level3', 'logs')
        config.set('paths.nested_log_dir', nested_path)
        
        # 验证所有层级目录都被创建
        assert os.path.exists(nested_path), f"嵌套目录应该被自动创建: {nested_path}"
        assert os.path.isdir(nested_path), f"应该是一个目录: {nested_path}"
    
    def test_path_keyword_detection(self):
        """测试路径关键词检测功能"""
        config = get_config_manager(test_mode=True, first_start_time=self.test_time)
        
        # 测试各种路径关键词
        path_configs = {
            'log_dir': os.path.join(self.temp_dir, 'log_dir'),
            'data_path': os.path.join(self.temp_dir, 'data_path'),
            'output_directory': os.path.join(self.temp_dir, 'output_directory'),
            'model_folder': os.path.join(self.temp_dir, 'model_folder'),
            'cache_location': os.path.join(self.temp_dir, 'cache_location'),
            'project_root': os.path.join(self.temp_dir, 'project_root'),
            'base_dir': os.path.join(self.temp_dir, 'base_dir'),
        }
        
        # 设置所有路径配置
        for key, path in path_configs.items():
            config.set(key, path)
        
        # 验证所有目录都被创建
        for key, path in path_configs.items():
            assert os.path.exists(path), f"目录应该被自动创建 {key}: {path}"
            assert os.path.isdir(path), f"应该是一个目录 {key}: {path}"
    
    def test_non_path_values_ignored(self):
        """测试非路径值不会触发目录创建"""
        config = get_config_manager(test_mode=True, first_start_time=self.test_time)
        
        # 设置非路径值
        config.set('paths.max_epochs', 100)
        config.set('paths.learning_rate', 0.001)
        config.set('paths.model_name', 'bert-base')
        config.set('log_level', 'INFO')
        config.set('debug_mode', True)
        
        # 这些值不应该触发目录创建，测试应该正常完成而不出错
        assert config.get('paths.max_epochs') == 100
        assert config.get('paths.learning_rate') == 0.001
        assert config.get('paths.model_name') == 'bert-base'
    
    def test_invalid_path_handling(self):
        """测试无效路径的处理"""
        config = get_config_manager(test_mode=True, first_start_time=self.test_time)
        
        # 设置无效路径（在Windows上，包含非法字符）
        invalid_paths = [
            'paths.invalid_dir1',  # 不包含路径分隔符
            '',  # 空路径
        ]
        
        # 这些操作不应该抛出异常
        for path_key in invalid_paths:
            try:
                config.set(path_key, 'invalid_path_value')
            except Exception as e:
                pytest.fail(f"设置无效路径不应该抛出异常: {e}")
    
    def test_permission_error_handling(self):
        """测试权限错误的处理"""
        config = get_config_manager(test_mode=True, first_start_time=self.test_time)
        
        # 模拟权限错误
        with patch('pathlib.Path.mkdir') as mock_mkdir:
            mock_mkdir.side_effect = PermissionError("Permission denied")
            
            # 设置路径，应该记录警告但不抛出异常
            test_path = os.path.join(self.temp_dir, 'permission_test')
            try:
                config.set('paths.permission_test_dir', test_path)
            except Exception as e:
                pytest.fail(f"权限错误应该被处理而不抛出异常: {e}")
    
    def test_path_configuration_manager_integration(self):
        """测试与路径配置管理器的集成"""
        config = get_config_manager(test_mode=True, first_start_time=self.test_time)
        
        # 设置基础配置
        config.set('base_dir', self.temp_dir)
        config.set('project_name', 'test_project')
        config.set('experiment_name', 'test_exp')
        config.set('debug_mode', True)
        
        # 触发路径配置更新
        if hasattr(config, '_path_config_manager') and config._path_config_manager:
            config._path_config_manager.invalidate_cache()
            path_configs = config._path_config_manager.generate_all_paths()
            
            # 验证生成的路径目录都被创建
            for path_key, path_value in path_configs.items():
                if path_value and isinstance(path_value, str):
                    assert os.path.exists(path_value), f"路径配置管理器生成的目录应该存在: {path_key} = {path_value}"
    
    def test_existing_directory_handling(self):
        """测试已存在目录的处理"""
        config = get_config_manager(test_mode=True, first_start_time=self.test_time)
        
        # 先手动创建目录
        existing_dir = os.path.join(self.temp_dir, 'existing_dir')
        os.makedirs(existing_dir, exist_ok=True)
        
        # 设置已存在的目录路径，应该不出错
        try:
            config.set('paths.existing_dir', existing_dir)
        except Exception as e:
            pytest.fail(f"设置已存在目录不应该抛出异常: {e}")
        
        # 验证目录仍然存在
        assert os.path.exists(existing_dir)
        assert os.path.isdir(existing_dir)
    
    def test_windows_path_formats(self):
        """测试Windows路径格式的处理"""
        config = get_config_manager(test_mode=True, first_start_time=self.test_time)
        
        # 测试不同的Windows路径格式
        windows_paths = [
            os.path.join(self.temp_dir, 'windows_style'),  # 使用os.path.join确保正确格式
            self.temp_dir.replace('/', '\\') + '\\backslash_style',  # 反斜杠格式
        ]
        
        for i, path in enumerate(windows_paths):
            config.set(f'paths.windows_test_{i}', path)
            assert os.path.exists(path), f"Windows路径格式应该被正确处理: {path}" 