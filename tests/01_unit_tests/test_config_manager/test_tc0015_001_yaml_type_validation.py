# tests/01_unit_tests/test_config_manager/test_tc0015_001_yaml_type_validation.py
from __future__ import annotations
from datetime import datetime

start_time = datetime.now()

import pytest
import tempfile
import os
import sys
import yaml

# 安全添加路径
src_path = os.path.join(os.path.dirname(__file__), '..', '..', '..')
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from src.config_manager.config_manager import get_config_manager, _clear_instances_for_testing


@pytest.fixture(autouse=True)
def cleanup_instances():
    """每个测试后清理实例"""
    yield
    _clear_instances_for_testing()
    pass


def test_tc0015_001_001_detect_quoted_integer_string():
    """测试检测引号包围的整数字符串并抛出错误"""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_file = os.path.join(tmpdir, 'test_config.yaml')
        
        # 创建包含错误类型的配置文件：引号包围的数字
        config_data = {
            '__data__': {
                'port': "8080",  # 错误：应该是数字 8080
                'name': "test_app"  # 正确：字符串
            },
            '__type_hints__': {}
        }
        
        with open(config_file, 'w', encoding='utf-8') as f:
            yaml.dump(config_data, f)
        
        # 尝试加载配置，应该抛出TypeError
        with pytest.raises(TypeError) as exc_info:
            get_config_manager(config_path=config_file, watch=False, test_mode=True)
        
        error_message = str(exc_info.value)
        assert "port" in error_message
        assert "8080" in error_message
        assert "字符串类型，但看起来像数字" in error_message
    pass


def test_tc0015_001_002_detect_quoted_float_string():
    """测试检测引号包围的浮点数字符串并抛出错误"""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_file = os.path.join(tmpdir, 'test_config.yaml')
        
        # 创建包含错误类型的配置文件：引号包围的浮点数
        config_data = {
            '__data__': {
                'version': "1.2",  # 错误：应该是浮点数 1.2
                'name': "test_app"  # 正确：字符串
            },
            '__type_hints__': {}
        }
        
        with open(config_file, 'w', encoding='utf-8') as f:
            yaml.dump(config_data, f)
        
        # 尝试加载配置，应该抛出TypeError
        with pytest.raises(TypeError) as exc_info:
            get_config_manager(config_path=config_file, watch=False, test_mode=True)
        
        error_message = str(exc_info.value)
        assert "version" in error_message
        assert "1.2" in error_message
        assert "字符串类型，但看起来像浮点数" in error_message
    pass


def test_tc0015_001_003_detect_quoted_boolean_string():
    """测试检测引号包围的布尔值字符串并抛出错误"""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_file = os.path.join(tmpdir, 'test_config.yaml')
        
        # 创建包含错误类型的配置文件：引号包围的布尔值
        config_data = {
            '__data__': {
                'enabled': "true",  # 错误：应该是布尔值 true
                'name': "test_app"  # 正确：字符串
            },
            '__type_hints__': {}
        }
        
        with open(config_file, 'w', encoding='utf-8') as f:
            yaml.dump(config_data, f)
        
        # 尝试加载配置，应该抛出TypeError
        with pytest.raises(TypeError) as exc_info:
            get_config_manager(config_path=config_file, watch=False, test_mode=True)
        
        error_message = str(exc_info.value)
        assert "enabled" in error_message
        assert "true" in error_message
        assert "字符串类型，但看起来像布尔值" in error_message
    pass


def test_tc0015_001_004_detect_quoted_false_boolean_string():
    """测试检测引号包围的false布尔值字符串并抛出错误"""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_file = os.path.join(tmpdir, 'test_config.yaml')
        
        # 创建包含错误类型的配置文件：引号包围的false
        config_data = {
            '__data__': {
                'disabled': "false",  # 错误：应该是布尔值 false
                'name': "test_app"    # 正确：字符串
            },
            '__type_hints__': {}
        }
        
        with open(config_file, 'w', encoding='utf-8') as f:
            yaml.dump(config_data, f)
        
        # 尝试加载配置，应该抛出TypeError
        with pytest.raises(TypeError) as exc_info:
            get_config_manager(config_path=config_file, watch=False, test_mode=True)
        
        error_message = str(exc_info.value)
        assert "disabled" in error_message
        assert "false" in error_message
        assert "字符串类型，但看起来像布尔值" in error_message
    pass


def test_tc0015_001_005_correct_types_load_successfully():
    """测试正确的类型应该成功加载"""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_file = os.path.join(tmpdir, 'test_config.yaml')
        
        # 创建包含正确类型的配置文件
        config_data = {
            '__data__': {
                'port': 8080,           # 正确：数字
                'version': 1.2,         # 正确：浮点数
                'enabled': True,        # 正确：布尔值
                'disabled': False,      # 正确：布尔值
                'name': "test_app",     # 正确：字符串
                'description': "A test application"  # 正确：字符串
            },
            '__type_hints__': {}
        }
        
        with open(config_file, 'w', encoding='utf-8') as f:
            yaml.dump(config_data, f)
        
        # 加载配置，应该成功
        cfg = get_config_manager(config_path=config_file, watch=False, test_mode=True)
        
        # 验证类型
        assert cfg.port == 8080
        assert isinstance(cfg.port, int)
        
        assert cfg.version == 1.2
        assert isinstance(cfg.version, float)
        
        assert cfg.enabled is True
        assert isinstance(cfg.enabled, bool)
        
        assert cfg.disabled is False
        assert isinstance(cfg.disabled, bool)
        
        assert cfg.name == "test_app"
        assert isinstance(cfg.name, str)
        
        assert cfg.description == "A test application"
        assert isinstance(cfg.description, str)
    pass


def test_tc0015_001_006_nested_structure_type_validation():
    """测试嵌套结构中的类型验证"""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_file = os.path.join(tmpdir, 'test_config.yaml')
        
        # 创建包含嵌套结构错误类型的配置文件
        config_data = {
            '__data__': {
                'database': {
                    'host': "localhost",  # 正确：字符串
                    'port': "5432",       # 错误：应该是数字 5432
                    'timeout': 30         # 正确：数字
                },
                'name': "test_app"        # 正确：字符串
            },
            '__type_hints__': {}
        }
        
        with open(config_file, 'w', encoding='utf-8') as f:
            yaml.dump(config_data, f)
        
        # 尝试加载配置，应该抛出TypeError
        with pytest.raises(TypeError) as exc_info:
            get_config_manager(config_path=config_file, watch=False, test_mode=True)
        
        error_message = str(exc_info.value)
        assert "database.port" in error_message
        assert "5432" in error_message
        assert "字符串类型，但看起来像数字" in error_message
    pass


def test_tc0015_001_007_list_structure_type_validation():
    """测试列表结构中的类型验证"""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_file = os.path.join(tmpdir, 'test_config.yaml')
        
        # 创建包含列表结构错误类型的配置文件
        config_data = {
            '__data__': {
                'ports': [8080, "8081", 8082],  # 错误：中间的应该是数字 8081
                'name': "test_app"              # 正确：字符串
            },
            '__type_hints__': {}
        }
        
        with open(config_file, 'w', encoding='utf-8') as f:
            yaml.dump(config_data, f)
        
        # 尝试加载配置，应该抛出TypeError
        with pytest.raises(TypeError) as exc_info:
            get_config_manager(config_path=config_file, watch=False, test_mode=True)
        
        error_message = str(exc_info.value)
        assert "ports[1]" in error_message
        assert "8081" in error_message
        assert "字符串类型，但看起来像数字" in error_message
    pass


def test_tc0015_001_008_legitimate_string_numbers_allowed():
    """测试合法的字符串数字（如版本号、ID等）应该被允许"""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_file = os.path.join(tmpdir, 'test_config.yaml')
        
        # 创建包含合法字符串数字的配置文件
        config_data = {
            '__data__': {
                'version_number': "v1.2.3",    # 合法：版本号字符串
                'user_id': "user123",          # 合法：用户ID字符串
                'api_key': "abc123def",        # 合法：API密钥字符串
                'port': 8080,                  # 正确：数字
                'name': "test_app"             # 正确：字符串
            },
            '__type_hints__': {}
        }
        
        with open(config_file, 'w', encoding='utf-8') as f:
            yaml.dump(config_data, f)
        
        # 加载配置，应该成功
        cfg = get_config_manager(config_path=config_file, watch=False, test_mode=True)
        
        # 验证值
        assert cfg.version_number == "v1.2.3"
        assert isinstance(cfg.version_number, str)
        
        assert cfg.user_id == "user123"
        assert isinstance(cfg.user_id, str)
        
        assert cfg.api_key == "abc123def"
        assert isinstance(cfg.api_key, str)
        
        assert cfg.port == 8080
        assert isinstance(cfg.port, int)
    pass