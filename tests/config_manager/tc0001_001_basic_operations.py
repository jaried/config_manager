# tests/config_manager/tc0001_001_basic_operations.py
from __future__ import annotations
from datetime import datetime

start_time = datetime.now()

import pytest
import tempfile
import os
from src.config_manager.config_manager import get_config_manager


def test_tc0001_001_001_get_set_operations():
    """测试基本设置和获取操作"""
    with tempfile.NamedTemporaryFile(suffix='.yaml') as tmpfile:
        cfg = get_config_manager(config_path=tmpfile.name)

        # 设置并获取简单值
        cfg.app_name = "TestApp"
        app_name = cfg.app_name
        assert app_name == "TestApp"

        # 设置并获取嵌套值
        cfg.database = {}
        cfg.database.host = "localhost"
        host = cfg.database.host
        assert host == "localhost"
    return


def test_tc0001_001_002_attribute_error():
    """测试访问不存在的属性"""
    with tempfile.NamedTemporaryFile(suffix='.yaml') as tmpfile:
        cfg = get_config_manager(config_path=tmpfile.name)

        # 访问不存在的属性
        with pytest.raises(AttributeError):
            value = cfg.non_existent_property
    return


def test_tc0001_001_003_update_operations():
    """测试批量更新操作"""
    with tempfile.NamedTemporaryFile(suffix='.yaml') as tmpfile:
        cfg = get_config_manager(config_path=tmpfile.name)

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
    with tempfile.NamedTemporaryFile(suffix='.yaml') as tmpfile:
        cfg = get_config_manager(config_path=tmpfile.name)

        # 设置配置值
        cfg.persistence_test = "save_me"

        # 重新加载配置
        reloaded = cfg.reload()
        assert reloaded

        # 验证值仍然存在
        value = cfg.persistence_test
        assert value == "save_me"
    return


def test_tc0001_001_005_config_id_generation():
    """测试配置ID生成"""
    with tempfile.NamedTemporaryFile(suffix='.yaml') as tmpfile:
        cfg = get_config_manager(config_path=tmpfile.name)

        id1 = cfg.generate_config_id()
        id2 = cfg.generate_config_id()

        assert isinstance(id1, str)
        assert isinstance(id2, str)
        assert len(id1) == 36
        assert id1 != id2
    return