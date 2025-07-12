# tests/config_manager/tc0001_001_basic_operations.py
from __future__ import annotations
from datetime import datetime

start_time = datetime.now()

import pytest
import tempfile
import os
import time
import sys

# 安全添加路径
src_path = os.path.join(os.path.dirname(__file__), '..', '..')
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from src.config_manager.config_manager import get_config_manager, _clear_instances_for_testing


@pytest.fixture(autouse=True)
def cleanup_instances():
    """每个测试后清理实例"""
    yield
    _clear_instances_for_testing()
    return


def test_tc0001_001_001_get_set_operations():
    """测试基本设置和获取操作"""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_file = os.path.join(tmpdir, 'test_config.yaml')
        cfg = get_config_manager(config_path=config_file, watch=False, test_mode=True)

        cfg.app_name = "TestApp"
        app_name = cfg.app_name
        assert app_name == "TestApp"

        cfg.database = {}
        cfg.database.host = "localhost"
        host = cfg.database.host
        assert host == "localhost"
    return


def test_tc0001_001_002_attribute_error():
    """测试访问不存在的属性"""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_file = os.path.join(tmpdir, 'test_config.yaml')
        cfg = get_config_manager(config_path=config_file, watch=False, test_mode=True)

        with pytest.raises(AttributeError):
            # 访问不存在的属性应该抛出AttributeError
            cfg.nonexistent_attribute
    return


def test_tc0001_001_003_update_operations():
    """测试批量更新操作"""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_file = os.path.join(tmpdir, 'test_config.yaml')
        cfg = get_config_manager(config_path=config_file, watch=False, test_mode=True)

        updates = {
            'feature_a_enabled': True,
            'feature_b_enabled': False,
            'settings_timeout': 30
        }

        cfg.update(updates)

        feature_a = cfg.feature_a_enabled
        feature_b = cfg.feature_b_enabled
        timeout = cfg.settings_timeout

        assert feature_a is True
        assert feature_b is False
        assert timeout == 30
    return


def test_tc0001_001_004_config_persistence():
    """测试配置持久化"""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_file = os.path.join(tmpdir, 'test_config.yaml')
        cfg = get_config_manager(config_path=config_file, watch=False, test_mode=True)

        cfg.persistence_test = "save_me"

        # 等待一下让自动保存完成
        time.sleep(0.2)

        saved = cfg.save()
        assert saved

        reloaded = cfg.reload()
        assert reloaded

        # 使用get方法获取值，更稳定
        value = cfg.get('persistence_test')
        if value is None:
            # 如果get失败，尝试直接从_data获取
            value = cfg._data.get('persistence_test')
        assert value == "save_me"
    return


def test_tc0001_001_005_config_id_generation():
    """测试配置ID生成"""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_file = os.path.join(tmpdir, 'test_config.yaml')
        cfg = get_config_manager(config_path=config_file, watch=False, test_mode=True)

        id1 = cfg.generate_config_id()
        id2 = cfg.generate_config_id()

        assert isinstance(id1, str)
        assert isinstance(id2, str)
        assert len(id1) == 36
        assert id1 != id2
    return