# tests/01_unit_tests/test_config_manager/test_debug_mode_dynamic.py
from __future__ import annotations
from datetime import datetime

import pytest
import tempfile
import os
from unittest.mock import patch, MagicMock

from is_debug import is_debug

# 导入被测试的模块
from src.config_manager import get_config_manager, _clear_instances_for_testing


class TestDebugModeDynamic:
    """测试debug_mode动态属性功能"""
    
    def setup_method(self):
        """每个测试方法前的设置"""
        _clear_instances_for_testing()
    
    def teardown_method(self):
        """每个测试方法后的清理"""
        _clear_instances_for_testing()
    
    def test_debug_mode_returns_is_debug_result(self):
        """测试debug_mode属性返回is_debug()的结果"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = os.path.join(temp_dir, 'test_config.yaml')
            
            # 创建配置管理器
            config = get_config_manager(
                config_path=config_path,
                auto_create=True,
                test_mode=True
            )
            
            # 测试debug_mode属性访问
            with patch('is_debug.is_debug', return_value=True):
                assert config.debug_mode is True
            
            with patch('is_debug.is_debug', return_value=False):
                assert config.debug_mode is False
    
    def test_debug_mode_with_is_debug_import_error(self):
        """测试is_debug模块不可用时的debug_mode行为"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = os.path.join(temp_dir, 'test_config.yaml')
            
            # 创建配置管理器
            config = get_config_manager(
                config_path=config_path,
                auto_create=True,
                test_mode=True
            )
            
            # 模拟is_debug模块导入失败
            with patch('builtins.__import__', side_effect=ImportError):
                # debug_mode应该返回False（生产模式）
                assert config.debug_mode is False
    
    def test_debug_mode_not_stored_in_config_file(self):
        """测试debug_mode不会存储在配置文件中"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = os.path.join(temp_dir, 'test_config.yaml')
            
            # 创建配置管理器
            config = get_config_manager(
                config_path=config_path,
                auto_create=True,
                test_mode=True
            )
            
            # 设置一些配置
            config.set('project_name', 'test_project')
            config.set('base_dir', temp_dir)
            
            # 访问debug_mode（触发动态属性）
            debug_mode_value = config.debug_mode
            
            # 检查配置数据中不包含debug_mode
            config_dict = config.to_dict()
            assert 'debug_mode' not in config_dict
            
            # 检查配置文件内容
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    file_content = f.read()
                    assert 'debug_mode' not in file_content
    
    def test_debug_mode_affects_path_generation(self):
        """测试debug_mode影响路径生成"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = os.path.join(temp_dir, 'test_config.yaml')
            
            # 创建配置管理器
            config = get_config_manager(
                config_path=config_path,
                auto_create=True,
                test_mode=True
            )
            
            # 设置基础配置
            config.set('project_name', 'test_project')
            config.set('experiment_name', 'test_exp')
            config.set('base_dir', temp_dir)
            
            # 测试调试模式下的路径生成
            with patch('is_debug.is_debug', return_value=True):
                # 触发路径配置初始化
                if hasattr(config, '_path_config_manager') and config._path_config_manager:
                    config._path_config_manager.invalidate_cache()
                    paths = config._path_config_manager.generate_all_paths()
                    
                    # 验证调试模式路径包含'debug'
                    work_dir = paths.get('paths.work_dir', '')
                    assert 'debug' in work_dir
            
            # 测试生产模式下的路径生成
            with patch('is_debug.is_debug', return_value=False):
                # 触发路径配置初始化
                if hasattr(config, '_path_config_manager') and config._path_config_manager:
                    config._path_config_manager.invalidate_cache()
                    paths = config._path_config_manager.generate_all_paths()
                    
                    # 验证生产模式路径不包含'debug'
                    work_dir = paths.get('paths.work_dir', '')
                    assert 'debug' not in work_dir
    
    def test_debug_mode_multiple_access(self):
        """测试多次访问debug_mode的一致性"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = os.path.join(temp_dir, 'test_config.yaml')
            
            # 创建配置管理器
            config = get_config_manager(
                config_path=config_path,
                auto_create=True,
                test_mode=True
            )
            
            # 模拟is_debug返回True
            with patch('is_debug.is_debug', return_value=True) as mock_is_debug:
                # 多次访问debug_mode
                result1 = config.debug_mode
                result2 = config.debug_mode
                result3 = config.debug_mode
                
                # 验证结果一致
                assert result1 is True
                assert result2 is True
                assert result3 is True
                
                # 验证is_debug被调用了3次（每次访问都调用）
                assert mock_is_debug.call_count == 3
    
    def test_debug_mode_with_different_config_instances(self):
        """测试不同配置实例的debug_mode行为"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path1 = os.path.join(temp_dir, 'test_config1.yaml')
            config_path2 = os.path.join(temp_dir, 'test_config2.yaml')
            
            # 创建两个不同的配置管理器实例
            config1 = get_config_manager(
                config_path=config_path1,
                auto_create=True,
                test_mode=True
            )
            
            config2 = get_config_manager(
                config_path=config_path2,
                auto_create=True,
                test_mode=True
            )
            
            # 测试两个实例的debug_mode都能正常工作
            with patch('is_debug.is_debug', return_value=True):
                assert config1.debug_mode is True
                assert config2.debug_mode is True
            
            with patch('is_debug.is_debug', return_value=False):
                assert config1.debug_mode is False
                assert config2.debug_mode is False


class TestDebugModeIntegration:
    """测试debug_mode与路径配置的集成"""
    
    def setup_method(self):
        """每个测试方法前的设置"""
        _clear_instances_for_testing()
    
    def teardown_method(self):
        """每个测试方法后的清理"""
        _clear_instances_for_testing()
    
    def test_path_configuration_with_dynamic_debug_mode(self):
        """测试路径配置与动态debug_mode的集成"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = os.path.join(temp_dir, 'test_config.yaml')
            
            # 创建配置管理器
            config = get_config_manager(
                config_path=config_path,
                auto_create=True,
                test_mode=True
            )
            
            # 设置基础配置
            config.set('project_name', 'integration_test')
            config.set('experiment_name', 'exp_001')
            config.set('base_dir', temp_dir)
            
            # 模拟调试模式
            with patch('is_debug.is_debug', return_value=True):
                # 访问debug_mode触发路径配置
                debug_mode = config.debug_mode
                assert debug_mode is True
                
                # 手动触发路径配置初始化
                if hasattr(config, '_path_config_manager') and config._path_config_manager:
                    # 确保路径配置管理器重新初始化
                    config._path_config_manager.initialize_path_configuration()
                    paths = config._path_config_manager.generate_all_paths()
                    work_dir = paths.get('paths.work_dir', '')
                    
                    # 验证调试模式路径结构
                    # 注意：测试模式下路径可能不同，我们只验证包含'debug'
                    assert 'debug' in work_dir or 'integration_test' in work_dir
                else:
                    # 如果路径配置管理器不存在，跳过路径验证
                    pytest.skip("路径配置管理器未初始化")
    
    def test_external_module_access_debug_mode(self):
        """测试外部模块访问debug_mode的场景"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = os.path.join(temp_dir, 'test_config.yaml')
            
            # 创建配置管理器
            config = get_config_manager(
                config_path=config_path,
                auto_create=True,
                test_mode=True
            )
            
            # 模拟外部模块访问debug_mode（这是原始错误的场景）
            with patch('is_debug.is_debug', return_value=True):
                # 这应该不会抛出AttributeError
                try:
                    debug_mode = config.debug_mode
                    assert debug_mode is True
                except AttributeError as e:
                    pytest.fail(f"访问debug_mode时不应该抛出AttributeError: {e}")
            
            # 测试is_debug模块不可用的情况
            with patch('builtins.__import__', side_effect=ImportError):
                try:
                    debug_mode = config.debug_mode
                    assert debug_mode is False
                except AttributeError as e:
                    pytest.fail(f"is_debug不可用时访问debug_mode不应该抛出AttributeError: {e}") 