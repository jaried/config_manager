# tests/01_unit_tests/test_config_manager/test_tc0015_001_yaml_type_validation.py
"""
类型验证相关测试

注意：根据用户明确要求"不要验证，如果加引号，就是字符串，原样返回"，
类型验证功能已被禁用。这些测试现在验证引号包围的值被正确保留为字符串。
"""
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


def test_tc0015_001_001_quoted_integer_string_preserved():
    """测试引号包围的整数字符串被正确保留为字符串（按用户要求：加引号的就是字符串）"""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_file = os.path.join(tmpdir, 'test_config.yaml')
        
        # 创建包含引号包围的数字的配置文件
        config_data = {
            '__data__': {
                'port': "8080",  # 引号包围：应该保留为字符串
                'name': "test_app"  # 正常字符串
            },
            '__type_hints__': {}
        }
        
        with open(config_file, 'w', encoding='utf-8') as f:
            yaml.dump(config_data, f)
        
        # 加载配置，应该成功且保留字符串类型
        cfg = get_config_manager(config_path=config_file, watch=False, test_mode=True)
        
        # 验证引号包围的数字保留为字符串
        assert cfg.port == "8080"
        assert isinstance(cfg.port, str)
        
        assert cfg.name == "test_app"
        assert isinstance(cfg.name, str)
    pass


def test_tc0015_001_002_quoted_float_string_preserved():
    """测试引号包围的浮点数字符串被正确保留为字符串（按用户要求：加引号的就是字符串）"""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_file = os.path.join(tmpdir, 'test_config.yaml')
        
        # 创建包含引号包围的浮点数的配置文件
        config_data = {
            '__data__': {
                'version': "1.2",  # 引号包围：应该保留为字符串
                'name': "test_app"  # 正常字符串
            },
            '__type_hints__': {}
        }
        
        with open(config_file, 'w', encoding='utf-8') as f:
            yaml.dump(config_data, f)
        
        # 加载配置，应该成功且保留字符串类型
        cfg = get_config_manager(config_path=config_file, watch=False, test_mode=True)
        
        # 验证引号包围的浮点数保留为字符串
        assert cfg.version == "1.2"
        assert isinstance(cfg.version, str)
        
        assert cfg.name == "test_app"
        assert isinstance(cfg.name, str)
    pass


def test_tc0015_001_003_quoted_boolean_string_preserved():
    """测试引号包围的布尔值字符串被正确保留为字符串（按用户要求：加引号的就是字符串）"""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_file = os.path.join(tmpdir, 'test_config.yaml')
        
        # 创建包含引号包围的布尔值的配置文件
        config_data = {
            '__data__': {
                'enabled': "true",  # 引号包围：应该保留为字符串
                'name': "test_app"  # 正常字符串
            },
            '__type_hints__': {}
        }
        
        with open(config_file, 'w', encoding='utf-8') as f:
            yaml.dump(config_data, f)
        
        # 加载配置，应该成功且保留字符串类型
        cfg = get_config_manager(config_path=config_file, watch=False, test_mode=True)
        
        # 验证引号包围的布尔值保留为字符串
        assert cfg.enabled == "true"
        assert isinstance(cfg.enabled, str)
        
        assert cfg.name == "test_app"
        assert isinstance(cfg.name, str)
    pass


def test_tc0015_001_004_quoted_false_boolean_string_preserved():
    """测试引号包围的false布尔值字符串被正确保留为字符串（按用户要求：加引号的就是字符串）"""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_file = os.path.join(tmpdir, 'test_config.yaml')
        
        # 创建包含引号包围的false的配置文件
        config_data = {
            '__data__': {
                'disabled': "false",  # 引号包围：应该保留为字符串
                'name': "test_app"    # 正常字符串
            },
            '__type_hints__': {}
        }
        
        with open(config_file, 'w', encoding='utf-8') as f:
            yaml.dump(config_data, f)
        
        # 加载配置，应该成功且保留字符串类型
        cfg = get_config_manager(config_path=config_file, watch=False, test_mode=True)
        
        # 验证引号包围的false保留为字符串
        assert cfg.disabled == "false"
        assert isinstance(cfg.disabled, str)
        
        assert cfg.name == "test_app"
        assert isinstance(cfg.name, str)
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


def test_tc0015_001_006_nested_structure_string_preservation():
    """测试嵌套结构中的引号字符串被正确保留（按用户要求：加引号的就是字符串）"""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_file = os.path.join(tmpdir, 'test_config.yaml')
        
        # 创建包含嵌套结构的配置文件
        config_data = {
            '__data__': {
                'database': {
                    'host': "localhost",  # 正常字符串
                    'port': "5432",       # 引号包围：应该保留为字符串
                    'timeout': 30         # 正常数字
                },
                'name': "test_app"        # 正常字符串
            },
            '__type_hints__': {}
        }
        
        with open(config_file, 'w', encoding='utf-8') as f:
            yaml.dump(config_data, f)
        
        # 加载配置，应该成功且保留字符串类型
        cfg = get_config_manager(config_path=config_file, watch=False, test_mode=True)
        
        # 验证嵌套结构中的引号包围值保留为字符串
        assert cfg.database.host == "localhost"
        assert isinstance(cfg.database.host, str)
        
        assert cfg.database.port == "5432"  # 引号包围的数字保留为字符串
        assert isinstance(cfg.database.port, str)
        
        assert cfg.database.timeout == 30  # 正常数字保持为数字
        assert isinstance(cfg.database.timeout, int)
        
        assert cfg.name == "test_app"
        assert isinstance(cfg.name, str)
    pass


def test_tc0015_001_007_list_structure_string_preservation():
    """测试列表结构中的引号字符串被正确保留（按用户要求：加引号的就是字符串）"""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_file = os.path.join(tmpdir, 'test_config.yaml')
        
        # 创建包含列表结构的配置文件
        config_data = {
            '__data__': {
                'ports': [8080, "8081", 8082],  # 混合类型：数字和引号包围的字符串
                'name': "test_app"              # 正常字符串
            },
            '__type_hints__': {}
        }
        
        with open(config_file, 'w', encoding='utf-8') as f:
            yaml.dump(config_data, f)
        
        # 加载配置，应该成功且保留各自的类型
        cfg = get_config_manager(config_path=config_file, watch=False, test_mode=True)
        
        # 验证列表中的类型
        assert cfg.ports[0] == 8080  # 正常数字保持为数字
        assert isinstance(cfg.ports[0], int)
        
        assert cfg.ports[1] == "8081"  # 引号包围的数字保留为字符串
        assert isinstance(cfg.ports[1], str)
        
        assert cfg.ports[2] == 8082  # 正常数字保持为数字
        assert isinstance(cfg.ports[2], int)
        
        assert cfg.name == "test_app"
        assert isinstance(cfg.name, str)
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