# tests/01_unit_tests/test_config_manager/test_tc0011_001_raw_yaml_support.py
from __future__ import annotations
from datetime import datetime

import tempfile
import yaml
import os
import pytest
from config_manager import get_config_manager
from config_manager.config_manager import _clear_instances_for_testing


class TestRawYamlSupport:
    """测试原始YAML格式支持"""

    def setup_method(self):
        """每个测试方法前的设置"""
        _clear_instances_for_testing()

    def teardown_method(self):
        """每个测试方法后的清理"""
        _clear_instances_for_testing()

    def test_tc0011_001_001_raw_yaml_format_loading(self):
        """TC0011-001-001: 测试原始YAML格式配置文件加载"""
        # 创建原始格式的YAML配置文件
        raw_config = {
            'app_name': '测试应用',
            'version': '1.0.0',
            'database': {
                'host': 'localhost',
                'port': 5432,
                'name': 'testdb'
            },
            'features': ['feature1', 'feature2'],
            'test_flag': True,
            'timeout': 30
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False, encoding='utf-8') as f:
            yaml.dump(raw_config, f, allow_unicode=True)
            config_path = f.name

        try:
            # 加载配置
            config = get_config_manager(config_path=config_path, watch=False)

            # 验证所有配置项都被正确加载
            assert hasattr(config, 'app_name')
            assert hasattr(config, 'version')
            assert hasattr(config, 'database')
            assert hasattr(config, 'features')
            assert hasattr(config, 'test_flag')
            assert hasattr(config, 'timeout')

            # 验证配置值正确
            assert config.app_name == '测试应用'
            assert config.version == '1.0.0'
            assert config.database.host == 'localhost'
            assert config.database.port == 5432
            assert config.database.name == 'testdb'
            assert config.features == ['feature1', 'feature2']
            assert config.test_flag == True
            assert config.timeout == 30

        finally:
            os.unlink(config_path)

    def test_tc0011_001_002_standard_format_still_works(self):
        """TC0011-001-002: 测试标准格式配置文件仍然正常工作"""
        # 创建标准格式的YAML配置文件
        standard_config = {
            '__data__': {
                'app_name': '标准应用',
                'version': '2.0.0',
                'database': {
                    'host': 'production-db',
                    'port': 3306,
                    'name': 'proddb'
                },
                'features': ['prod_feature1', 'prod_feature2'],
                'test_flag': False,
                'timeout': 60
            },
            '__type_hints__': {
                'database.port': 'int',
                'timeout': 'int'
            }
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False, encoding='utf-8') as f:
            yaml.dump(standard_config, f, allow_unicode=True)
            config_path = f.name

        try:
            # 加载配置
            config = get_config_manager(config_path=config_path, watch=False)

            # 验证所有配置项都被正确加载
            assert hasattr(config, 'app_name')
            assert hasattr(config, 'version')
            assert hasattr(config, 'database')
            assert hasattr(config, 'features')
            assert hasattr(config, 'test_flag')
            assert hasattr(config, 'timeout')

            # 验证配置值正确
            assert config.app_name == '标准应用'
            assert config.version == '2.0.0'
            assert config.database.host == 'production-db'
            assert config.database.port == 3306
            assert config.database.name == 'proddb'
            assert config.features == ['prod_feature1', 'prod_feature2']
            assert config.test_flag == False
            assert config.timeout == 60

            # 验证类型提示被正确加载
            assert config.get_type_hint('database.port') == 'int'
            assert config.get_type_hint('timeout') == 'int'

        finally:
            os.unlink(config_path)

    def test_tc0011_001_003_raw_yaml_attribute_access(self):
        """TC0011-001-003: 测试原始YAML格式的各种属性访问方式"""
        raw_config = {
            'simple_key': 'simple_value',
            'nested': {
                'level1': {
                    'level2': 'deep_value'
                }
            },
            'list_data': [1, 2, 3, 4, 5],
            'mixed_list': ['string', 123, {'key': 'value'}]
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False, encoding='utf-8') as f:
            yaml.dump(raw_config, f, allow_unicode=True)
            config_path = f.name

        try:
            config = get_config_manager(config_path=config_path, watch=False)

            # 测试直接属性访问
            assert config.simple_key == 'simple_value'
            assert config.nested.level1.level2 == 'deep_value'
            assert config.list_data == [1, 2, 3, 4, 5]
            assert config.mixed_list == ['string', 123, {'key': 'value'}]

            # 测试 hasattr
            assert hasattr(config, 'simple_key')
            assert hasattr(config, 'nested')
            assert hasattr(config, 'list_data')
            assert hasattr(config, 'mixed_list')

            # 测试 getattr
            assert getattr(config, 'simple_key') == 'simple_value'
            assert getattr(config, 'nonexistent', 'default') == 'default'

            # 测试 get 方法
            assert config.get('simple_key') == 'simple_value'
            assert config.get('nested.level1.level2') == 'deep_value'
            assert config.get('nonexistent', 'default') == 'default'

        finally:
            os.unlink(config_path)

    def test_tc0011_001_004_raw_yaml_to_dict_conversion(self):
        """TC0011-001-004: 测试原始YAML格式的字典转换"""
        raw_config = {
            'key1': 'value1',
            'key2': {
                'nested_key': 'nested_value'
            },
            'key3': [1, 2, 3]
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False, encoding='utf-8') as f:
            yaml.dump(raw_config, f, allow_unicode=True)
            config_path = f.name

        try:
            config = get_config_manager(config_path=config_path, watch=False)

            # 转换为字典
            config_dict = config.to_dict()

            # 验证原始配置项都在字典中
            assert 'key1' in config_dict
            assert 'key2' in config_dict
            assert 'key3' in config_dict

            # 验证值正确
            assert config_dict['key1'] == 'value1'
            assert config_dict['key2']['nested_key'] == 'nested_value'
            assert config_dict['key3'] == [1, 2, 3]

            # 验证ConfigManager添加的内部键也存在
            assert 'first_start_time' in config_dict
            assert 'config_file_path' in config_dict

        finally:
            os.unlink(config_path)

    def test_tc0011_001_005_raw_yaml_modification_and_save(self):
        """TC0011-001-005: 测试原始YAML格式的修改和保存"""
        raw_config = {
            'original_key': 'original_value',
            'to_modify': 'old_value'
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False, encoding='utf-8') as f:
            yaml.dump(raw_config, f, allow_unicode=True)
            config_path = f.name

        try:
            config = get_config_manager(config_path=config_path, watch=False)

            # 验证原始值
            assert config.original_key == 'original_value'
            assert config.to_modify == 'old_value'

            # 修改配置
            config.to_modify = 'new_value'
            config.new_key = 'new_value'

            # 保存配置
            config.save()

            # 重新加载验证
            config2 = get_config_manager(config_path=config_path, watch=False)
            assert config2.original_key == 'original_value'
            assert config2.to_modify == 'new_value'
            assert config2.new_key == 'new_value'

        finally:
            os.unlink(config_path)

    def test_tc0011_001_006_raw_yaml_empty_file_handling(self):
        """TC0011-001-006: 测试原始YAML格式的空文件处理"""
        # 创建空的YAML文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False, encoding='utf-8') as f:
            f.write('')  # 空文件
            config_path = f.name

        try:
            config = get_config_manager(config_path=config_path, watch=False, auto_create=True)

            # 空文件应该能正常加载，只包含ConfigManager的内部键
            config_dict = config.to_dict()
            assert 'first_start_time' in config_dict
            assert 'config_file_path' in config_dict

            # 应该能正常添加配置
            config.test_key = 'test_value'
            assert config.test_key == 'test_value'

        finally:
            os.unlink(config_path)

    def test_tc0011_001_007_raw_yaml_with_internal_keys(self):
        """TC0011-001-007: 测试原始YAML格式包含内部键的处理"""
        # 创建包含内部键的原始格式配置
        raw_config = {
            'user_key': 'user_value',
            '__internal_key': 'should_be_ignored',  # 应该被忽略
            '__some_other_internal': 'should_be_ignored'  # 应该被忽略
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False, encoding='utf-8') as f:
            yaml.dump(raw_config, f, allow_unicode=True)
            config_path = f.name

        try:
            config = get_config_manager(config_path=config_path, watch=False)

            # 验证用户键被正确加载
            assert hasattr(config, 'user_key')
            assert config.user_key == 'user_value'

            # 验证内部键被忽略
            assert not hasattr(config, '__internal_key')
            assert not hasattr(config, '__some_other_internal')

            # 验证ConfigManager自己的内部键存在
            config_dict = config.to_dict()
            assert 'first_start_time' in config_dict
            assert 'config_file_path' in config_dict

        finally:
            os.unlink(config_path)

    def test_tc0011_001_008_raw_yaml_complex_nested_structure(self):
        """TC0011-001-008: 测试原始YAML格式的复杂嵌套结构"""
        complex_config = {
            'application': {
                'name': '复杂应用',
                'version': '3.0.0',
                'modules': {
                    'auth': {
                        'enabled': True,
                        'providers': ['local', 'oauth', 'ldap'],
                        'settings': {
                            'session_timeout': 3600,
                            'max_attempts': 3
                        }
                    },
                    'database': {
                        'primary': {
                            'host': 'primary-db',
                            'port': 5432,
                            'replicas': [
                                {'host': 'replica1', 'port': 5432},
                                {'host': 'replica2', 'port': 5432}
                            ]
                        }
                    }
                }
            },
            'environments': {
                'development': {'debug': True, 'log_level': 'DEBUG'},
                'production': {'debug': False, 'log_level': 'ERROR'}
            }
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False, encoding='utf-8') as f:
            yaml.dump(complex_config, f, allow_unicode=True)
            config_path = f.name

        try:
            config = get_config_manager(config_path=config_path, watch=False)

            # 验证深层嵌套访问
            assert config.application.name == '复杂应用'
            assert config.application.version == '3.0.0'
            assert config.application.modules.auth.enabled == True
            assert config.application.modules.auth.providers == ['local', 'oauth', 'ldap']
            assert config.application.modules.auth.settings.session_timeout == 3600
            assert config.application.modules.auth.settings.max_attempts == 3

            # 验证数组中的嵌套对象
            replicas = config.application.modules.database.primary.replicas
            assert len(replicas) == 2
            assert replicas[0]['host'] == 'replica1'
            assert replicas[1]['host'] == 'replica2'

            # 验证环境配置
            assert config.environments.development.debug == True
            assert config.environments.development.log_level == 'DEBUG'
            assert config.environments.production.debug == False
            assert config.environments.production.log_level == 'ERROR'

        finally:
            os.unlink(config_path) 