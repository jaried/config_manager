# tests/config_manager/tc0001_002_type_hint_support.py
from __future__ import annotations
from datetime import datetime

start_time = datetime.now()

import pytest
import tempfile
import time
import os
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


def test_tc0001_002_001_type_hint_support():
    """测试类型提示支持"""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_file = os.path.join(tmpdir, 'test_config.yaml')
        cfg = get_config_manager(config_path=config_file, watch=False, test_mode=True)

        # 测试基本类型
        cfg.string_value = "test"
        cfg.int_value = 42
        cfg.float_value = 3.14
        cfg.bool_value = True
        cfg.list_value = [1, 2, 3]
        cfg.dict_value = {"key": "value"}

        assert cfg.string_value == "test"
        assert cfg.int_value == 42
        assert cfg.float_value == 3.14
        assert cfg.bool_value is True
        assert cfg.list_value == [1, 2, 3]
        assert cfg.dict_value == {"key": "value"}
    return


def test_tc0001_002_002_nested_type_hint_support():
    """测试嵌套类型提示支持"""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_file = os.path.join(tmpdir, 'test_config.yaml')
        cfg = get_config_manager(config_path=config_file, watch=False, test_mode=True)

        # 测试嵌套结构
        cfg.database = {}
        cfg.database.host = "localhost"
        cfg.database.port = 5432
        cfg.database.credentials = {}
        cfg.database.credentials.username = "admin"
        cfg.database.credentials.password = "secret"

        assert cfg.database.host == "localhost"
        assert cfg.database.port == 5432
        assert cfg.database.credentials.username == "admin"
        assert cfg.database.credentials.password == "secret"
    return


def test_tc0001_002_003_complex_type_hint_support():
    """测试复杂类型提示支持"""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_file = os.path.join(tmpdir, 'test_config.yaml')
        cfg = get_config_manager(config_path=config_file, watch=False, test_mode=True)

        # 测试复杂嵌套结构
        cfg.application = {}
        cfg.application.features = {}
        cfg.application.features.feature_a = {}
        cfg.application.features.feature_a.enabled = True
        cfg.application.features.feature_a.settings = {}
        cfg.application.features.feature_a.settings.timeout = 30
        cfg.application.features.feature_a.settings.retries = [1, 2, 3]

        assert cfg.application.features.feature_a.enabled is True
        assert cfg.application.features.feature_a.settings.timeout == 30
        assert cfg.application.features.feature_a.settings.retries == [1, 2, 3]
    return