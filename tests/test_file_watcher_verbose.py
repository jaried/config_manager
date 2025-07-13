# tests/test_file_watcher_verbose.py
from __future__ import annotations

import os
import tempfile
import time
import yaml
from config_manager import get_config_manager


def test_file_watcher_verbose():
    """详细测试文件监视器的工作状态"""
    
    with tempfile.TemporaryDirectory() as temp_dir:
        config_path = os.path.join(temp_dir, "test_config.yaml")
        
        # 创建初始配置文件
        initial_data = {
            "__data__": {"setting": "initial_value"},
            "__type_hints__": {}
        }
        
        with open(config_path, 'w') as f:
            yaml.dump(initial_data, f)
        
        print(f"配置文件路径: {config_path}")
        initial_mtime = os.path.getmtime(config_path)
        print(f"初始修改时间: {initial_mtime}")
        
        # 创建配置管理器
        config = get_config_manager(
            config_path=config_path,
            watch=True,
            test_mode=False
        )
        
        # 检查文件监视器状态
        watcher = getattr(config, '_watcher', None)
        if watcher:
            print(f"文件监视器已创建: {watcher}")
            print(f"监视器线程状态: {watcher._watcher_thread}")
            if watcher._watcher_thread:
                print(f"监视器线程是否活跃: {watcher._watcher_thread.is_alive()}")
            print(f"监视器记录的修改时间: {watcher._last_mtime}")
            print(f"内部保存标志: {watcher._internal_save_flag}")
        else:
            print("❌ 文件监视器未创建")
            return
        
        time.sleep(2)
        
        # 外部修改文件
        print("\n=== 外部修改文件 ===")
        modified_data = {
            "__data__": {"setting": "modified_value"},
            "__type_hints__": {}
        }
        
        time.sleep(0.2)  # 确保时间戳变化
        
        with open(config_path, 'w') as f:
            yaml.dump(modified_data, f)
        
        new_mtime = os.path.getmtime(config_path)
        print(f"修改后文件时间: {new_mtime}")
        print(f"时间是否变化: {new_mtime > initial_mtime}")
        
        # 等待监视器检测
        print("等待监视器检测...")
        for i in range(10):
            time.sleep(1)
            current_value = config.get('setting')
            watcher_mtime = watcher._last_mtime
            internal_flag = watcher._internal_save_flag
            
            print(f"等待 {i+1}s - 配置值: {current_value}, 监视器时间: {watcher_mtime}, 内部标志: {internal_flag}")
            
            if current_value == "modified_value":
                print("✅ 检测到外部变化")
                break
        else:
            print("❌ 10秒内未检测到外部变化")


if __name__ == "__main__":
    test_file_watcher_verbose()