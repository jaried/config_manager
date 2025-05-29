# tests/config_manager/tc0005_001_advanced_features.py
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


def test_tc0005_001_001_snapshot_and_restore():
    """测试快照和恢复功能"""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_file = os.path.join(tmpdir, 'test_config.yaml')
        cfg = get_config_manager(config_path=config_file, watch=False)

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
        cfg = get_config_manager(config_path=config_file, watch=False)

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
        cfg = get_config_manager(config_path=config_file, watch=False)

        # 测试get_config_path
        retrieved_path = cfg.get_config_path()
        assert retrieved_path == config_file

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
    """测试单例行为"""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_file = os.path.join(tmpdir, 'test_config.yaml')

        # 获取两次配置管理器实例
        cfg1 = get_config_manager(config_path=config_file, watch=False)
        cfg2 = get_config_manager(config_path=config_file, watch=False)

        # 应该是同一个实例
        assert cfg1 is cfg2

        # 在一个实例上设置值，另一个实例应该能看到
        cfg1.singleton_test = "test_value"
        singleton_value = cfg2.singleton_test
        assert singleton_value == "test_value"
    return


def test_tc0005_001_005_empty_snapshot_restore():
    """测试空快照恢复"""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_file = os.path.join(tmpdir, 'test_config.yaml')
        cfg = get_config_manager(config_path=config_file, watch=False)

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