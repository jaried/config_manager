# tests/config_manager/tc0003_001_concurrency_test.py
from __future__ import annotations
from datetime import datetime

start_time = datetime.now()

import pytest
import threading
import time
import tempfile
import os
from src.config_manager.config_manager import get_config_manager, _clear_instances_for_testing


@pytest.fixture(autouse=True)
def cleanup_instances():
    """每个测试后清理实例"""
    yield
    _clear_instances_for_testing()
    return


def test_tc0003_001_001_thread_safety():
    """测试多线程安全性"""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_file = os.path.join(tmpdir, 'test_config.yaml')
        cfg = get_config_manager(
            config_path=config_file,
            autosave_delay=0.1,
            watch=False
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

        for i in range(5):
            t = threading.Thread(target=worker, args=(i,))
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        time.sleep(0.2)

        for i in range(5):
            value = cfg.get(f"thread_{i}")
            assert value == f"value_{i}"
            assert f"value_{i}" in results
    return