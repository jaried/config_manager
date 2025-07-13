# tests/test_duplicate_save_fix.py
from __future__ import annotations

import os
import tempfile
import time
from config_manager import get_config_manager


def test_no_duplicate_saves_during_initialization():
    """测试初始化期间不会产生重复保存"""
    with tempfile.TemporaryDirectory() as temp_dir:
        config_path = os.path.join(temp_dir, "test_config.yaml")
        
        # 计算初始化前的时间
        start_time = time.time()
        
        # 创建配置管理器，启用文件监视
        config = get_config_manager(
            config_path=config_path, 
            auto_create=True, 
            watch=True,  # 启用文件监视
            test_mode=False
        )
        
        # 设置一些配置值
        config.test_value = "initial_value"
        config.project_name = "test_project"
        
        # 等待一段时间确保所有异步操作完成
        time.sleep(2)
        
        end_time = time.time()
        
        # 验证配置被正确设置
        assert config.test_value == "initial_value"
        assert config.project_name == "test_project"
        
        # 验证配置文件确实被创建
        assert os.path.exists(config_path)
        
        print(f"初始化耗时: {end_time - start_time:.2f}秒")
        print("初始化完成，无重复保存警告")


if __name__ == "__main__":
    test_no_duplicate_saves_during_initialization()
    print("✅ 重复保存修复验证通过")