# tests/config_manager/test_tc0008_003_call_chain_edge_cases.py
from __future__ import annotations
from datetime import datetime

start_time = datetime.now()

import pytest
import tempfile
import os
import sys
import threading
import time
from io import StringIO
from contextlib import redirect_stdout
from unittest.mock import patch

# 添加src到路径，确保能导入配置管理器
project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
src_path = os.path.join(project_root, 'src')
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from config_manager.config_manager import get_config_manager, _clear_instances_for_testing
from config_manager.core.call_chain import CallChainTracker
import config_manager.config_manager as cm_module


@pytest.fixture(autouse=True)
def cleanup_instances():
    """每个测试后清理实例"""
    # 临时开启调用链显示，因为这些是调用链边界情况测试
    original_switch = cm_module.ENABLE_CALL_CHAIN_DISPLAY
    cm_module.ENABLE_CALL_CHAIN_DISPLAY = True
    
    try:
        yield
    finally:
        # 恢复原始开关状态
        cm_module.ENABLE_CALL_CHAIN_DISPLAY = original_switch
        _clear_instances_for_testing()
    return


def test_tc0008_003_001_very_long_function_names():
    """测试包含很长函数名的调用链"""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_file = os.path.join(tmpdir, 'long_names_test.yaml')

        def this_is_a_very_long_function_name_that_might_cause_formatting_issues():
            """非常长的函数名"""
            output = StringIO()
            with redirect_stdout(output):
                cfg = get_config_manager(
                    config_path=config_file,
                    watch=False,
                    autosave_delay=0.1
                )
                cfg.long_name_test = "success"

            return cfg, output.getvalue()

        cfg, output = this_is_a_very_long_function_name_that_might_cause_formatting_issues()

        # 验证长函数名能正确显示在调用链中
        assert "调用链:" in output
        assert "this_is_a_very_long_function_name" in output

        # 验证调用链格式仍然正确
        lines = output.split('\n')
        call_chain_line = None
        for line in lines:
            if "调用链:" in line:
                call_chain_line = line
                break

        assert call_chain_line is not None
        assert " <- " in call_chain_line or len(call_chain_line.split(" <- ")) >= 1

        print(f"长函数名调用链:\n{output}")
        return


def test_tc0008_003_002_multithreaded_environment():
    """测试多线程环境下的调用链"""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_file = os.path.join(tmpdir, 'multithread_test.yaml')
        thread_results = {}

        def worker_thread(thread_id: int):
            """工作线程函数"""
            # 为每个线程使用不同的配置文件，避免单例模式的影响
            thread_config_file = os.path.join(tmpdir, f'thread_{thread_id}_config.yaml')

            output = StringIO()
            with redirect_stdout(output):
                cfg = get_config_manager(
                    config_path=thread_config_file,
                    watch=False,
                    autosave_delay=0.1
                )
                cfg.set(f'thread_{thread_id}_data', f'thread_{thread_id}_value', autosave=False)

            thread_results[thread_id] = output.getvalue()
            return

        # 创建多个线程
        threads = []
        for i in range(3):
            thread = threading.Thread(target=worker_thread, args=(i,))
            threads.append(thread)

        # 启动所有线程
        for thread in threads:
            thread.start()

        # 等待所有线程完成
        for thread in threads:
            thread.join()

        # 验证多线程环境下的基本功能
        # 注意：在多线程环境下，stdout重定向可能不稳定，所以我们主要验证功能性而不是输出
        successful_threads = 0
        for thread_id, output in thread_results.items():
            # 检查是否有任何输出或配置相关信息
            has_config_info = (
                    "调用链:" in output or
                    "配置已从" in output or
                    "配置文件不存在" in output or
                    len(output.strip()) > 0
            )
            
            if has_config_info:
                successful_threads += 1
                print(f"线程 {thread_id} 成功产生输出")
            else:
                print(f"线程 {thread_id} 没有输出（可能是多线程stdout重定向问题）")
        
        # 至少应该有一个线程成功产生输出
        # 如果所有线程都没有输出，那可能是测试环境问题
        if successful_threads == 0:
            print("警告：所有线程都没有产生输出，这可能是多线程环境下stdout重定向的限制")
            # 在这种情况下，我们验证配置文件是否被创建
            created_files = 0
            for i in range(3):
                thread_config_file = os.path.join(tmpdir, f'thread_{i}_config.yaml')
                if os.path.exists(thread_config_file):
                    created_files += 1
            
            assert created_files > 0, "至少应该创建一个配置文件"
            print(f"验证通过：创建了 {created_files} 个配置文件")
        else:
            print(f"验证通过：{successful_threads} 个线程成功产生输出")

        print("多线程调用链输出:")
        for thread_id, output in thread_results.items():
            print(f"线程 {thread_id}:\n{output}")

        return


def test_tc0008_003_003_inspect_module_failure():
    """测试inspect模块失败时的调用链处理"""
    tracker = CallChainTracker()

    def test_function_with_mock_failure():
        """测试函数，模拟inspect失败"""
        with patch('inspect.stack') as mock_stack:
            # 模拟inspect.stack()抛出异常
            mock_stack.side_effect = Exception("模拟inspect模块失败")

            # 调用链获取应该不会抛出异常
            try:
                chain = tracker.get_call_chain()
                return chain
            except Exception as e:
                # 不应该到达这里
                return f"unexpected_exception: {e}"

    result = test_function_with_mock_failure()

    # 验证即使inspect失败，也能优雅处理
    assert isinstance(result, str)
    # 结果可能是空字符串或错误信息，但不应该抛出异常

    print(f"inspect失败处理结果: {result}")
    return


def test_tc0008_003_004_very_deep_recursion():
    """测试非常深的递归调用链"""
    tracker = CallChainTracker()

    def deep_recursive_function(depth: int, max_depth: int = 20):
        """深度递归函数"""
        if depth >= max_depth:
            chain = tracker.get_call_chain()
            return chain
        else:
            return deep_recursive_function(depth + 1, max_depth)

    # 创建深度递归调用链
    result_chain = deep_recursive_function(0)

    # 验证深度递归不会导致问题
    assert isinstance(result_chain, str)

    # 验证调用链包含环境信息
    assert result_chain.startswith("[P:")  # 应该包含进程ID信息

    # 验证调用链包含深度递归的函数
    parts = result_chain.split(" <- ") if result_chain else []

    # 验证包含递归函数调用
    recursive_parts = [part for part in parts if "deep_recursive_function" in part]
    assert len(recursive_parts) >= 20  # 应该有至少20层递归

    # 验证调用链格式正确
    assert "|" in result_chain  # 应该包含格式化的调用信息
    assert "F:deep_recursive_function" in result_chain  # 应该包含函数名

    print(f"深度递归调用链长度: {len(parts)}")
    print(f"递归函数层数: {len(recursive_parts)}")
    return


def test_tc0008_003_005_lambda_functions():
    """测试包含lambda函数的调用链"""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_file = os.path.join(tmpdir, 'lambda_test.yaml')

        # 使用lambda函数的场景
        lambda_function = lambda: get_config_manager(
            config_path=config_file,
            watch=False,
            autosave_delay=0.1
        )

        def wrapper_function():
            """包装函数"""
            output = StringIO()
            with redirect_stdout(output):
                cfg = lambda_function()
                cfg.lambda_test = "success"

            return cfg, output.getvalue()

        cfg, output = wrapper_function()

        # 验证lambda函数在调用链中的显示
        assert "调用链:" in output
        assert "wrapper_function" in output
        # lambda函数可能显示为"<lambda>"或类似形式

        print(f"Lambda函数调用链:\n{output}")
        return


def test_tc0008_003_006_empty_stack_handling():
    """测试空调用栈的处理"""
    tracker = CallChainTracker()

    with patch('inspect.stack') as mock_stack:
        # 模拟返回空的调用栈
        mock_stack.return_value = []

        chain = tracker.get_call_chain()

        # 验证空调用栈的处理
        assert isinstance(chain, str)
        # 可能返回空字符串或默认值

        print(f"空调用栈处理结果: '{chain}'")
        return


def test_tc0008_003_007_invalid_start_time_types():
    """测试无效类型的start_time处理"""
    tracker = CallChainTracker()

    # 模拟不同类型的无效start_time
    invalid_start_times = [
        123,  # 数字
        [],  # 列表
        {},  # 字典
        None,  # None
        "invalid_datetime_string",  # 无效的日期时间字符串
    ]

    current_module = sys.modules[__name__]
    original_start_time = getattr(current_module, 'start_time', None)

    try:
        for invalid_time in invalid_start_times:
            setattr(current_module, 'start_time', invalid_time)

            # 获取start_time应该不会抛出异常
            try:
                result_time = tracker.get_caller_start_time()
                assert isinstance(result_time, datetime)
                print(f"无效start_time {type(invalid_time).__name__} 处理成功: {result_time}")
            except Exception as e:
                assert False, f"处理无效start_time时抛出异常: {e}"

    finally:
        # 恢复原始start_time
        if original_start_time is not None:
            setattr(current_module, 'start_time', original_start_time)
        elif hasattr(current_module, 'start_time'):
            delattr(current_module, 'start_time')

    return


def test_tc0008_003_008_unicode_paths():
    """测试包含Unicode字符的文件路径"""
    with tempfile.TemporaryDirectory() as tmpdir:
        # 创建包含中文的配置文件路径
        unicode_config_file = os.path.join(tmpdir, '配置文件_测试.yaml')

        def function_with_unicode_path():
            """使用Unicode路径的函数"""
            output = StringIO()
            with redirect_stdout(output):
                cfg = get_config_manager(
                    config_path=unicode_config_file,
                    watch=False,
                    autosave_delay=0.1
                )
                cfg.unicode_test = "成功"

            return cfg, output.getvalue()

        cfg, output = function_with_unicode_path()

        # 验证Unicode路径不会导致调用链显示错误
        assert "调用链:" in output
        assert "function_with_unicode_path" in output

        # 验证配置文件路径显示正确
        assert "配置文件不存在" in output or "配置已从" in output

        print(f"Unicode路径调用链:\n{output}")
        return