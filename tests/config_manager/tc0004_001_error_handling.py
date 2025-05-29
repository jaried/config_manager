# tests/config_manager/tc0004_001_error_handling.py
from __future__ import annotations
from datetime import datetime

start_time = datetime.now()

import pytest
import tempfile
from src.config_manager.config_manager import get_config_manager


def test_tc0004_001_001_invalid_key_access():
    """测试无效键访问"""
    with tempfile.NamedTemporaryFile(suffix='.yaml') as tmpfile:
        cfg = get_config_manager(config_path=tmpfile.name)

        # 访问不存在的键
        value = cfg.get("invalid_key")
        assert value is None

        # 使用默认值
        default_value = cfg.get("invalid_key", default="default")
        assert default_value == "default"
    return


def test_tc0004_001_002_file_permission_error(monkeypatch):
    """测试文件权限错误处理"""
    with tempfile.NamedTemporaryFile(suffix='.yaml') as tmpfile:
        cfg = get_config_manager(config_path=tmpfile.name)

        # 模拟保存时的权限错误
        def mock_save():
            raise PermissionError("模拟权限错误")

        monkeypatch.setattr(cfg, 'save', mock_save)

        # 捕获并验证错误
        with pytest.raises(PermissionError) as excinfo:
            cfg.set("test_permission", "value")

        error_msg = str(excinfo.value)
        assert "模拟权限错误" in error_msg
    return


def test_tc0004_001_003_edge_case_values():
    """测试边界值处理"""
    with tempfile.NamedTemporaryFile(suffix='.yaml') as tmpfile:
        cfg = get_config_manager(config_path=tmpfile.name)

        # 空值
        cfg.set("empty_value", None)
        value = cfg.get("empty_value")
        assert value is None

        # 大值
        large_value = 'A' * 1000000  # 1MB字符串
        cfg.set("large_value", large_value)
        saved_value = cfg.get("large_value")
        assert saved_value == large_value
    return