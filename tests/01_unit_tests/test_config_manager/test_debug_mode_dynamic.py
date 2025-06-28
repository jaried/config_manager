# tests/01_unit_tests/test_config_manager/test_debug_mode_dynamic.py
from __future__ import annotations
from datetime import datetime

import pytest
import tempfile
import os
from unittest.mock import patch, MagicMock
from pathlib import Path
import sys

# Add project root to Python path
# 项目根目录由conftest.py自动配置

from config_manager import get_config_manager, _clear_instances_for_testing

@pytest.fixture(autouse=True)
def clear_instances_fixture():
    """在每个测试前后自动清理ConfigManager单例"""
    _clear_instances_for_testing()
    yield
    _clear_instances_for_testing()


class TestDebugModeDynamic:
    """测试debug_mode属性的动态行为"""

    @patch('is_debug.is_debug', return_value=True)
    def test_debug_mode_returns_is_debug_result_true(self, mock_is_debug, tmp_path: Path):
        """当is_debug()返回True时，测试debug_mode属性"""
        # 在test_mode下，我们不需要显式传递config_path，让它自动处理
        config = get_config_manager(test_mode=True, config_path=str(tmp_path / "config.yaml"))
        assert config is not None
        assert config.debug_mode is True

    @patch('is_debug.is_debug', return_value=False)
    def test_debug_mode_returns_is_debug_result_false(self, mock_is_debug, tmp_path: Path):
        """当is_debug()返回False时，测试debug_mode属性"""
        config = get_config_manager(test_mode=True, config_path=str(tmp_path / "config.yaml"))
        assert config is not None
        assert config.debug_mode is False

    @patch('is_debug.is_debug', side_effect=ImportError)
    def test_debug_mode_with_is_debug_import_error(self, mock_is_debug, tmp_path: Path):
        """测试当is_debug模块不可用时，debug_mode的行为"""
        config = get_config_manager(test_mode=True, config_path=str(tmp_path / "config.yaml"))
        assert config is not None
        assert config.debug_mode is False
        
    @patch('is_debug.is_debug', return_value=True)
    def test_debug_mode_is_dynamic_and_not_cached(self, mock_is_debug, tmp_path: Path):
        """测试debug_mode属性是否为动态调用，而不是缓存值"""
        config = get_config_manager(test_mode=True, config_path=str(tmp_path / "config.yaml"))
        assert config is not None
        
        assert config.debug_mode is True
        
        mock_is_debug.return_value = False
        
        assert config.debug_mode is False
        assert mock_is_debug.call_count >= 2

    def test_setting_debug_mode_manually_is_ignored(self, tmp_path: Path):
        """测试手动设置debug_mode无效，因为它是一个动态只读属性"""
        config = get_config_manager(test_mode=True, config_path=str(tmp_path / "config.yaml"))
        assert config is not None
        
        # debug_mode的设置会被静默忽略，而不是抛出异常
        original_debug_mode = config.debug_mode
        config.debug_mode = True
        # 设置后，debug_mode应该仍然保持原值（由is_debug()决定）
        assert config.debug_mode == original_debug_mode



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
                
                # 获取工作目录
                work_dir = config.get('paths.work_dir')
                
                # 验证调试模式路径结构
                assert work_dir is not None and work_dir != ''
                assert 'debug' in work_dir or 'integration_test' in work_dir
    
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