# tests/01_unit_tests/test_config_manager/test_tc0012_004_backup_isolation.py
from __future__ import annotations
from datetime import datetime
import os
import tempfile
import pytest
from unittest.mock import patch, MagicMock
from src.config_manager import get_config_manager, _clear_instances_for_testing



class TestTC0012004BackupIsolation:
    """测试test_mode下的备份隔离功能"""

    def setup_method(self):
        """每个测试前的设置"""
        _clear_instances_for_testing()

    def teardown_method(self):
        """每个测试后的清理"""
        _clear_instances_for_testing()

    def test_tc0012_004_001_backup_path_isolation(self):
        """测试生产环境和测试环境的备份路径隔离"""
        fixed_time = datetime(2025, 1, 7, 10, 0, 0)
        
        # 生产环境配置管理器
        prod_cfg = get_config_manager(first_start_time=fixed_time)
        prod_backup_path = prod_cfg._get_backup_path()
        
        # 测试环境配置管理器
        test_cfg = get_config_manager(test_mode=True, first_start_time=fixed_time)
        test_backup_path = test_cfg._get_backup_path()
        
        # 验证备份路径完全不同
        assert prod_backup_path != test_backup_path
        
        # 验证生产环境备份路径不包含临时目录标识
        assert "temp" not in prod_backup_path.lower()
        assert "tests" not in prod_backup_path
        
        # 验证测试环境备份路径包含临时目录标识
        assert "temp" in test_backup_path.lower() or "tests" in test_backup_path
        
        # 验证两个路径都包含正确的时间戳
        assert "20250107" in prod_backup_path
        assert "100000" in prod_backup_path
        assert "20250107" in test_backup_path
        assert "100000" in test_backup_path
        
        print(f"生产环境备份路径: {prod_backup_path}")
        print(f"测试环境备份路径: {test_backup_path}")

    def test_tc0012_004_002_backup_file_creation_isolation(self):
        """测试备份文件创建的隔离性"""
        fixed_time = datetime(2025, 1, 7, 10, 0, 0)
        
        # 生产环境：设置配置并触发备份
        prod_cfg = get_config_manager(first_start_time=fixed_time, autosave_delay=0.1)
        prod_cfg.test_backup_isolation = "production_value"
        
        # 测试环境：设置配置并触发备份
        test_cfg = get_config_manager(test_mode=True, first_start_time=fixed_time, autosave_delay=0.1)
        test_cfg.test_backup_isolation = "test_value"
        
        # 等待自动保存和备份
        import time
        time.sleep(0.3)
        
        # 获取备份路径
        prod_backup_path = prod_cfg._get_backup_path()
        test_backup_path = test_cfg._get_backup_path()
        
        # 验证备份文件都存在
        assert os.path.exists(prod_backup_path), f"生产环境备份文件不存在: {prod_backup_path}"
        assert os.path.exists(test_backup_path), f"测试环境备份文件不存在: {test_backup_path}"
        
        # 验证备份文件内容不同
        with open(prod_backup_path, 'r', encoding='utf-8') as f:
            prod_content = f.read()
        
        with open(test_backup_path, 'r', encoding='utf-8') as f:
            test_content = f.read()
        
        assert "production_value" in prod_content
        assert "test_value" in test_content
        assert prod_content != test_content

    def test_tc0012_004_003_backup_directory_structure(self):
        """测试备份目录结构的正确性"""
        fixed_time = datetime(2025, 1, 7, 10, 0, 0)
        
        # 测试环境配置管理器
        test_cfg = get_config_manager(test_mode=True, first_start_time=fixed_time, autosave_delay=0.1)
        test_cfg.directory_structure_test = "test_value"
        
        # 等待自动保存
        import time
        time.sleep(0.3)
        
        # 获取备份路径
        backup_path = test_cfg._get_backup_path()
        
        # 验证备份文件存在
        assert os.path.exists(backup_path)
        
        # 验证目录结构
        # 新的期望结构：{temp}/tests/20250107/100000/test_project/experiment_name/backup/20250107/100000/config_20250107_100000.yaml
        path_parts = backup_path.replace('\\', '/').split('/')
        
        # 查找关键目录
        assert 'tests' in path_parts
        assert '20250107' in path_parts
        assert '100000' in path_parts
        assert 'test_project' in path_parts
        assert 'experiment_name' in path_parts
        assert 'backup' in path_parts
        
        # 验证文件名格式
        filename = os.path.basename(backup_path)
        assert filename == 'config_20250107_100000.yaml'

    def test_tc0012_004_004_multiple_test_instances_backup_isolation(self):
        """测试多个测试实例的备份隔离"""
        time1 = datetime(2025, 1, 7, 10, 0, 0)
        time2 = datetime(2025, 1, 7, 11, 0, 0)
        
        # 创建两个不同时间的测试实例
        test_cfg1 = get_config_manager(test_mode=True, first_start_time=time1, autosave_delay=0.1)
        test_cfg2 = get_config_manager(test_mode=True, first_start_time=time2, autosave_delay=0.1)
        
        # 设置不同的配置值
        test_cfg1.multi_instance_test = "instance1_value"
        test_cfg2.multi_instance_test = "instance2_value"
        
        # 等待自动保存
        import time
        time.sleep(0.3)
        
        # 获取备份路径
        backup_path1 = test_cfg1._get_backup_path()
        backup_path2 = test_cfg2._get_backup_path()
        
        # 验证备份路径不同
        assert backup_path1 != backup_path2
        
        # 验证时间戳不同
        assert "100000" in backup_path1  # 10:00:00
        assert "110000" in backup_path2  # 11:00:00
        
        # 验证备份文件都存在
        assert os.path.exists(backup_path1)
        assert os.path.exists(backup_path2)
        
        # 验证备份内容不同
        with open(backup_path1, 'r', encoding='utf-8') as f:
            content1 = f.read()
        
        with open(backup_path2, 'r', encoding='utf-8') as f:
            content2 = f.read()
        
        assert "instance1_value" in content1
        assert "instance2_value" in content2
        assert content1 != content2

    def test_tc0012_004_005_backup_path_generation_consistency(self):
        """测试备份路径生成的一致性"""
        fixed_time = datetime(2025, 1, 7, 10, 0, 0)
        
        # 创建测试环境配置管理器
        test_cfg = get_config_manager(test_mode=True, first_start_time=fixed_time)
        
        # 多次获取备份路径，应该保持一致
        backup_path1 = test_cfg._get_backup_path()
        backup_path2 = test_cfg._get_backup_path()
        backup_path3 = test_cfg._get_backup_path()
        
        # 验证路径一致性
        assert backup_path1 == backup_path2 == backup_path3
        
        # 验证路径格式正确
        assert backup_path1.endswith('config_20250107_100000.yaml')
        assert '20250107' in backup_path1
        assert '100000' in backup_path1

    @patch('src.config_manager.config_manager.PathResolver._find_project_root')
    @patch('os.path.exists')
    def test_tc0012_004_006_backup_with_custom_config_path(self, mock_exists, mock_find_root):
        """测试自定义配置路径下的备份隔离"""
        # 设置Mock
        mock_find_root.return_value = '/mock/project'
        mock_exists.return_value = False  # 模拟配置文件不存在，会创建空配置
        
        fixed_time = datetime(2025, 1, 7, 10, 0, 0)
        
        # 使用自定义配置路径的测试模式
        with patch('builtins.open'), \
             patch('ruamel.yaml.YAML') as mock_yaml_class, \
             patch('os.makedirs'), \
             patch('shutil.copy2'):
            
            # 设置YAML Mock
            mock_yaml = MagicMock()
            mock_yaml_class.return_value = mock_yaml
            mock_yaml.load.return_value = {'__data__': {}}
            
            test_cfg = get_config_manager(
                config_path="/custom/path/config.yaml",
                test_mode=True,
                first_start_time=fixed_time
            )
            
            backup_path = test_cfg._get_backup_path()
            
            # 验证备份路径基于测试环境路径生成
            assert "temp" in backup_path.lower() or "tests" in backup_path
            assert "20250107" in backup_path
            assert "100000" in backup_path
            assert backup_path.endswith('config_20250107_100000.yaml')
            
            # 验证不包含原始自定义路径
            assert "/custom/path/" not in backup_path 