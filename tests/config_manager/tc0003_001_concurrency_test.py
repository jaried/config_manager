# tests/config_manager/tc0003_001_concurrency_test.py
from __future__ import annotations
from datetime import datetime

start_time = datetime.now()

import pytest
import threading
import time
import tempfile
from src.config_manager.config_manager import get_config_manager


def test_tc0003_001_001_thread_safety():
    """测试多线程安全性"""
    with tempfile.NamedTemporaryFile(suffix='.yaml') as tmpfile:
        cfg = get_config_manager(
            config_path=tmpfile.name,
            autosave_delay=0.1
        )
        results = []
        threads = []

        def worker(thread_id):
            key = f"thread_{thread_id}"
            cfg.set(key, f"value_{thread_id}")
            time.sleep(0.05)
            value = cfg.get(key)
            results.append(value)
            return

        # 创建多个线程
        for i in range(5):
            t = threading.Thread(target=worker, args=(i,))
            threads.append(t)
            t.start()

        # 等待所有线程完成
        for t in threads:
            t.join()

        # 等待自动保存完成
        time.sleep(0.2)

        # 验证所有值
        for i in range(5):
            value = cfg.get(f"thread_{i}")
            assert value == f"value_{i}"
            assert f"value_{i}" in results
    return