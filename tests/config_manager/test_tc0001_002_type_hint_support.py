# tests/config_manager/tc0002_001_autosave_feature.py
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


def test_tc0002_001_001_autosave_basic():
    """测试基本自动保存功能"""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_file = os.path.join(tmpdir, 'test_config.yaml')
        cfg = get_config_manager(
            config_path=config_file,
            autosave_delay=0.1,
            watch=False
        )

        cfg.autosave_test = "value1"

        # 等待自动保存
        time.sleep(0.2)

        # 验证备份文件存在（现在文件保存到备份路径）
        backup_path = cfg._get_backup_path()
        file_exists = os.path.exists(backup_path)
        assert file_exists

        reloaded = cfg.reload()
        assert reloaded

        # 使用 get 方法而不是直接属性访问，更稳定
        value = cfg.get('autosave_test')
        if value is None:
            # 如果 get 失败，尝试直接从 _data 获取
            value = cfg._data.get('autosave_test')

        assert value == "value1"
    return


def test_tc0002_001_002_multilevel_autosave():
    """测试多级配置自动保存"""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_file = os.path.join(tmpdir, 'test_config.yaml')
        cfg = get_config_manager(
            config_path=config_file,
            autosave_delay=0.1,
            watch=False
        )

        cfg.level1 = {}
        cfg.level1.level2 = {}
        cfg.level1.level2.level3_value = "deep_value"

        # 等待自动保存
        time.sleep(0.2)

        reloaded = cfg.reload()
        assert reloaded

        # 使用get方法获取嵌套值
        value = cfg.get("level1.level2.level3_value")
        assert value == "deep_value"
    return


def test_tc0002_001_003_autosave_delay():
    """测试自动保存延迟功能"""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_file = os.path.join(tmpdir, 'test_config.yaml')
        cfg = get_config_manager(
            config_path=config_file,
            autosave_delay=0.5,
            watch=False
        )

        start_time_val = time.time()
        cfg.delay_test = "value"
        end_time_val = time.time()

        time_diff = end_time_val - start_time_val
        assert time_diff < 0.1

        # 等待自动保存
        time.sleep(0.6)

        # 验证备份文件存在（现在文件保存到备份路径）
        backup_path = cfg._get_backup_path()
        file_exists = os.path.exists(backup_path)
        assert file_exists
    return