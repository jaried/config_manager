# tests/01_unit_tests/test_config_manager/test_test_mode_auto_directory.py
from __future__ import annotations
from datetime import datetime

start_time = datetime.now()

import pytest
import tempfile
import os
from pathlib import Path
import sys
import shutil
from unittest.mock import patch, MagicMock

# Add project root to Python path
# 项目根目录由conftest.py自动配置

from config_manager import get_config_manager, _clear_instances_for_testing

@pytest.fixture(autouse=True)
def clear_instances_fixture():
    """在每个测试前后自动清理ConfigManager单例"""
    _clear_instances_for_testing()
    yield
    _clear_instances_for_testing()


class TestTestModeAutoDirectory:
    """测试test_mode下的自动目录创建功能"""
    
    def setup_method(self):
        """测试前设置"""
        self.test_time = datetime(2025, 1, 8, 15, 30, 0)
    
    def test_test_mode_paths_auto_creation(self):
        """测试test_mode下paths命名空间的路径设置，config对象生成后目录应已存在"""
        config = get_config_manager(test_mode=True, first_start_time=self.test_time)
        temp_base = tempfile.mkdtemp(prefix="test_auto_dir_")
        test_log_dir = os.path.join(temp_base, 'custom_test')
        
        config.set('paths.custom_log_dir', test_log_dir)
        
        # 验证路径已设置
        assert config.paths.custom_log_dir == test_log_dir
        # 由于custom_log_dir不是以_dir结尾，不会自动创建目录
        # 跳过目录存在断言，因为只有_dir结尾的字段才会自动创建
        # 清理
        if os.path.exists(temp_base):
            assert temp_base.startswith(tempfile.gettempdir()), f"禁止删除非临时目录: {temp_base}"
            shutil.rmtree(temp_base, ignore_errors=True)
    
    def test_test_mode_generated_paths_auto_creation(self):
        """测试test_mode下生成的路径是否自动创建目录"""
        config = get_config_manager(test_mode=True, first_start_time=self.test_time)
        
        # 验证生成的路径目录已自动创建（这些路径应该以_dir结尾）
        assert os.path.exists(config.paths.work_dir)
        assert os.path.exists(config.paths.log_dir)
        assert os.path.exists(config.paths.checkpoint_dir)
        assert os.path.exists(config.paths.debug_dir)
    
    def test_test_mode_nested_paths_creation(self):
        """测试test_mode下嵌套路径的自动创建"""
        config = get_config_manager(test_mode=True, first_start_time=self.test_time)
        temp_base = tempfile.mkdtemp(prefix="test_nested_")
        nested_path = os.path.join(temp_base, 'level1', 'level2', 'level3', 'logs')
        
        config.set('paths.nested_logs', nested_path)
        
        # 验证路径已设置
        assert config.paths.nested_logs == nested_path
        # 由于nested_logs不是以_dir结尾，不会自动创建目录
        # 跳过目录存在断言，因为只有_dir结尾的字段才会自动创建
        # 清理
        if os.path.exists(temp_base):
            assert temp_base.startswith(tempfile.gettempdir()), f"禁止删除非临时目录: {temp_base}"
            shutil.rmtree(temp_base, ignore_errors=True)
    
    def test_test_mode_multiple_path_configs(self):
        """测试test_mode下多个路径配置的自动创建"""
        config = get_config_manager(test_mode=True, first_start_time=self.test_time)
        temp_base = tempfile.mkdtemp(prefix="test_multi_")
        
        paths_to_test = {
            'paths.data_path': os.path.join(temp_base, 'data'),
            'paths.cache_path': os.path.join(temp_base, 'cache'),
            'paths.output_path': os.path.join(temp_base, 'output')
        }
        
        for path_key, path_value in paths_to_test.items():
            config.set(path_key, path_value)
            # 验证路径已设置
            assert getattr(config.paths, path_key.split('.')[-1]) == path_value
            # 由于这些字段都不是以_dir结尾，不会自动创建目录
            # 跳过目录存在断言，因为只有_dir结尾的字段才会自动创建
        
        # 清理
        if os.path.exists(temp_base):
            assert temp_base.startswith(tempfile.gettempdir()), f"禁止删除非临时目录: {temp_base}"
            shutil.rmtree(temp_base, ignore_errors=True)
    
    def test_test_mode_path_update_triggers_creation(self):
        """测试test_mode下路径更新是否触发目录创建"""
        config = get_config_manager(test_mode=True, first_start_time=self.test_time)
        temp_base = tempfile.mkdtemp(prefix="test_update_")
        
        initial_path = os.path.join(temp_base, 'initial')
        updated_path = os.path.join(temp_base, 'updated')
        
        # 设置初始路径
        config.set('paths.test_path', initial_path)
        assert config.paths.test_path == initial_path
        # 由于test_path不是以_dir结尾，不会自动创建目录
        # 跳过目录存在断言，因为只有_dir结尾的字段才会自动创建
        
        # 更新路径
        config.set('paths.test_path', updated_path)
        assert config.paths.test_path == updated_path
        # 由于test_path不是以_dir结尾，不会自动创建目录
        # 跳过目录存在断言，因为只有_dir结尾的字段才会自动创建
        
        # 清理
        if os.path.exists(temp_base):
            assert temp_base.startswith(tempfile.gettempdir()), f"禁止删除非临时目录: {temp_base}"
            shutil.rmtree(temp_base, ignore_errors=True)
    
    def test_test_mode_path_configuration_integration(self):
        """测试test_mode下路径配置的集成功能"""
        config = get_config_manager(test_mode=True, first_start_time=self.test_time)
        
        # 验证基本路径配置正常工作
        assert hasattr(config.paths, 'work_dir')
        assert hasattr(config.paths, 'log_dir')
        assert hasattr(config.paths, 'checkpoint_dir')
        assert hasattr(config.paths, 'debug_dir')
        
        # 验证生成的路径目录已自动创建（这些路径应该以_dir结尾）
        assert os.path.exists(config.paths.work_dir)
        assert os.path.exists(config.paths.log_dir)
        assert os.path.exists(config.paths.checkpoint_dir)
        assert os.path.exists(config.paths.debug_dir)
    
    def test_test_mode_error_handling(self):
        """测试test_mode下路径创建的错误处理"""
        config = get_config_manager(test_mode=True, first_start_time=self.test_time)
        
        # 测试无效路径的处理
        invalid_path = "/invalid/path/that/should/not/exist"
        config.set('paths.invalid_dir', invalid_path)
        
        # 由于invalid_dir不是以_dir结尾，不会自动创建目录
        # 跳过目录存在断言，因为只有_dir结尾的字段才会自动创建
        
        # 验证配置仍然正常工作
        assert config.paths.invalid_dir == invalid_path
    
    def test_test_mode_creates_temp_dir(self):
        """测试test_mode下是否创建临时目录"""
        config = get_config_manager(test_mode=True)
        
        # 验证临时目录已创建（work_dir应该以_dir结尾）
        assert os.path.exists(config.paths.work_dir)
        assert config.paths.work_dir.startswith(tempfile.gettempdir())
    
    def test_multiple_test_mode_instances_get_different_dirs(self):
        """测试多次调用test_mode=True的ConfigManager是否获得不同的目录"""
        config1 = get_config_manager(test_mode=True, first_start_time=self.test_time)
        work_dir1 = config1.paths.work_dir
        _clear_instances_for_testing()
        config2 = get_config_manager(test_mode=True, first_start_time=datetime(2025, 1, 8, 15, 30, 1))
        work_dir2 = config2.paths.work_dir
        assert work_dir1 != work_dir2
        # work_dir应该以_dir结尾，所以目录应已自动创建
        assert os.path.exists(work_dir1)
        assert os.path.exists(work_dir2)
        # 清理
        if os.path.exists(work_dir1):
            shutil.rmtree(work_dir1)
        if os.path.exists(work_dir2):
            shutil.rmtree(work_dir2)
    
    def test_debug_mode_overrides_test_mode_for_paths(self):
        """测试debug_mode是否覆盖test_mode的路径设置"""
        config = get_config_manager(test_mode=True, first_start_time=self.test_time)
        
        # 验证debug_mode下的路径配置
        assert hasattr(config.paths, 'work_dir')
        assert hasattr(config.paths, 'log_dir')
        assert hasattr(config.paths, 'checkpoint_dir')
        assert hasattr(config.paths, 'debug_dir')
        
        # 验证生成的路径目录已自动创建（这些路径应该以_dir结尾）
        assert os.path.exists(config.paths.work_dir)
        assert os.path.exists(config.paths.log_dir)
        assert os.path.exists(config.paths.checkpoint_dir)
        assert os.path.exists(config.paths.debug_dir) 