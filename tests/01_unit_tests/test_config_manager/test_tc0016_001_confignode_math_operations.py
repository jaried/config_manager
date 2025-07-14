# tests/01_unit_tests/test_config_manager/test_tc0016_001_confignode_math_operations.py
from __future__ import annotations
from datetime import datetime

start_time = datetime.now()

import pytest
import tempfile
import os
import sys

# 安全添加路径
src_path = os.path.join(os.path.dirname(__file__), '..', '..', '..')
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from src.config_manager.config_manager import get_config_manager, _clear_instances_for_testing
from src.config_manager.config_node import ConfigNode


@pytest.fixture(autouse=True)
def cleanup_instances():
    """每个测试后清理实例"""
    yield
    _clear_instances_for_testing()
    pass


def test_tc0016_001_001_single_value_auto_unpack():
    """测试单值ConfigNode自动解包"""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_file = os.path.join(tmpdir, 'test_config.yaml')
        cfg = get_config_manager(config_path=config_file, watch=False, test_mode=True)
        
        # 设置单值字典，应该自动解包
        cfg.test_value = {'single': 42}
        
        # 访问时应该返回基础类型
        assert cfg.test_value == 42
        assert isinstance(cfg.test_value, int)
        
        # 数学运算应该正常工作
        result = cfg.test_value * 2.0
        assert result == 84.0
    pass


def test_tc0016_001_002_multi_value_confignode_math_error():
    """测试多值ConfigNode数学运算错误"""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_file = os.path.join(tmpdir, 'test_config.yaml')
        cfg = get_config_manager(config_path=config_file, watch=False, test_mode=True)
        
        # 设置多值字典，应该保持为ConfigNode
        cfg.batch_size = {'train': 32, 'val': 16}
        
        # 访问时应该返回ConfigNode
        assert isinstance(cfg.batch_size, ConfigNode)
        
        # 数学运算应该抛出清晰的错误
        with pytest.raises(TypeError) as exc_info:
            cfg.batch_size * 2.0
        
        error_message = str(exc_info.value)
        assert "ConfigNode乘法运算失败" in error_message
        assert "{'train': 32, 'val': 16}" in error_message
        assert "请检查配置值是否为正确的数值类型" in error_message
    pass


def test_tc0016_001_003_confignode_math_operations():
    """测试ConfigNode各种数学运算"""
    node = ConfigNode({'value': 10})
    
    # 测试各种数学运算
    assert node * 2 == 20.0
    assert 2 * node == 20.0
    assert node + 5 == 15.0
    assert 5 + node == 15.0
    assert node - 3 == 7.0
    assert 20 - node == 10.0
    assert node / 2 == 5.0
    assert 50 / node == 5.0
    pass


def test_tc0016_001_004_confignode_type_conversion():
    """测试ConfigNode类型转换"""
    node = ConfigNode({'value': 10})
    
    # 测试类型转换
    assert float(node) == 10.0
    assert int(node) == 10
    pass


def test_tc0016_001_005_invalid_confignode_conversion():
    """测试无效ConfigNode转换"""
    # 多值ConfigNode无法转换
    multi_node = ConfigNode({'a': 1, 'b': 2})
    
    with pytest.raises(TypeError) as exc_info:
        float(multi_node)
    
    assert "无法将ConfigNode转换为float" in str(exc_info.value)
    assert "ConfigNode应该包含单个数值才能进行数学运算" in str(exc_info.value)
    
    # 包含非数值的ConfigNode无法转换
    str_node = ConfigNode({'value': 'text'})
    
    with pytest.raises(TypeError) as exc_info:
        float(str_node)
    
    assert "无法将ConfigNode转换为float" in str(exc_info.value)
    pass


def test_tc0016_001_006_nested_confignode_no_auto_unpack():
    """测试嵌套ConfigNode不会自动解包"""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_file = os.path.join(tmpdir, 'test_config.yaml')
        cfg = get_config_manager(config_path=config_file, watch=False, test_mode=True)
        
        # 设置嵌套结构
        cfg.nested = {'level1': {'level2': 42}}
        
        # 访问时应该返回ConfigNode，不会自动解包
        assert isinstance(cfg.nested, ConfigNode)
        assert 'level1' in cfg.nested._data
        
        # 数学运算应该失败
        with pytest.raises(TypeError) as exc_info:
            cfg.nested * 2.0
        
        error_message = str(exc_info.value)
        assert "ConfigNode乘法运算失败" in error_message
    pass