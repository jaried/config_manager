# src/tools/call_chain_demo.py
from __future__ import annotations
from datetime import datetime

start_time = datetime.now()

import tempfile
import os
import sys
import time
import threading
import asyncio

# 添加src到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from config_manager.config_manager import get_config_manager, _clear_instances_for_testing


def level_3_function():
    """第三层函数，模拟深层调用"""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_file = os.path.join(tmpdir, 'demo_call_chain.yaml')

        print("=== 演示配置创建时的完整调用链 ===")
        cfg = get_config_manager(
            config_path=config_file,
            watch=False,
            autosave_delay=0.2
        )

        print("\n=== 演示配置设置和自动保存的完整调用链 ===")
        cfg.demo_value = "演示调用链"
        cfg.nested = {}
        cfg.nested.deep_value = "深层值"

        # 等待自动保存
        print("等待自动保存...")
        time.sleep(0.5)

        print("\n=== 演示配置重新加载的完整调用链 ===")
        cfg.reload()

        print("\n=== 演示手动保存的完整调用链 ===")
        cfg.manual_save_demo = "手动保存演示"
        cfg.save()

    return


def level_2_function():
    """第二层函数"""
    level_3_function()
    return


def level_1_function():
    """第一层函数"""
    level_2_function()
    return


def thread_worker():
    """线程工作函数"""
    print("\n=== 线程中的配置操作演示 ===")
    with tempfile.TemporaryDirectory() as tmpdir:
        config_file = os.path.join(tmpdir, 'thread_demo.yaml')
        cfg = get_config_manager(
            config_path=config_file,
            watch=False,
            autosave_delay=0.2
        )
        cfg.thread_demo = "线程演示"
        time.sleep(0.3)
    return


async def async_worker():
    """异步工作函数"""
    print("\n=== 异步函数中的配置操作演示 ===")
    with tempfile.TemporaryDirectory() as tmpdir:
        config_file = os.path.join(tmpdir, 'async_demo.yaml')
        cfg = get_config_manager(
            config_path=config_file,
            watch=False,
            autosave_delay=0.2
        )
        cfg.async_demo = "异步演示"
        await asyncio.sleep(0.3)
    return


def demo_threading():
    """演示线程中的调用链"""
    print("\n" + "=" * 50)
    print("演示线程调用链")
    print("=" * 50)

    thread = threading.Thread(target=thread_worker, name="ConfigDemoThread")
    thread.start()
    thread.join()
    return


async def demo_async():
    """演示异步调用链"""
    print("\n" + "=" * 50)
    print("演示异步调用链")
    print("=" * 50)

    await async_worker()
    return


def main():
    """主函数"""
    print("配置管理器完整调用链演示工具")
    print("=" * 60)
    print("此工具演示配置管理器在不同环境下的完整调用链信息")
    print("包括：进程ID、线程信息、异步信息、完整调用栈")
    print("=" * 60)

    try:
        # 清理之前的实例
        _clear_instances_for_testing()

        # 演示普通多层调用
        print("=== 演示普通多层调用链 ===")
        level_1_function()

        # 演示线程调用
        demo_threading()

        # 演示异步调用
        asyncio.run(demo_async())

        print("\n" + "=" * 60)
        print("调用链演示完成")
        print("\n调用链信息说明：")
        print("格式：[P:进程ID|T:线程名(线程ID)标志|A:异步信息] 调用链...")
        print("标志：M=主线程，D=守护线程")
        print("类型：[user]=用户代码，[3rd]=第三方库，[std]=标准库，[async]=异步库，[thread]=线程库")
        print("内容：模块名@[类型]文件路径:函数名():行号")

    except Exception as e:
        print(f"演示失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        _clear_instances_for_testing()
    return


if __name__ == "__main__":
    main()