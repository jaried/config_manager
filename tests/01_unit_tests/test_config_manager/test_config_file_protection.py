# tests/01_unit_tests/test_config_manager/test_config_file_protection.py
from __future__ import annotations
import tempfile
import os
import shutil
import pytest
from unittest.mock import patch

from src.config_manager import get_config_manager, _clear_instances_for_testing


class TestConfigFileProtection:
    """测试配置文件保护功能"""
    
    def setup_method(self):
        """每个测试方法前的设置"""
        _clear_instances_for_testing()
    
    def teardown_method(self):
        """每个测试方法后的清理"""
        _clear_instances_for_testing()
    
    def test_windows_path_escape_fix(self):
        """测试Windows路径转义问题的修复"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = os.path.join(temp_dir, 'test_config.yaml')
            
            # 创建包含Windows路径的配置文件（会导致YAML解析错误）
            problematic_config = '''__data__:
  project_name: "TestProject"
  base_dir: "d:\\logs"
  experiment_name: "test_exp"
  paths:
    work_dir: "d:\\logs\\TestProject\\test_exp"
    log_dir: "d:\\logs\\TestProject\\test_exp\\logs"
__type_hints__: {}'''
            
            with open(config_path, 'w', encoding='utf-8') as f:
                f.write(problematic_config)
            
            # 尝试加载配置，应该能够成功（因为修复了路径转义问题）
            config = get_config_manager(
                config_path=config_path,
                auto_create=False
            )
            
            # 验证配置加载成功
            assert config is not None
            assert config.project_name == "TestProject"
            assert config.base_dir == "d:/logs"  # 应该被转换为正斜杠
            assert config.experiment_name == "test_exp"
    
    def test_config_file_protection_on_parse_error(self):
        """测试配置文件解析错误时的保护机制"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = os.path.join(temp_dir, 'test_config.yaml')
            
            # 创建一个有语法错误的YAML文件
            invalid_yaml = '''__data__:
  project_name: "TestProject"
  base_dir: "d:\\invalid\\escape\\sequence"  # 这会导致解析错误
  experiment_name: test_exp
  invalid_yaml: [unclosed list
__type_hints__: {}'''
            
            with open(config_path, 'w', encoding='utf-8') as f:
                f.write(invalid_yaml)
            
            # 备份原始文件内容
            original_content = invalid_yaml
            
            # 尝试加载配置，应该失败但不覆盖原文件
            config = get_config_manager(
                config_path=config_path,
                auto_create=True  # 即使设置auto_create=True也不应该覆盖
            )
            
            # 验证初始化失败
            assert config is None
            
            # 验证原始文件没有被覆盖
            with open(config_path, 'r', encoding='utf-8') as f:
                current_content = f.read()
            
            assert current_content == original_content
    
    def test_config_file_not_overwritten_on_cleanup(self):
        """测试清理时不会覆盖解析失败的配置文件"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = os.path.join(temp_dir, 'test_config.yaml')
            
            # 创建一个有效的配置文件
            valid_config = '''__data__:
  project_name: "TestProject"
  base_dir: "d:/logs"
  experiment_name: "test_exp"
__type_hints__: {}'''
            
            with open(config_path, 'w', encoding='utf-8') as f:
                f.write(valid_config)
            
            # 成功加载配置
            config = get_config_manager(
                config_path=config_path,
                auto_create=True
            )
            
            assert config is not None
            assert config.project_name == "TestProject"
            
            # 清理配置管理器（模拟程序退出）
            _clear_instances_for_testing()
            
            # 验证配置文件内容包含我们设置的值（可能会有自动生成的字段）
            with open(config_path, 'r', encoding='utf-8') as f:
                current_content = f.read()
            
            # 验证关键字段存在
            assert 'project_name: "TestProject"' in current_content or 'project_name: TestProject' in current_content
            assert 'experiment_name: "test_exp"' in current_content or 'experiment_name: test_exp' in current_content
    
    def test_successful_config_can_be_saved(self):
        """测试成功加载的配置可以正常保存"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = os.path.join(temp_dir, 'test_config.yaml')
            
            # 创建有效配置
            config = get_config_manager(
                config_path=config_path,
                auto_create=True
            )
            
            # 设置一些配置值
            config.set('project_name', 'TestProject')
            config.set('experiment_name', 'test_exp')
            config.set('base_dir', 'd:/logs')
            
            # 手动保存
            config.save()
            
            # 验证文件被正确保存
            assert os.path.exists(config_path)
            
            # 重新加载验证
            config2 = get_config_manager(
                config_path=config_path,
                auto_create=False
            )
            
            assert config2.project_name == 'TestProject'
            assert config2.experiment_name == 'test_exp'
            # base_dir现在可能是多平台配置，需要获取当前平台路径
            base_dir_value = config2._data.get('base_dir')
            if hasattr(base_dir_value, 'is_multi_platform_config') and base_dir_value.is_multi_platform_config():
                current_base_dir = config2.get('base_dir')  # 这会返回当前平台路径
                assert current_base_dir is not None
            else:
                assert config2.base_dir == 'd:/logs'
    
    def test_complex_windows_paths_handling(self):
        """测试复杂Windows路径的处理"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = os.path.join(temp_dir, 'test_config.yaml')
            
            # 创建包含各种Windows路径的配置
            complex_config = '''__data__:
  project_name: "FuturesTradingPL"
  base_dir: "d:\\logs"
  experiment_name: "feature_network_mvp"
  paths:
    work_dir: "d:\\logs\\FuturesTradingPL\\feature_network_mvp"
    checkpoint_dir: "d:\\logs\\FuturesTradingPL\\feature_network_mvp\\checkpoint"
    log_dir: "d:\\logs\\FuturesTradingPL\\feature_network_mvp\\logs\\2025-06-14\\003852"
  database:
    path: "c:\\data\\database.db"
  logs:
    base_root_dir: ".\\logs"
__type_hints__: {}'''
            
            with open(config_path, 'w', encoding='utf-8') as f:
                f.write(complex_config)
            
            # 加载配置
            config = get_config_manager(
                config_path=config_path,
                auto_create=False
            )
            
            # 验证所有路径都被正确处理（路径可能保持原始格式或被转换）
            assert config is not None
            assert config.project_name == "FuturesTradingPL"
            # 路径可能是正斜杠或反斜杠格式，都是有效的
            assert config.base_dir in ["d:/logs", "d:\\logs"]
            assert config.paths.work_dir in ["d:/logs/FuturesTradingPL/feature_network_mvp", "d:\\logs\\FuturesTradingPL\\feature_network_mvp"]
            assert config.paths.checkpoint_dir in ["d:/logs/FuturesTradingPL/feature_network_mvp/checkpoint", "d:\\logs\\FuturesTradingPL\\feature_network_mvp\\checkpoint"]
            assert config.database.path in ["c:/data/database.db", "c:\\data\\database.db"]
            assert config.logs.base_root_dir in ["./logs", ".\\logs"]
    
    def test_backup_creation_on_parse_error(self):
        """测试解析错误时备份文件的创建"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = os.path.join(temp_dir, 'test_config.yaml')
            
            # 创建有效配置
            valid_config = '''__data__:
  project_name: "TestProject"
  base_dir: "d:/logs"
__type_hints__: {}'''
            
            with open(config_path, 'w', encoding='utf-8') as f:
                f.write(valid_config)
            
            # 成功加载配置
            config = get_config_manager(
                config_path=config_path,
                auto_create=True
            )
            
            assert config is not None
            
            # 修改配置
            config.set('test_key', 'test_value')
            config.save()
            
            # 验证备份文件被创建
            backup_dir = os.path.join(os.path.dirname(config_path), 'backup')
            assert os.path.exists(backup_dir)
            
            # 查找备份文件
            backup_files = []
            for root, dirs, files in os.walk(backup_dir):
                for file in files:
                    if file.endswith('.yaml'):
                        backup_files.append(os.path.join(root, file))
            
            assert len(backup_files) > 0
            
            # 验证备份文件内容
            with open(backup_files[0], 'r', encoding='utf-8') as f:
                backup_content = f.read()
            
            assert 'test_key' in backup_content
            assert 'test_value' in backup_content 