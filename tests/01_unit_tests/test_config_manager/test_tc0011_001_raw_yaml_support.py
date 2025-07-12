# tests/01_unit_tests/test_config_manager/test_tc0011_001_raw_yaml_support.py
from __future__ import annotations

import tempfile
import os
from ruamel.yaml import YAML
import pytest

# 移除硬编码的路径设置，因为它现在由 conftest.py 处理
# sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..')))

from src.config_manager.config_manager import get_config_manager, _clear_instances_for_testing


class TestRawYamlSupport:
    """测试原始YAML格式支持"""

    def setup_method(self):
        """每个测试方法前的设置"""
        _clear_instances_for_testing()
        self.yaml = YAML()
        self.temp_files = []

    def teardown_method(self):
        """每个测试方法后的清理"""
        _clear_instances_for_testing()
        for f in self.temp_files:
            try:
                os.unlink(f)
            except OSError:
                pass

    def _create_temp_yaml(self, data):
        """创建一个临时的YAML文件并返回路径"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False, encoding='utf-8') as f:
            self.yaml.dump(data, f)
            path = f.name
        self.temp_files.append(path)
        return path

    def test_tc0011_001_001_raw_yaml_format_loading(self):
        """TC0011-001-001: 测试原始YAML格式配置文件加载"""
        raw_config = {
            'app_name': '测试应用',
            'version': '1.0.0',
            'database': {'host': 'localhost', 'port': 5432, 'name': 'testdb'},
            'features': ['feature1', 'feature2'],
            'test_flag': True,
            'timeout': 30
        }
        config_path = self._create_temp_yaml(raw_config)
        config = get_config_manager(config_path=config_path, watch=False)

        assert config.app_name == '测试应用'
        assert config.database.port == 5432
        assert config.features == ['feature1', 'feature2']

    def test_tc0011_001_002_standard_format_still_works(self):
        """TC0011-001-002: 测试标准格式配置文件仍然正常工作"""
        standard_config = {
            '__data__': {
                'app_name': '标准应用',
                'version': '2.0.0',
            },
            '__type_hints__': {}
        }
        config_path = self._create_temp_yaml(standard_config)
        config = get_config_manager(config_path=config_path, watch=False)

        assert config.app_name == '标准应用'
        assert config.version == '2.0.0'

    def test_tc0011_001_003_raw_yaml_attribute_access(self):
        """TC0011-001-003: 测试原始YAML格式的各种属性访问方式"""
        raw_config = {
            'simple_key': 'simple_value',
            'nested': {'level1': {'level2': 'deep_value'}}
        }
        config_path = self._create_temp_yaml(raw_config)
        config = get_config_manager(config_path=config_path, watch=False)

        assert config.simple_key == 'simple_value'
        assert config.nested.level1.level2 == 'deep_value'
        assert config.get('nested.level1.level2') == 'deep_value'
        assert config.get('nonexistent', 'default') == 'default'

    def test_tc0011_001_004_raw_yaml_to_dict_conversion(self):
        """TC0011-001-004: 测试原始YAML格式的字典转换"""
        raw_config = {'key1': 'value1', 'key2': {'nested_key': 'nested_value'}}
        config_path = self._create_temp_yaml(raw_config)
        config = get_config_manager(config_path=config_path, watch=False)
        config_dict = config.to_dict()

        assert config_dict['key1'] == 'value1'
        assert config_dict['key2']['nested_key'] == 'nested_value'
        assert 'config_file_path' in config_dict

    def test_tc0011_001_005_raw_yaml_modification_and_save(self):
        """TC0011-001-005: 测试原始YAML格式的修改和保存"""
        raw_config = {'original_key': 'original_value', 'to_modify': 'old_value'}
        config_path = self._create_temp_yaml(raw_config)
        config = get_config_manager(config_path=config_path, watch=False)

        config.to_modify = 'new_value'
        config.new_key = 'new_value'
        config.save()

        # 重新加载验证
        _clear_instances_for_testing()
        config2 = get_config_manager(config_path=config_path, watch=False)
        assert config2.to_modify == 'new_value'
        assert config2.new_key == 'new_value'

    def test_tc0011_001_006_raw_yaml_empty_file_handling(self):
        """TC0011-001-006: 测试原始YAML格式的空文件处理"""
        config_path = self._create_temp_yaml('')
        config = get_config_manager(config_path=config_path, watch=False)
        assert config.to_dict() is not None
        
        # 使用set方法而不是直接属性赋值来避免ConfigManager特殊处理
        config.set('new_data', "test", autosave=False)
        assert config.get('new_data') == "test"

    def test_get_raw_yaml_content(self, tmp_path):
        """测试获取原始YAML文件内容"""
        config_path = tmp_path / "test.yaml"
        config_data = {'key': 'value', 'nested': {'key': 'nested_value'}}
        
        # 先创建配置文件
        with open(config_path, 'w', encoding='utf-8') as f:
            self.yaml.dump(config_data, f)
        
        cm = get_config_manager(str(config_path))
        
        raw_content = cm.get_raw_yaml_content()

        reread_data = self.yaml.load(raw_content)
        assert config_data == reread_data

    def test_get_raw_yaml_content_file_not_found(self):
        """测试当配置文件不存在时获取内容"""
        cm = get_config_manager("non_existent_file.yaml", auto_create=False)
        if cm is None:
            # 如果配置管理器创建失败，则测试通过
            return
        with pytest.raises(FileNotFoundError):
            cm.get_raw_yaml_content() 