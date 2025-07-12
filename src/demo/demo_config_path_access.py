# src/demo/demo_config_path_access.py
from __future__ import annotations
from datetime import datetime

start_time = datetime.now()

import os
import tempfile
from config_manager import get_config_manager


def demo_config_path_access():
    """演示配置文件路径访问功能"""
    print("配置文件路径访问演示")
    print("=" * 50)

    # 1. 使用默认路径的配置管理器
    print("\n1. 使用默认路径的配置管理器")
    cfg_default = get_config_manager(first_start_time=start_time)
    
    print(f"默认配置路径: {cfg_default.get_config_path()}")
    print(f"配置文件绝对路径: {cfg_default.get_config_file_path()}")
    
    # 设置一些配置值
    cfg_default.app_name = "默认路径应用"
    cfg_default.version = "1.0.0"
    
    # 2. 使用明确指定路径的配置管理器
    print("\n2. 使用明确指定路径的配置管理器")
    with tempfile.TemporaryDirectory() as tmpdir:
        custom_config_path = os.path.join(tmpdir, "custom_config.yaml")
        
        cfg_custom = get_config_manager(
            config_path=custom_config_path,
            auto_create=True,
            first_start_time=start_time
        )
        
        print(f"自定义配置路径: {cfg_custom.get_config_path()}")
        print(f"配置文件绝对路径: {cfg_custom.get_config_file_path()}")
        
        # 设置一些配置值
        cfg_custom.app_name = "自定义路径应用"
        cfg_custom.version = "2.0.0"
        cfg_custom.database = {}
        cfg_custom.database.host = "localhost"
        cfg_custom.database.port = 5432
        
        # 3. 演示配置数据中包含路径信息
        print("\n3. 配置数据中的路径信息")
        print("默认配置中的路径信息:")
        print(f"  config_file_path: {cfg_default._data.get('config_file_path')}")
        
        print("\n自定义配置中的路径信息:")
        print(f"  config_file_path: {cfg_custom._data.get('config_file_path')}")
        
        # 4. 演示路径信息在配置重载后的持久性
        print("\n4. 配置重载后的路径信息持久性")
        cfg_custom.test_value = "重载前的值"
        
        # 手动保存
        cfg_custom.save()
        
        # 重新加载
        cfg_custom.reload()
        
        print("重载后的路径信息:")
        print(f"  配置文件绝对路径: {cfg_custom.get_config_file_path()}")
        print(f"  测试值: {cfg_custom.test_value}")

    return cfg_default, cfg_custom


def demo_path_based_operations():
    """演示基于路径的操作"""
    print("\n" + "=" * 50)
    print("基于路径的操作演示")
    print("=" * 50)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = os.path.join(tmpdir, "operations_config.yaml")
        
        cfg = get_config_manager(
            config_path=config_path,
            auto_create=True,
            first_start_time=start_time
        )
        
        # 1. 获取配置文件所在目录
        print("\n1. 配置文件目录信息")
        config_file_path = cfg.get_config_file_path()
        config_dir = os.path.dirname(config_file_path)
        config_filename = os.path.basename(config_file_path)
        
        print(f"配置文件完整路径: {config_file_path}")
        print(f"配置文件目录: {config_dir}")
        print(f"配置文件名: {config_filename}")
        
        # 2. 基于配置文件路径创建相关文件
        print("\n2. 基于配置路径创建相关文件")
        log_dir = os.path.join(config_dir, "logs")
        data_dir = os.path.join(config_dir, "data")
        
        os.makedirs(log_dir, exist_ok=True)
        os.makedirs(data_dir, exist_ok=True)
        
        # 将这些路径保存到配置中
        cfg.paths = {}
        cfg.paths.config_file = config_file_path
        cfg.paths.config_dir = config_dir
        cfg.paths.log_dir = log_dir
        cfg.paths.data_dir = data_dir
        
        print(f"日志目录: {cfg.paths.log_dir}")
        print(f"数据目录: {cfg.paths.data_dir}")
        
        # 3. 验证路径信息的一致性
        print("\n3. 路径信息一致性验证")
        stored_config_path = cfg.paths.config_file
        retrieved_config_path = cfg.get_config_file_path()
        
        print(f"存储的配置路径: {stored_config_path}")
        print(f"检索的配置路径: {retrieved_config_path}")
        print(f"路径一致性: {stored_config_path == retrieved_config_path}")

    return cfg


if __name__ == "__main__":
    # 运行演示
    cfg_default, cfg_custom = demo_config_path_access()
    cfg_operations = demo_path_based_operations()
    
    print("\n" + "=" * 50)
    print("演示完成")
    print("=" * 50) 