# tests/01_unit_tests/test_config_manager/test_tc0012_001_test_mode_simple.py
from __future__ import annotations

import os
import tempfile
import pytest
from src.config_manager import get_config_manager, TestEnvironmentManager
from src.config_manager.config_manager import _clear_instances_for_testing


class TestTestModeSimple:
    """测试test_mode功能的简化版本"""

    def setup_method(self):
        """每个测试方法前的设置"""
        _clear_instances_for_testing()
        # 清理测试环境变量
        if 'CONFIG_MANAGER_TEST_MODE' in os.environ:
            del os.environ['CONFIG_MANAGER_TEST_MODE']
        if 'CONFIG_MANAGER_TEST_BASE_DIR' in os.environ:
            del os.environ['CONFIG_MANAGER_TEST_BASE_DIR']

    def teardown_method(self):
        """每个测试方法后的清理"""
        # 清理当前测试环境
        TestEnvironmentManager.cleanup_current_test_environment()
        _clear_instances_for_testing()

    def test_test_mode_basic_isolation(self):
        """测试test_mode基本隔离功能，确保不污染生产配置文件"""
        # 记录生产配置文件的修改时间
        prod_config_path = "/mnt/ntfs/ubuntu_data/NutstoreFiles/invest2025/project/config_manager/src/config/config.yaml"
        if os.path.exists(prod_config_path):
            original_mtime = os.path.getmtime(prod_config_path)
        else:
            original_mtime = None
        
        # 创建测试模式配置
        test_cfg = get_config_manager(test_mode=True)
        test_cfg.test_isolation = "test_value"
        test_cfg.save()
        
        # 获取测试配置路径
        test_path = test_cfg.get_config_file_path()
        
        # 验证测试模式路径特征
        assert 'tmp' in test_path.lower() or 'temp' in test_path.lower(), "测试配置应该在临时目录"
        assert 'tests' in test_path, "测试配置应该在tests目录结构中"
        
        # 验证测试配置数据正确保存
        assert test_cfg.get('test_isolation') == "test_value"
        
        # 验证测试配置从生产配置正确复制了基础数据
        assert test_cfg.get('project_name') == 'test_project', "应该从生产配置复制了project_name"
        assert test_cfg.get('first_start_time') is not None, "应该从生产配置复制了first_start_time"
        
        # 验证测试环境变量
        assert os.environ.get('CONFIG_MANAGER_TEST_MODE') == 'true', "应该设置了测试模式环境变量"
        assert 'CONFIG_MANAGER_TEST_BASE_DIR' in os.environ, "应该设置了测试基础目录环境变量"
        
        # 验证生产配置文件没有被修改
        if original_mtime is not None:
            current_mtime = os.path.getmtime(prod_config_path)
            assert current_mtime == original_mtime, f"生产配置文件不应该被修改，原始时间: {original_mtime}, 当前时间: {current_mtime}"
        
        print(f"✓ 测试配置路径: {test_path}")
        print(f"✓ 测试模式环境变量: CONFIG_MANAGER_TEST_MODE={os.environ.get('CONFIG_MANAGER_TEST_MODE')}")
        print(f"✓ 测试基础目录: {os.environ.get('CONFIG_MANAGER_TEST_BASE_DIR')}")
        print(f"✓ 生产配置文件未被污染")