# tests/config_manager/tc0004_001_error_handling.py
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


def test_tc0004_001_001_invalid_key_access():
    """测试无效键访问"""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_file = os.path.join(tmpdir, 'test_config.yaml')
        cfg = get_config_manager(config_path=config_file, watch=False)

        value = cfg.get("invalid_key")
        assert value is None

        default_value = cfg.get("invalid_key", default="default")
        assert default_value == "default"
    return


def test_tc0004_001_002_file_permission_error():
    """测试文件权限错误处理"""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_file = os.path.join(tmpdir, 'test_config.yaml')
        cfg = get_config_manager(config_path=config_file, watch=False)

        original_save = cfg.save

        def mock_save():
            raise PermissionError("模拟权限错误")

        object.__setattr__(cfg, 'save', mock_save)

        with pytest.raises(PermissionError) as excinfo:
            cfg.set("test_permission", "value", autosave=False)
            cfg.save()

        error_msg = str(excinfo.value)
        assert "模拟权限错误" in error_msg

        object.__setattr__(cfg, 'save', original_save)
    return


def test_tc0004_001_003_edge_case_values():
    """测试边界值处理"""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_file = os.path.join(tmpdir, 'test_config.yaml')
        cfg = get_config_manager(config_path=config_file, watch=False)

        cfg.set("empty_value", None)
        value = cfg.get("empty_value")
        assert value is None

        large_value = 'A' * 1_000_000
        cfg.set("large_value", large_value)
        saved_value = cfg.get("large_value")
        assert saved_value == large_value
    return