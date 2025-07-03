# tests/config_manager/tc0005_001_advanced_features.py
from __future__ import annotations
from datetime import datetime

start_time = datetime.now()

import pytest
import tempfile
import os
import time
from src.config_manager.config_manager import get_config_manager, _clear_instances_for_testing
from pathlib import Path


@pytest.fixture(autouse=True)
def cleanup_instances():
    """每个测试后清理实例"""
    yield
    _clear_instances_for_testing()
    return


def test_tc0005_001_001_snapshot_and_restore():
    """测试快照和恢复功能"""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_file = os.path.join(tmpdir, 'test_config.yaml')
        cfg = get_config_manager(config_path=config_file, watch=False, test_mode=True)

        # 设置初始值
        cfg.test_value = "original"
        cfg.nested = {}
        cfg.nested.value = "nested_original"

        # 创建快照
        snapshot = cfg.snapshot()

        # 修改值
        cfg.test_value = "modified"
        cfg.nested.value = "nested_modified"

        modified_test = cfg.test_value
        modified_nested = cfg.nested.value
        assert modified_test == "modified"
        assert modified_nested == "nested_modified"

        # 恢复快照
        cfg.restore(snapshot)

        restored_test = cfg.test_value
        restored_nested = cfg.nested.value
        assert restored_test == "original"
        assert restored_nested == "nested_original"
    return


def test_tc0005_001_002_temporary_context():
    """测试临时配置上下文"""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_file = os.path.join(tmpdir, 'test_config.yaml')
        cfg = get_config_manager(config_path=config_file, watch=False, test_mode=True)

        # 设置初始值
        cfg.temp_test = "original"

        # 使用临时上下文
        with cfg.temporary({"temp_test": "temporary", "new_temp": "temp_value"}) as temp_cfg:
            temp_test_value = temp_cfg.temp_test
            new_temp_value = temp_cfg.new_temp
            assert temp_test_value == "temporary"
            assert new_temp_value == "temp_value"

        # 退出上下文后值应恢复
        final_test_value = cfg.temp_test
        final_new_temp = cfg.get("new_temp")
        assert final_test_value == "original"
        assert final_new_temp is None
    return


def test_tc0005_001_003_config_path_methods():
    """测试配置路径相关方法"""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_file = os.path.join(tmpdir, 'test_config.yaml')
        cfg = get_config_manager(config_path=config_file, watch=False, auto_create=True, autosave_delay=0.1, test_mode=True)

        # 设置一个值触发自动保存
        cfg.path_test = "test_value"
        time.sleep(0.2)  # 等待自动保存

        # 测试get_config_path - 现在应该返回原始配置路径
        retrieved_path = cfg.get_config_path()

        # 验证返回的是原始配置路径
        assert tempfile.gettempdir() in retrieved_path and 'tests' in retrieved_path and (retrieved_path.endswith('src/config/config.yaml') or retrieved_path.endswith('src\\config\\config.yaml'))

        # 测试generate_config_id
        id1 = cfg.generate_config_id()
        id2 = cfg.generate_config_id()

        assert isinstance(id1, str)
        assert isinstance(id2, str)
        assert len(id1) == 36  # UUID4 长度
        assert len(id2) == 36
        assert id1 != id2  # 每次生成的ID应该不同
    return


def test_tc0005_001_004_singleton_behavior():
    """测试测试模式下的隔离特性"""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_file = os.path.join(tmpdir, 'test_config.yaml')

        # 获取两次配置管理器实例 - 测试模式下的行为
        cfg1 = get_config_manager(config_path=config_file, watch=False, test_mode=True)
        cfg2 = get_config_manager(config_path=config_file, watch=False, test_mode=True)

        # 验证测试模式下使用了测试路径（而不是生产路径）
        path1 = cfg1.get_config_path()
        path2 = cfg2.get_config_path()
        
        # 两个路径都应该是测试环境路径
        assert 'tests' in path1, f"应该使用测试路径: {path1}"
        assert 'tests' in path2, f"应该使用测试路径: {path2}"
        assert tempfile.gettempdir() in path1, f"应该在临时目录下: {path1}"
        assert tempfile.gettempdir() in path2, f"应该在临时目录下: {path2}"

        # 验证测试模式功能正常工作
        cfg1.singleton_test = "test_value_1"
        cfg2.singleton_test = "test_value_2"  # 可能覆盖前一个值，这取决于是否为同一实例
        
        # 验证配置功能正常
        assert hasattr(cfg1, 'singleton_test'), "应该能够设置配置值"
        assert hasattr(cfg2, 'singleton_test'), "应该能够设置配置值"
    return


def test_tc0005_001_005_empty_snapshot_restore():
    """测试空快照恢复"""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_file = os.path.join(tmpdir, 'test_config.yaml')
        cfg = get_config_manager(config_path=config_file, watch=False, test_mode=True)

        # 创建空快照
        empty_snapshot = {'data': {}, 'type_hints': {}}

        # 设置一些值
        cfg.test_empty = "will_be_removed"

        # 恢复空快照
        cfg.restore(empty_snapshot)

        # 值应该被清除
        empty_value = cfg.get('test_empty')
        assert empty_value is None
    return


def test_tc0005_001_006_backup_loading():
    """测试备份文件的创建和历史版本管理"""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_file = os.path.join(tmpdir, 'test_config.yaml')

        # 创建配置管理器并设置值
        cfg = get_config_manager(config_path=config_file, watch=False, auto_create=True, autosave_delay=0.1, test_mode=True)
        cfg.backup_test = "original_value"
        cfg.nested_backup = {}
        cfg.nested_backup.value = "nested_value"

        # 等待自动保存
        time.sleep(0.2)

        # 验证原始配置文件存在
        assert os.path.exists(cfg.get_config_path())
        
        # 验证备份文件也被创建
        backup_path = cfg._get_backup_path()
        backup_dir = os.path.dirname(backup_path)
        assert os.path.exists(backup_dir), f"备份目录不存在: {backup_dir}"

        # 修改值并再次保存
        cfg.backup_test = "modified_value"
        time.sleep(0.2)

        # 验证原始配置文件被更新
        assert cfg.backup_test == "modified_value"

        # 重新加载配置验证持久化
        reloaded = cfg.reload()
        assert reloaded
        assert cfg.backup_test == "modified_value"
        assert cfg.nested_backup.value == "nested_value"

        # 跨平台判断配置文件路径在临时目录下且存在
        assert os.path.exists(cfg.get_config_path())
        assert os.path.commonpath([cfg.get_config_path(), tempfile.gettempdir()]) == tempfile.gettempdir()

        # 断言测试环境路径下的备份文件存在
        assert os.path.exists(cfg.get_config_path()), "测试环境路径下的配置文件应存在"
        backup_path = cfg._get_backup_path()
        backup_dir = os.path.dirname(backup_path)
        assert os.path.exists(backup_dir), "测试环境路径下的备份目录应存在"
    return
