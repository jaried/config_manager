# src/tools/debug_autosave.py
from __future__ import annotations
from datetime import datetime

start_time = datetime.now()

import tempfile
import os
import sys
import time
import yaml
import threading

# 添加src到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from config_manager.config_manager import get_config_manager, _clear_instances_for_testing


def debug_autosave_detailed():
    """详细调试自动保存问题"""
    print("详细调试自动保存问题")
    print("=" * 30)

    with tempfile.TemporaryDirectory() as tmpdir:
        config_file = os.path.join(tmpdir, 'debug_autosave.yaml')

        try:
            # 清理实例
            _clear_instances_for_testing()

            # 创建配置管理器，启用自动保存
            cfg = get_config_manager(
                config_path=config_file,
                watch=False,
                autosave_delay=0.1
            )
            print("✓ 配置管理器创建成功（自动保存延迟0.1秒）")

            # 检查初始状态
            print(f"初始 _data 状态: {cfg._data}")
            print(f"初始 to_dict() 结果: {cfg.to_dict()}")

            # 设置值
            print("\n设置值...")
            cfg.debug_test = "debug_value"
            print(f"设置后 _data: {cfg._data}")
            print(f"设置后 to_dict(): {cfg.to_dict()}")
            print(f"设置后访问值: {cfg.debug_test}")

            # 立即手动保存测试
            print("\n手动保存测试...")
            manual_save = cfg.save()
            print(f"手动保存结果: {manual_save}")

            if os.path.exists(config_file):
                with open(config_file, 'r', encoding='utf-8') as f:
                    manual_content = yaml.safe_load(f)
                print(f"手动保存内容: {manual_content}")

            # 删除文件，重新测试自动保存
            if os.path.exists(config_file):
                os.remove(config_file)
                print("删除文件，重新测试自动保存")

            # 重新设置值触发自动保存
            print("\n触发自动保存...")
            cfg.auto_test = "auto_value"
            print(f"触发自动保存后 _data: {cfg._data}")
            print(f"触发自动保存后 to_dict(): {cfg.to_dict()}")

            # 检查自动保存调度
            print(f"自动保存定时器状态: {cfg._autosave_timer}")
            print(f"自动保存锁状态: {cfg._autosave_lock}")

            # 等待自动保存
            print("等待自动保存（0.2秒）...")
            time.sleep(0.2)

            print(f"等待后自动保存定时器状态: {cfg._autosave_timer}")

            # 检查文件
            file_exists = os.path.exists(config_file)
            print(f"自动保存后文件存在: {file_exists}")

            if file_exists:
                with open(config_file, 'r', encoding='utf-8') as f:
                    auto_content = yaml.safe_load(f)
                print(f"自动保存内容: {auto_content}")

            # 测试线程安全
            print("\n测试线程安全...")

            def set_values_in_thread():
                cfg.thread_test = "thread_value"
                print(f"线程中设置后 _data: {cfg._data}")
                return

            thread = threading.Thread(target=set_values_in_thread)
            thread.start()
            thread.join()

            time.sleep(0.2)  # 等待可能的自动保存

            print(f"线程测试后 _data: {cfg._data}")

        except Exception as e:
            print(f"❌ 调试失败: {e}")
            import traceback
            traceback.print_exc()
        finally:
            _clear_instances_for_testing()
    return


if __name__ == "__main__":
    debug_autosave_detailed()