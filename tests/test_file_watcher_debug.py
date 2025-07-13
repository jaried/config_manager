# tests/test_file_watcher_debug.py
from __future__ import annotations

import os
import tempfile
import time
import yaml
from config_manager import get_config_manager


def test_file_watcher_external_change():
    """测试文件监视器对外部文件变化的检测"""
    
    with tempfile.TemporaryDirectory() as temp_dir:
        config_path = os.path.join(temp_dir, "test_config.yaml")
        
        # 创建初始配置文件
        initial_data = {
            "__data__": {"setting": "initial_value"},
            "__type_hints__": {}
        }
        
        with open(config_path, 'w') as f:
            yaml.dump(initial_data, f)
        
        print(f"创建配置文件: {config_path}")
        
        # 创建配置管理器，启用文件监视
        config = get_config_manager(
            config_path=config_path,
            watch=True,
            test_mode=False
        )
        
        print(f"初始值: {config.get('setting')}")
        assert config.get('setting') == "initial_value"
        
        # 等待文件监视器启动
        print("等待文件监视器启动...")
        time.sleep(2)
        
        # 在外部修改配置文件
        print("外部修改配置文件...")
        modified_data = {
            "__data__": {"setting": "modified_value"},
            "__type_hints__": {}
        }
        
        time.sleep(0.1)  # 确保时间戳变化
        
        with open(config_path, 'w') as f:
            yaml.dump(modified_data, f)
        
        print("等待文件监视器检测变化...")
        time.sleep(5)  # 给文件监视器足够时间检测变化
        
        # 检查配置是否已更新
        current_value = config.get('setting')
        print(f"当前值: {current_value}")
        
        if current_value == "modified_value":
            print("✅ 文件监视器正常工作")
        else:
            print("❌ 文件监视器未检测到外部变化")
            
            # 手动重新加载测试
            print("尝试手动重新加载...")
            config.reload()
            reloaded_value = config.get('setting')
            print(f"手动重新加载后的值: {reloaded_value}")


if __name__ == "__main__":
    test_file_watcher_external_change()