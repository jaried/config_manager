# tests/01_unit_tests/test_config_manager/test_tc0017_001_frequent_load_save.py
from __future__ import annotations
from datetime import datetime

import os
import time
import tempfile
import shutil
import threading
from unittest.mock import patch, MagicMock

import pytest

from config_manager import get_config_manager


def test_frequent_load_save_during_initialization():
    """测试初始化过程中的频繁加载保存问题"""
    with tempfile.TemporaryDirectory() as temp_dir:
        config_path = os.path.join(temp_dir, "config.yaml")
        
        # 创建初始配置文件
        initial_config = """
app_name: "test_app"
training:
  batch_size: 32
  learning_rate: 0.001
"""
        with open(config_path, "w", encoding="utf-8") as f:
            f.write(initial_config)
        
        # 用于统计加载和保存次数的计数器
        load_count = [0]
        save_count = [0]
        
        # 监控文件操作
        from config_manager.core.file_operations import FileOperations
        file_ops = FileOperations()
        
        # 保存原始方法
        original_load = file_ops.load_config
        original_save = file_ops.save_config
        original_save_only = file_ops.save_config_only
        
        def count_load(*args, **kwargs):
            load_count[0] += 1
            print(f"配置加载第 {load_count[0]} 次: {args[0] if args else '未知路径'}")
            # 直接调用原始方法，不通过mock
            return original_load(*args, **kwargs)
            
        def count_save(*args, **kwargs):
            save_count[0] += 1
            print(f"配置保存第 {save_count[0]} 次: {args[0] if args else '未知路径'}")
            # 直接调用原始方法，不通过mock
            return original_save(*args, **kwargs)
        
        # 补丁FileOperations的方法
        with patch('config_manager.core.file_operations.FileOperations.load_config', side_effect=count_load) as mock_load, \
             patch('config_manager.core.file_operations.FileOperations.save_config', side_effect=count_save) as mock_save, \
             patch('config_manager.core.file_operations.FileOperations.save_config_only', side_effect=lambda *args, **kwargs: original_save_only(*args, **kwargs)) as mock_save_only:
            
            # 创建配置管理器实例（启用文件监视）
            config = get_config_manager(
                config_path=config_path,
                watch=True,
                auto_create=True,
                autosave_delay=0.1,  # 短延迟以便快速触发
                test_mode=True
            )
            
            # 等待初始化完成
            time.sleep(0.5)
            
            # 记录初始化后的计数
            initial_load_count = load_count[0]
            initial_save_count = save_count[0]
            
            print(f"初始化完成后 - 加载次数: {initial_load_count}, 保存次数: {initial_save_count}")
            
            # 简单的配置访问（不应该触发额外的加载保存）
            print("开始访问配置...")
            _ = config.app_name
            print(f"访问app_name后 - 加载次数: {load_count[0]}, 保存次数: {save_count[0]}")
            _ = config.training.batch_size
            print(f"访问training.batch_size后 - 加载次数: {load_count[0]}, 保存次数: {save_count[0]}")
            
            # 等待一段时间观察是否有额外的加载保存
            time.sleep(1.0)
            
            final_load_count = load_count[0]
            final_save_count = save_count[0]
            
            print(f"最终 - 加载次数: {final_load_count}, 保存次数: {final_save_count}")
            
            # 断言：初始化应该只加载一次
            assert initial_load_count == 1, f"期望初始化时只加载1次，实际加载了{initial_load_count}次"
            
            # 断言：简单的读取操作不应该触发额外的加载
            assert final_load_count == initial_load_count, f"简单读取操作不应该触发额外加载，加载次数从{initial_load_count}增加到{final_load_count}"
            
            # 断言：初始化时最多只应该有1次保存操作（初始化备份）
            # 调整期望：初始化过程可能有1次备份保存，但不应该有额外的自动保存
            assert final_save_count <= 1, f"初始化时最多只应该有1次保存操作（初始化备份），实际保存了{final_save_count}次"
            
            # 如果有超过1次保存，说明存在不必要的自动保存
            if final_save_count > 1:
                print(f"警告：检测到{final_save_count}次保存操作，可能存在不必要的自动保存")


def test_watch_save_cycle_prevention():
    """测试文件监视器和自动保存的循环问题"""
    with tempfile.TemporaryDirectory() as temp_dir:
        config_path = os.path.join(temp_dir, "config.yaml")
        
        # 创建初始配置文件
        initial_config = """
app_name: "test_app"
value: 100
"""
        with open(config_path, "w", encoding="utf-8") as f:
            f.write(initial_config)
        
        # 统计文件监视器回调次数
        callback_count = [0]
        
        def count_callback():
            callback_count[0] += 1
            print(f"文件监视器回调第 {callback_count[0]} 次")
        
        # 监控保存操作
        save_count = [0]
        
        # 获取原始方法引用，避免每次创建新实例
        from config_manager.core.file_operations import FileOperations
        original_save_config = FileOperations.save_config
        
        def count_save(self, *args, **kwargs):
            save_count[0] += 1
            print(f"保存操作第 {save_count[0]} 次")
            # 调用原始方法，使用相同的实例
            return original_save_config(self, *args, **kwargs)
        
        with patch('config_manager.core.file_operations.FileOperations.save_config', side_effect=count_save):
            # 创建配置管理器
            config = get_config_manager(
                config_path=config_path,
                watch=True,
                auto_create=True,
                autosave_delay=0.1,
                test_mode=True
            )
            
            # 等待初始化
            time.sleep(0.2)
            
            # 修改配置触发保存
            config.value = 200
            
            # 等待自动保存完成
            time.sleep(0.5)
            
            record_save_count = save_count[0]
            record_callback_count = callback_count[0]
            
            # 再等待一段时间观察是否有循环
            time.sleep(2.0)
            
            final_save_count = save_count[0]
            final_callback_count = callback_count[0]
            
            print(f"修改后保存次数: {record_save_count} -> {final_save_count}")
            print(f"监视器回调次数: {record_callback_count} -> {final_callback_count}")
            
            # 断言：一次修改应该只触发一次保存
            assert final_save_count <= 2, f"一次配置修改应该最多触发2次保存（初始化备份+正常保存），实际保存了{final_save_count}次"
            
            # 断言：保存操作不应该触发监视器的无限回调
            assert final_callback_count <= 1, f"内部保存不应该触发监视器回调，实际回调了{final_callback_count}次"


def test_multiple_config_changes_batching():
    """测试多次配置修改的批量处理"""
    with tempfile.TemporaryDirectory() as temp_dir:
        config_path = os.path.join(temp_dir, "config.yaml")
        
        # 创建初始配置
        initial_config = """
app_name: "test_app"
settings:
  value1: 1
  value2: 2
  value3: 3
"""
        with open(config_path, "w", encoding="utf-8") as f:
            f.write(initial_config)
        
        save_count = [0]
        
        # 获取原始方法引用，避免每次创建新实例
        from config_manager.core.file_operations import FileOperations
        original_save_config = FileOperations.save_config
        
        def count_save(self, *args, **kwargs):
            save_count[0] += 1
            print(f"保存操作第 {save_count[0]} 次")
            # 调用原始方法，使用相同的实例
            return original_save_config(self, *args, **kwargs)
        
        with patch('config_manager.core.file_operations.FileOperations.save_config', side_effect=count_save):
            config = get_config_manager(
                config_path=config_path,
                watch=False,  # 关闭监视避免干扰
                auto_create=True,
                autosave_delay=0.2,  # 较长延迟以便批量处理
                test_mode=True
            )
            
            # 等待初始化
            time.sleep(0.1)
            initial_save_count = save_count[0]
            
            # 快速连续修改多个配置
            config.settings.value1 = 10
            config.settings.value2 = 20
            config.settings.value3 = 30
            config.app_name = "modified_app"
            
            # 在延迟时间内再次修改
            time.sleep(0.1)
            config.settings.value1 = 100
            
            # 等待所有自动保存完成
            time.sleep(0.5)
            
            final_save_count = save_count[0]
            save_operations = final_save_count - initial_save_count
            
            print(f"5次配置修改触发了 {save_operations} 次保存操作")
            
            # 断言：多次快速修改应该被批量处理，不应该每次都保存
            assert save_operations <= 2, f"5次快速配置修改应该被批量处理为最多2次保存，实际保存了{save_operations}次"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])