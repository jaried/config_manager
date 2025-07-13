# tests/01_unit_tests/test_config_manager/test_tc0014_001_single_save_mechanism.py
from __future__ import annotations
from datetime import datetime

import tempfile
import os
import pytest
import time
from pathlib import Path
from src.config_manager import get_config_manager
from src.config_manager.config_manager import _clear_instances_for_testing


class TestTC0014001SingleSaveMechanism:
    """测试单次保存机制"""

    def setup_method(self):
        """每个测试方法前的设置"""
        _clear_instances_for_testing()

    def teardown_method(self):
        """每个测试方法后的清理"""
        _clear_instances_for_testing()

    def test_tc0014_001_001_initialization_single_backup(self):
        """TC0014-001-001: 测试初始化期间只创建一个备份文件"""
        
        # 创建临时配置文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("""project_name: "single_save_test"
experiment_name: "save_test"
base_dir: "/tmp/single_save_test"
learning_rate: 0.001
model:
  layers: 3
  dropout: 0.5
""")
            temp_config_path = f.name
        
        try:
            print(f"临时配置文件: {temp_config_path}")
            
            # 获取配置管理器
            config = get_config_manager(
                config_path=temp_config_path,
                test_mode=True,
                watch=False,
                auto_create=True
            )
            
            # 检查备份文件数量
            backup_dir = Path(config.paths.backup_dir)
            assert backup_dir.exists(), f"备份目录应该存在: {backup_dir}"
            
            backup_files = list(backup_dir.glob("*.yaml"))
            print(f"备份文件: {[str(f) for f in backup_files]}")
            
            # 应该只有一个备份文件
            assert len(backup_files) == 1, f"应该只有1个备份文件，实际有{len(backup_files)}个"
            
            print("✓ 初始化期间只创建了一个备份文件")
            
        finally:
            # 清理临时文件
            try:
                os.unlink(temp_config_path)
            except:
                pass

    def test_tc0014_001_002_post_initialization_autosave_works(self):
        """TC0014-001-002: 测试初始化完成后自动保存机制正常工作"""
        
        # 创建临时配置文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("""project_name: "autosave_test"
experiment_name: "post_init_test"
base_dir: "/tmp/autosave_test"
""")
            temp_config_path = f.name
        
        try:
            # 获取配置管理器
            config = get_config_manager(
                config_path=temp_config_path,
                test_mode=True,
                watch=False,
                auto_create=True,
                autosave_delay=0.1  # 很短的自动保存延迟
            )
            
            # 确认初始化完成
            assert hasattr(config, '_during_initialization')
            assert not config._during_initialization, "初始化应该已经完成"
            
            # 在初始化完成后设置一个新值
            config.set('post_init_test_value', 'test_value')
            
            # 等待自动保存
            time.sleep(0.2)
            
            # 直接检查配置文件内容来验证值是否被保存
            import yaml
            actual_config_path = config.get_config_file_path()
            
            with open(actual_config_path, 'r') as f:
                saved_config = yaml.safe_load(f)
            
            # 验证值被正确保存到__data__节点中
            if '__data__' in saved_config:
                saved_data = saved_config['__data__']
            else:
                saved_data = saved_config
                
            assert 'post_init_test_value' in saved_data, f"值应该被保存到配置文件中，当前配置: {saved_data}"
            assert saved_data['post_init_test_value'] == 'test_value', "保存的值应该正确"
            
            print("✓ 初始化完成后自动保存机制正常工作")
            
        finally:
            # 清理临时文件
            try:
                os.unlink(temp_config_path)
            except:
                pass

    def test_tc0014_001_003_initialization_saves_all_changes(self):
        """TC0014-001-003: 测试初始化期间的所有更改都被保存"""
        
        # 创建临时配置文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("""project_name: "init_save_test"
experiment_name: "save_all_test"
base_dir: "/tmp/init_save_test"
""")
            temp_config_path = f.name
        
        try:
            # 获取配置管理器
            config = get_config_manager(
                config_path=temp_config_path,
                test_mode=True,
                watch=False,
                auto_create=True
            )
            
            # 创建新的配置管理器实例来验证所有初始化期间的更改都被保存
            _clear_instances_for_testing()
            config2 = get_config_manager(
                config_path=temp_config_path,
                test_mode=True,
                watch=False,
                auto_create=True
            )
            
            # 验证关键字段都存在
            assert config2.get('first_start_time') is not None, "first_start_time应该被保存"
            assert config2.get('config_file_path') is not None, "config_file_path应该被保存"
            assert hasattr(config2, 'paths'), "paths应该被设置"
            assert config2.paths.work_dir is not None, "work_dir路径应该被保存"
            
            print("✓ 初始化期间的所有更改都被正确保存")
            
        finally:
            # 清理临时文件
            try:
                os.unlink(temp_config_path)
            except:
                pass

    def test_tc0014_001_004_backup_timing_correct(self):
        """TC0014-001-004: 测试备份创建时机正确（在paths目录创建后）"""
        
        # 创建临时配置文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("""project_name: "timing_test"
experiment_name: "backup_timing"
base_dir: "/tmp/timing_test"
""")
            temp_config_path = f.name
        
        try:
            # 获取配置管理器
            config = get_config_manager(
                config_path=temp_config_path,
                test_mode=True,
                watch=False,
                auto_create=True
            )
            
            # 验证paths目录存在
            assert hasattr(config, 'paths'), "paths应该存在"
            backup_dir = Path(config.paths.backup_dir)
            assert backup_dir.exists(), f"备份目录应该存在: {backup_dir}"
            
            # 验证备份文件存在且包含paths信息
            backup_files = list(backup_dir.glob("*.yaml"))
            assert len(backup_files) >= 1, "应该至少有一个备份文件"
            
            # 读取备份文件内容，验证包含paths信息
            with open(backup_files[0], 'r') as f:
                backup_content = f.read()
            
            assert 'paths:' in backup_content, "备份文件应该包含paths配置"
            assert 'work_dir:' in backup_content, "备份文件应该包含work_dir配置"
            
            print("✓ 备份创建时机正确，包含完整的paths信息")
            
        finally:
            # 清理临时文件
            try:
                os.unlink(temp_config_path)
            except:
                pass