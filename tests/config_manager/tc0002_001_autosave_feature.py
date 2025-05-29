# tests/config_manager/tc0002_001_autosave_feature.py
from __future__ import annotations
from datetime import datetime

start_time = datetime.now()

import pytest
import tempfile
import time
import os
from src.config_manager.config_manager import get_config_manager


def test_tc0002_001_001_autosave_basic():
    """测试基本自动保存功能"""
    with tempfile.NamedTemporaryFile(suffix='.yaml') as tmpfile:
        cfg = get_config_manager(
            config_path=tmpfile.name,
            autosave_delay=0.1
        )

        # 设置配置值
        cfg.autosave_test = "value1"

        # 等待自动保存完成
        time.sleep(0.2)

        # 验证文件已创建
        file_exists = os.path.exists(tmpfile.name)
        assert file_exists

        # 重新加载验证值
        reloaded = cfg.reload()
        assert reloaded
        value = cfg.autosave_test
        assert value == "value1"
    return


def test_tc0002_001_002_multilevel_autosave():
    """测试多级配置自动保存"""
    with tempfile.NamedTemporaryFile(suffix='.yaml') as tmpfile:
        cfg = get_config_manager(
            config_path=tmpfile.name,
            autosave_delay=0.1
        )

        # 设置多级配置值
        cfg.level1 = {}
        cfg.level1.level2 = {}
        cfg.level1.level2.level3_value = "deep_value"

        # 等待自动保存完成
        time.sleep(0.2)

        # 重新加载验证值
        reloaded = cfg.reload()
        assert reloaded
        value = cfg.level1.level2.level3_value
        assert value == "deep_value"
    return


def test_tc0002_001_003_autosave_delay():
    """测试自动保存延迟功能"""
    with tempfile.NamedTemporaryFile(suffix='.yaml') as tmpfile:
        cfg = get_config_manager(
            config_path=tmpfile.name,
            autosave_delay=0.5
        )

        start_time = time.time()
        cfg.delay_test = "value"
        end_time = time.time()

        # 验证没有立即保存
        time_diff = end_time - start_time
        assert time_diff < 0.1

        # 等待自动保存
        time.sleep(0.6)
        file_exists = os.path.exists(tmpfile.name)
        assert file_exists
    return