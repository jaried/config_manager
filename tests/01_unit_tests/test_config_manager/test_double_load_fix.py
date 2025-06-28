# tests/01_unit_tests/test_config_manager/test_double_load_fix.py
from __future__ import annotations
from datetime import datetime

import tempfile
import os
import sys
import time
from ruamel.yaml import YAML
import pytest
from unittest.mock import patch, MagicMock

# 添加src到路径
# 项目根目录由conftest.py自动配置

from src.config_manager.config_manager import get_config_manager, _clear_instances_for_testing


def create_mock_yaml_file(config_path, data):
    """创建模拟的YAML文件"""
    os.makedirs(os.path.dirname(config_path), exist_ok=True)
    yaml = YAML()
    with open(config_path, 'w', encoding='utf-8') as f:
        yaml.dump(data, f)



class TestDoubleLoadFix:
    """测试配置重复加载修复"""

    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """在每个测试前后清理单例"""
        _clear_instances_for_testing()
        yield
        _clear_instances_for_testing()
            
    def test_external_modification_reloads_on_access(self, tmp_path):
        """
        测试当文件在外部被修改时，下一次访问配置是否能触发重新加载并获取新值。
        """
        config_file = tmp_path / "config.yaml"
        
        # 1. Arrange: 创建初始配置文件
        initial_data = {"setting": "initial_value"}
        create_mock_yaml_file(config_file, initial_data)
        
        # 2. Act: 获取配置管理器并验证初始值
        cfg = get_config_manager(str(config_file), watch=False) # 关闭watch以手动控制重载
        assert cfg.setting == "initial_value"
        
        # 3. Arrange: 在外部修改配置文件
        modified_data = {"setting": "modified_value"}
        # 模拟文件时间戳变化
        time.sleep(0.1)
        create_mock_yaml_file(config_file, modified_data)

        # 4. Act & Assert: 再次访问时应自动重新加载
        assert cfg.setting == "modified_value"

    def test_internal_modification_and_save(self, tmp_path):
        """
        测试内部修改配置后，是否能正确保存，并且外部修改能覆盖内部修改。
        """
        config_file = tmp_path / "config.yaml"
        
        # 1. Arrange: 创建初始配置文件
        initial_data = {"setting": "initial_value"}
        create_mock_yaml_file(config_file, initial_data)

        # 2. Act: 获取配置并进行内部修改
        cfg = get_config_manager(str(config_file), autosave_delay=0.1)
        cfg.setting = "internal_change"
        assert cfg.setting == "internal_change"
        
        # 3. Act: 等待自动保存
        time.sleep(0.3)

        # 4. Assert: 验证文件内容是否已更新
        yaml = YAML()
        with open(config_file, 'r', encoding='utf-8') as f:
            content = yaml.load(f)
        # to_dict() 会包含内部元数据，所以我们只检查业务数据
        assert content['__data__']['setting'] == 'internal_change'

    def test_reload_after_internal_and_external_changes(self, tmp_path):
        """
        测试在内部修改后，外部的修改是否仍然能够被正确加载。
        """
        config_file = tmp_path / "config.yaml"
        
        # 1. Arrange: 初始状态
        create_mock_yaml_file(config_file, {"setting": "initial"})
        cfg = get_config_manager(str(config_file), watch=False)
        assert cfg.setting == "initial"
        
        # 2. Act: 内部修改
        cfg.setting = "internal_change"
        assert cfg.setting == "internal_change"
        
        # 3. Arrange: 外部修改
        time.sleep(0.1)
        create_mock_yaml_file(config_file, {"setting": "external_final"})
        
        # 4. Act & Assert: 再次访问，应加载外部的最终修改
        assert cfg.setting == "external_final"