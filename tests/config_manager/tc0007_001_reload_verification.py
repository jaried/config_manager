# tests/config_manager/tc0007_001_reload_verification.py
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


def test_tc0007_001_001_simple_reload():
    """测试简单重新加载"""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_file = os.path.join(tmpdir, 'test_config.yaml')
        cfg = get_config_manager(config_path=config_file, watch=False)

        # 设置值
        cfg.test_value = "hello"

        # 保存
        cfg.save()

        # 重新加载
        cfg.reload()

        # 验证值仍然存在
        reloaded_value = cfg.test_value
        assert reloaded_value == "hello"
    return


def test_tc0007_001_002_nested_reload():
    """测试嵌套结构重新加载"""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_file = os.path.join(tmpdir, 'test_config.yaml')
        cfg = get_config_manager(config_path=config_file, watch=False)

        # 设置嵌套结构
        cfg.level1 = {}
        cfg.level1.level2 = {}
        cfg.level1.level2.value = "nested_value"

        # 保存
        cfg.save()

        # 重新加载
        cfg.reload()

        # 验证嵌套值存在
        nested_value = cfg.level1.level2.value
        assert nested_value == "nested_value"

        # 使用get方法验证
        get_value = cfg.get("level1.level2.value")
        assert get_value == "nested_value"
    return


def test_tc0007_001_003_autosave_reload():
    """测试自动保存后重新加载"""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_file = os.path.join(tmpdir, 'test_config.yaml')
        cfg = get_config_manager(
            config_path=config_file,
            watch=False,
            autosave_delay=0.1
        )

        # 设置值并等待自动保存
        cfg.autosave_test = "auto_saved_value"
        time.sleep(0.2)  # 等待自动保存

        # 重新加载
        cfg.reload()

        # 验证自动保存的值存在 - 使用 get 方法
        auto_value = cfg.get('autosave_test')
        if auto_value is None:
            # 如果 get 失败，直接从 _data 检查
            auto_value = cfg._data.get('autosave_test')

        assert auto_value == "auto_saved_value"
    return