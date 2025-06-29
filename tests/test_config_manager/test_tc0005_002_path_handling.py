# tests/config_manager/tc0005_002_path_handling.py
from __future__ import annotations
from datetime import datetime

start_time = datetime.now()

import pytest
import tempfile
import os
import time
from src.config_manager.config_manager import get_config_manager, _clear_instances_for_testing


@pytest.fixture(autouse=True)
def cleanup_instances():
    """每个测试后清理实例"""
    yield
    _clear_instances_for_testing()
    return


def test_tc0005_002_001_explicit_path_handling():
    """测试明确指定路径的处理"""
    with tempfile.TemporaryDirectory() as tmpdir:
        # 明确指定配置文件路径在临时目录中
        config_file = os.path.join(tmpdir, 'config', 'config.yaml')
        
        # 创建配置管理器，明确指定路径
        cfg = get_config_manager(config_path=config_file, watch=False, auto_create=True, autosave_delay=0.1, test_mode=True)
        
        # 设置测试值
        cfg.explicit_test = "explicit_value"
        
        # 等待自动保存
        time.sleep(0.2)
        
        # 获取配置文件路径
        config_path = cfg.get_config_path()
        
        # 验证路径应该在临时目录中
        assert os.path.exists(config_path)
        assert config_path.endswith('.yaml')
        assert tmpdir in config_path or config_path.startswith(tmpdir)
        assert config_path == config_file
        
        # 验证配置值
        assert cfg.explicit_test == "explicit_value"
        
        # 重新加载配置
        reloaded = cfg.reload()
        assert reloaded
        
        # 再次验证配置值
        assert cfg.explicit_test == "explicit_value"
    return


def test_tc0005_002_002_project_structure_path():
    """测试项目结构路径处理"""
    with tempfile.TemporaryDirectory() as tmpdir:
        # 明确指定配置文件路径在临时目录的src/config中
        config_file = os.path.join(tmpdir, 'src', 'config', 'config.yaml')
        
        # 创建配置管理器，明确指定路径
        cfg = get_config_manager(config_path=config_file, watch=False, auto_create=True, autosave_delay=0.1, test_mode=True)
        
        # 设置测试值
        cfg.project_test = "project_value"
        
        # 等待自动保存
        time.sleep(0.2)
        
        # 获取配置文件路径
        config_path = cfg.get_config_path()
        
        # 验证路径应该在临时目录的src/config中
        assert os.path.exists(config_path)
        assert config_path.endswith('.yaml')
        assert tmpdir in config_path or config_path.startswith(tmpdir)
        assert 'src/config' in config_path or 'src\\config' in config_path
        assert config_path == config_file
        
        # 验证配置值
        assert cfg.project_test == "project_value"
        
        # 重新加载配置
        reloaded = cfg.reload()
        assert reloaded
        
        # 再次验证配置值
        assert cfg.project_test == "project_value"
    return


def test_tc0005_002_003_backup_creation():
    """测试备份文件创建"""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_file = os.path.join(tmpdir, 'test_config.yaml')
        
        # 创建配置管理器
        cfg = get_config_manager(config_path=config_file, watch=False, auto_create=True, autosave_delay=0.1, test_mode=True)
        
        # 设置测试值
        cfg.backup_creation_test = "backup_value"
        
        # 等待自动保存
        time.sleep(0.2)
        
        # 验证原始配置文件存在
        assert os.path.exists(config_file)
        assert cfg.get_config_path() == config_file
        
        # 验证备份文件也被创建
        config_dir = os.path.dirname(config_file)
        backup_dir = os.path.join(config_dir, 'backup')
        assert os.path.exists(backup_dir)
        
        # 验证配置值
        assert cfg.backup_creation_test == "backup_value"
        
        # 修改值并再次保存
        cfg.backup_creation_test = "modified_backup_value"
        time.sleep(0.2)
        
        # 验证原始配置文件被更新
        assert cfg.backup_creation_test == "modified_backup_value"
        
        # 验证配置路径始终是原始路径
        assert cfg.get_config_path() == config_file
    return 

# 注释：cursor.ai现在可以正常修改Python文件了！PowerShell + UTF-8编码解决了问题 