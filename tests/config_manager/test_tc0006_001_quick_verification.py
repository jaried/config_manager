# tests/config_manager/tc0006_001_quick_verification.py
from __future__ import annotations
from datetime import datetime

start_time = datetime.now()

import pytest
import tempfile
import os
from src.config_manager.config_manager import get_config_manager, _clear_instances_for_testing


@pytest.fixture(autouse=True)
def cleanup_instances():
    """每个测试后清理实例"""
    yield
    _clear_instances_for_testing()
    return


def test_tc0006_001_001_basic_functionality():
    """快速验证基本功能"""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_file = os.path.join(tmpdir, 'test_config.yaml')

        # 创建配置管理器
        cfg = get_config_manager(config_path=config_file, watch=False)

        # 测试基本设置
        cfg.app_name = "TestApp"
        app_name = cfg.app_name
        assert app_name == "TestApp"

        # 测试字典设置
        cfg.database = {}
        cfg.database.host = "localhost"

        database_host = cfg.database.host
        assert database_host == "localhost"

        # 测试保存
        saved = cfg.save()
        assert saved

        # 测试重新加载
        reloaded = cfg.reload()
        assert reloaded

        # 验证数据仍然存在
        reloaded_app_name = cfg.app_name
        reloaded_host = cfg.database.host
        assert reloaded_app_name == "TestApp"
        assert reloaded_host == "localhost"
    return


def test_tc0006_001_002_nested_dict_assignment():
    """测试嵌套字典赋值"""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_file = os.path.join(tmpdir, 'test_config.yaml')
        cfg = get_config_manager(config_path=config_file, watch=False)

        # 测试多层嵌套字典
        cfg.level1 = {}
        cfg.level1.level2 = {}
        cfg.level1.level2.value = "deep_value"

        deep_value = cfg.level1.level2.value
        assert deep_value == "deep_value"

        # 保存并重新加载
        cfg.save()
        cfg.reload()

        # 验证嵌套结构保持完整
        reloaded_value = cfg.level1.level2.value
        assert reloaded_value == "deep_value"
    return


def test_tc0006_001_003_update_with_dict():
    """测试使用字典更新"""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_file = os.path.join(tmpdir, 'test_config.yaml')
        cfg = get_config_manager(config_path=config_file, watch=False)

        # 使用update方法设置嵌套结构
        cfg.update({
            'server': {
                'host': 'localhost',
                'port': 8_080,
                'ssl': True
            }
        })

        server_host = cfg.server.host
        server_port = cfg.server.port
        server_ssl = cfg.server.ssl

        assert server_host == 'localhost'
        assert server_port == 8_080
        assert server_ssl is True
    return