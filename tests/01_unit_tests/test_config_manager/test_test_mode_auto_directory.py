# tests/01_unit_tests/test_config_manager/test_test_mode_auto_directory.py
from __future__ import annotations
from datetime import datetime

start_time = datetime.now()

import pytest
import tempfile
import os
from pathlib import Path
from is_debug import is_debug

from src.config_manager import get_config_manager


class TestTestModeAutoDirectory:
    """测试test_mode下的自动目录创建功能"""
    
    def setup_method(self):
        """测试前设置"""
        self.test_time = datetime(2025, 1, 8, 15, 30, 0)
    
    def test_test_mode_paths_auto_creation(self):
        """测试test_mode下paths命名空间的自动目录创建"""
        # 创建测试模式配置管理器
        config = get_config_manager(test_mode=True, first_start_time=self.test_time)
        
        # 使用tempfile.mkdtemp()创建唯一临时目录
        temp_base = tempfile.mkdtemp(prefix="test_auto_dir_")
        test_log_dir = os.path.join(temp_base, 'custom_test')
        
        # 设置paths命名空间下的路径
        config.set('paths.custom_log_dir', test_log_dir)
        
        # 验证目录已创建
        assert os.path.exists(test_log_dir), f"测试模式下目录应该被自动创建: {test_log_dir}"
        assert os.path.isdir(test_log_dir), f"应该是一个目录: {test_log_dir}"
        
        # 清理
        import shutil
        if os.path.exists(temp_base):
            assert temp_base.startswith(tempfile.gettempdir()), f"禁止删除非临时目录: {temp_base}"
            shutil.rmtree(temp_base, ignore_errors=True)
    
    def test_test_mode_generated_paths_auto_creation(self):
        """测试test_mode下路径配置管理器生成的路径自动创建"""
        config = get_config_manager(test_mode=True, first_start_time=self.test_time)
        
        # 使用tempfile.mkdtemp()创建唯一临时目录
        temp_base = tempfile.mkdtemp(prefix="test_auto_dir_")
        config.set('base_dir', temp_base)
        config.set('project_name', 'test_auto_dir')
        config.set('experiment_name', 'test_exp')
        config.set('debug_mode', True)
        
        # 获取生成的路径
        work_dir = config.get('paths.work_dir')
        log_dir = config.get('paths.log_dir')
        checkpoint_dir = config.get('paths.checkpoint_dir')
        
        # 验证所有生成的路径目录都存在
        assert work_dir and os.path.exists(work_dir), f"工作目录应该存在: {work_dir}"
        assert log_dir and os.path.exists(log_dir), f"日志目录应该存在: {log_dir}"
        assert checkpoint_dir and os.path.exists(checkpoint_dir), f"检查点目录应该存在: {checkpoint_dir}"
        
        # 验证目录结构正确
        assert os.path.isdir(work_dir), f"工作目录应该是目录: {work_dir}"
        assert os.path.isdir(log_dir), f"日志目录应该是目录: {log_dir}"
        assert os.path.isdir(checkpoint_dir), f"检查点目录应该是目录: {checkpoint_dir}"
        
        # 清理
        import shutil
        if os.path.exists(temp_base):
            assert temp_base.startswith(tempfile.gettempdir()), f"禁止删除非临时目录: {temp_base}"
            shutil.rmtree(temp_base, ignore_errors=True)
    
    def test_test_mode_nested_paths_creation(self):
        """测试test_mode下深层嵌套路径的创建"""
        config = get_config_manager(test_mode=True, first_start_time=self.test_time)
        
        # 使用tempfile.mkdtemp()创建唯一临时目录
        temp_base = tempfile.mkdtemp(prefix="test_nested_")
        nested_path = os.path.join(temp_base, 'level1', 'level2', 'level3', 'logs')
        
        config.set('paths.deep_nested_dir', nested_path)
        
        # 验证所有层级目录都被创建
        assert os.path.exists(nested_path), f"深层嵌套目录应该被创建: {nested_path}"
        assert os.path.isdir(nested_path), f"应该是一个目录: {nested_path}"
        
        # 验证父目录也存在
        parent_dirs = [
            os.path.join(temp_base, 'level1'),
            os.path.join(temp_base, 'level1', 'level2'),
            os.path.join(temp_base, 'level1', 'level2', 'level3'),
        ]
        
        for parent_dir in parent_dirs:
            assert os.path.exists(parent_dir), f"父目录应该存在: {parent_dir}"
            assert os.path.isdir(parent_dir), f"父目录应该是目录: {parent_dir}"
        
        # 清理
        import shutil
        if os.path.exists(temp_base):
            assert temp_base.startswith(tempfile.gettempdir()), f"禁止删除非临时目录: {temp_base}"
            shutil.rmtree(temp_base, ignore_errors=True)
    
    def test_test_mode_multiple_path_configs(self):
        """测试test_mode下多个路径配置的批量创建"""
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
        
        # 验证所有目录都被创建
        for key, path in path_configs.items():
            assert os.path.exists(path), f"目录应该被创建 {key}: {path}"
            assert os.path.isdir(path), f"应该是目录 {key}: {path}"
        
        # 清理
        import shutil
        if os.path.exists(temp_base):
            assert temp_base.startswith(tempfile.gettempdir()), f"禁止删除非临时目录: {temp_base}"
            shutil.rmtree(temp_base, ignore_errors=True)
    
    def test_test_mode_path_update_triggers_creation(self):
        """测试test_mode下路径更新触发目录创建"""
        config = get_config_manager(test_mode=True, first_start_time=self.test_time)
        
        # 使用tempfile.mkdtemp()创建唯一临时目录
        temp_base = tempfile.mkdtemp(prefix="test_update_")
        
        # 初始设置
        initial_path = os.path.join(temp_base, 'initial')
        config.set('paths.update_test_dir', initial_path)
        
        # 验证初始目录创建
        assert os.path.exists(initial_path), f"初始目录应该被创建: {initial_path}"
        
        # 更新路径
        updated_path = os.path.join(temp_base, 'updated')
        config.set('paths.update_test_dir', updated_path)
        
        # 验证新目录也被创建
        assert os.path.exists(updated_path), f"更新后的目录应该被创建: {updated_path}"
        assert os.path.exists(initial_path), f"初始目录应该仍然存在: {initial_path}"
        
        # 清理
        import shutil
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
        
        # 手动触发路径配置更新（模拟实际使用场景）
        if hasattr(config, '_path_config_manager') and config._path_config_manager:
            config._path_config_manager.invalidate_cache()
            path_configs = config._path_config_manager.generate_all_paths()
            
            # 验证所有生成的路径都存在
            for path_key, path_value in path_configs.items():
                if path_value and isinstance(path_value, str):
                    assert os.path.exists(path_value), f"集成测试中路径应该存在: {path_key} = {path_value}"
                    assert os.path.isdir(path_value), f"应该是目录: {path_key} = {path_value}"
        
        # 验证可以通过config.paths访问
        assert hasattr(config, 'paths'), "应该有paths属性"
        assert config.paths.work_dir, "work_dir应该有值"
        assert config.paths.log_dir, "log_dir应该有值"
        assert config.paths.checkpoint_dir, "checkpoint_dir应该有值"
        
        # 验证通过paths访问的目录都存在
        assert os.path.exists(config.paths.work_dir), f"通过paths访问的work_dir应该存在: {config.paths.work_dir}"
        assert os.path.exists(config.paths.log_dir), f"通过paths访问的log_dir应该存在: {config.paths.log_dir}"
        assert os.path.exists(config.paths.checkpoint_dir), f"通过paths访问的checkpoint_dir应该存在: {config.paths.checkpoint_dir}"
        
        # 清理
        import shutil
        if os.path.exists(temp_base):
            assert temp_base.startswith(tempfile.gettempdir()), f"禁止删除非临时目录: {temp_base}"
            shutil.rmtree(temp_base, ignore_errors=True)
    
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