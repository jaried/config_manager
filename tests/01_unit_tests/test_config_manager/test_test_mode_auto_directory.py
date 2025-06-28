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

from src.config_manager import get_config_manager, _clear_instances_for_testing

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
        """测试test_mode下paths命名空间的路径设置，不再自动创建"""
        config = get_config_manager(test_mode=True, first_start_time=self.test_time)
        temp_base = tempfile.mkdtemp(prefix="test_auto_dir_")
        test_log_dir = os.path.join(temp_base, 'custom_test')
        
        config.set('paths.custom_log_dir', test_log_dir)
        
        # 验证路径已设置
        assert config.paths.custom_log_dir == test_log_dir
        # 验证目录不再自动创建
        assert not os.path.exists(test_log_dir)
    
    def test_test_mode_generated_paths_auto_creation(self):
        """测试test_mode下路径配置管理器生成的路径，不再自动创建"""
        config = get_config_manager(test_mode=True, first_start_time=self.test_time)
        
        # 使用tempfile.mkdtemp()创建唯一临时目录
        temp_base = tempfile.mkdtemp(prefix="test_auto_dir_")
        config.set('base_dir', temp_base)
        config.set('project_name', 'test_auto_dir')
        config.set('experiment_name', 'test_exp')
        config.set('debug_mode', True)
        
        # 显式调用路径生成
        config.setup_project_paths()
        
        # 获取生成的路径
        work_dir = config.get('paths.work_dir')
        log_dir = config.get('paths.log_dir')
        checkpoint_dir = config.get('paths.checkpoint_dir')
        
        # 验证所有生成的路径目录都不存在
        assert work_dir and not os.path.exists(work_dir)
        assert log_dir and not os.path.exists(log_dir)
        assert checkpoint_dir and not os.path.exists(checkpoint_dir)
        
        # 手动创建并验证
        os.makedirs(work_dir)
        os.makedirs(log_dir)
        os.makedirs(checkpoint_dir)
        assert os.path.isdir(work_dir)
        assert os.path.isdir(log_dir)
        assert os.path.isdir(checkpoint_dir)
        
        # 清理
        if os.path.exists(temp_base):
            assert temp_base.startswith(tempfile.gettempdir()), f"禁止删除非临时目录: {temp_base}"
            shutil.rmtree(temp_base, ignore_errors=True)
    
    def test_test_mode_nested_paths_creation(self):
        """测试test_mode下深层嵌套路径的设置，不再自动创建"""
        config = get_config_manager(test_mode=True, first_start_time=self.test_time)
        
        # 使用tempfile.mkdtemp()创建唯一临时目录
        temp_base = tempfile.mkdtemp(prefix="test_nested_")
        nested_path = os.path.join(temp_base, 'level1', 'level2', 'level3', 'logs')
        
        config.set('paths.deep_nested_dir', nested_path)
        
        # 验证所有层级目录都未被创建
        assert not os.path.exists(nested_path)
        
        # 手动创建并验证
        os.makedirs(nested_path)
        assert os.path.exists(nested_path)
        assert os.path.isdir(nested_path)
        
        # 清理
        if os.path.exists(temp_base):
            assert temp_base.startswith(tempfile.gettempdir()), f"禁止删除非临时目录: {temp_base}"
            shutil.rmtree(temp_base, ignore_errors=True)
    
    def test_test_mode_multiple_path_configs(self):
        """测试test_mode下多个路径配置的批量设置，不再自动创建"""
        config = get_config_manager(test_mode=True, first_start_time=self.test_time)
        
        # 使用tempfile.mkdtemp()创建唯一临时目录
        temp_base = tempfile.mkdtemp(prefix="test_multi_")
        
        # 设置多个路径配置
        path_configs = {
            'paths.data_dir': os.path.join(temp_base, 'data'),
            'paths.model_dir': os.path.join(temp_base, 'models'),
            'paths.output_dir': os.path.join(temp_base, 'outputs'),
            'paths.cache_dir': os.path.join(temp_base, 'cache'),
        }
        
        # 批量设置路径
        for key, path in path_configs.items():
            config.set(key, path)
        
        # 验证所有目录都未被创建
        for key, path in path_configs.items():
            assert not os.path.exists(path)
        
        # 清理
        if os.path.exists(temp_base):
            assert temp_base.startswith(tempfile.gettempdir()), f"禁止删除非临时目录: {temp_base}"
            shutil.rmtree(temp_base, ignore_errors=True)
    
    def test_test_mode_path_update_triggers_creation(self):
        """测试test_mode下路径更新不再触发目录创建"""
        config = get_config_manager(test_mode=True, first_start_time=self.test_time)
        
        # 使用tempfile.mkdtemp()创建唯一临时目录
        temp_base = tempfile.mkdtemp(prefix="test_update_")
        
        # 初始设置
        initial_path = os.path.join(temp_base, 'initial')
        config.set('paths.update_test_dir', initial_path)
        
        # 验证初始目录未创建
        assert not os.path.exists(initial_path)
        
        # 更新路径
        updated_path = os.path.join(temp_base, 'updated')
        config.set('paths.update_test_dir', updated_path)
        
        # 验证新目录也未被创建
        assert not os.path.exists(updated_path)
        
        # 清理
        if os.path.exists(temp_base):
            assert temp_base.startswith(tempfile.gettempdir()), f"禁止删除非临时目录: {temp_base}"
            shutil.rmtree(temp_base, ignore_errors=True)
    
    def test_test_mode_path_configuration_integration(self):
        """测试test_mode下与路径配置管理器的完整集成"""
        config = get_config_manager(test_mode=True, first_start_time=self.test_time)
        
        # 使用tempfile.mkdtemp()创建唯一临时目录
        temp_base = tempfile.mkdtemp(prefix="test_integration_")
        
        # 设置完整的项目配置
        config.set('base_dir', temp_base)
        config.set('project_name', 'test_integration')
        config.set('experiment_name', 'exp_001')
        config.set('debug_mode', True)
        
        # 手动触发路径配置更新
        config.setup_project_paths()
            
        # 验证所有生成的路径都未自动创建
        path_configs = config.get('paths').to_dict()
        for path_key, path_value in path_configs.items():
            if path_value and isinstance(path_value, str):
                assert not os.path.exists(path_value)
        
        # 验证可以通过config.paths访问
        assert hasattr(config, 'paths'), "应该有paths属性"
        assert config.paths.work_dir, "work_dir应该有值"
        assert config.paths.log_dir, "log_dir应该有值"
        assert config.paths.checkpoint_dir, "checkpoint_dir应该有值"
        
        # 手动创建后验证
        os.makedirs(config.paths.work_dir, exist_ok=True)
        assert os.path.exists(config.paths.work_dir)
        
    def test_test_mode_error_handling(self):
        """测试test_mode下错误处理"""
        config = get_config_manager(test_mode=True, first_start_time=self.test_time)
        
        # 测试设置无效路径不会抛出异常
        try:
            config.set('paths.invalid_test', '')  # 空路径
            config.set('paths.another_invalid', 'not_a_real_path')  # 不像路径的值
        except Exception as e:
            pytest.fail(f"设置无效路径不应该抛出异常: {e}")
        
        # 测试设置非字符串值不会触发目录创建
        try:
            config.set('paths.numeric_value', 123)
            config.set('paths.boolean_value', True)
            config.set('paths.list_value', ['a', 'b', 'c'])
        except Exception as e:
            pytest.fail(f"设置非字符串值不应该抛出异常: {e}")

    @patch('is_debug.is_debug', return_value=False)
    def test_test_mode_creates_temp_dir(self, mock_is_debug):
        """测试test_mode=True时，是否在系统临时目录下生成路径"""
        config = get_config_manager(test_mode=True)
        config.setup_project_paths()
        
        work_dir = Path(config.paths.work_dir)
        # 验证目录不再自动创建
        assert not work_dir.exists()
        
        # 验证它是否在系统临时目录的子目录中
        # 这有点难直接断言，但我们可以检查它是否包含 'pytest' 或 'tmp' 等特征
        temp_dir_str = tempfile.gettempdir()
        assert str(work_dir).startswith(temp_dir_str)
        
    @patch('is_debug.is_debug', return_value=False)
    def test_multiple_test_mode_instances_get_different_dirs(self, mock_is_debug):
        """测试多次调用test_mode=True的ConfigManager是否获得不同的目录"""
        config1 = get_config_manager(test_mode=True, first_start_time=self.test_time)
        config1.setup_project_paths()
        
        _clear_instances_for_testing()
        
        # 使用不同的时间以确保路径不同
        config2 = get_config_manager(test_mode=True, first_start_time=datetime(2025, 1, 8, 15, 30, 1))
        config2.setup_project_paths()

        work_dir1 = Path(config1.paths.work_dir)
        work_dir2 = Path(config2.paths.work_dir)

        assert not work_dir1.exists()
        assert not work_dir2.exists()
        assert work_dir1 != work_dir2
    
    @patch('is_debug.is_debug', return_value=True)
    def test_debug_mode_overrides_test_mode_for_paths(self, mock_is_debug):
        """测试当is_debug()返回True时，即使test_mode=True，路径也应包含'debug'"""
        config = get_config_manager(test_mode=True, first_start_time=self.test_time)
        config.setup_project_paths()

        # 验证生成的work_dir是否包含'debug'部分
        work_dir = Path(config.paths.work_dir)
        assert 'debug' in work_dir.parts
        
        # 清理
        # 获取测试基础目录并清理
        test_base_dir = Path(config.get_config_file_path()).parents[2]
        if os.path.exists(test_base_dir) and 'pytest' in str(test_base_dir):
            shutil.rmtree(test_base_dir, ignore_errors=True) 