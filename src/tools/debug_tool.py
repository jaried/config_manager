# src/tools/debug_tool.py
from __future__ import annotations
from datetime import datetime

start_time = datetime.now()

import tempfile
import os
import sys
import traceback

# 添加src到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from config_manager.config_manager import get_config_manager, _clear_instances_for_testing


def debug_basic_functionality():
    """调试基本功能"""
    print("开始调试配置管理器基本功能")
    print("=" * 50)

    with tempfile.TemporaryDirectory() as tmpdir:
        config_file = os.path.join(tmpdir, 'debug_config.yaml')

        try:
            # 清理之前的实例
            _clear_instances_for_testing()
            print("✓ 清理实例完成")

            # 创建配置管理器
            cfg = get_config_manager(config_path=config_file, watch=False)
            print("✓ 配置管理器创建成功")

            # 测试基本设置
            print("开始测试基本属性设置...")
            cfg.app_name = "DebugApp"
            app_name = cfg.app_name
            print(f"✓ 设置app_name: {app_name}")

            # 测试字典设置
            print("开始测试字典设置...")
            cfg.database = {}
            print("✓ 设置空字典成功")

            cfg.database.host = "localhost"
            database_host = cfg.database.host
            print(f"✓ 设置嵌套属性: {database_host}")

            # 测试保存
            print("开始测试保存...")
            saved = cfg.save()
            print(f"✓ 保存结果: {saved}")

            # 测试重新加载
            print("开始测试重新加载...")
            reloaded = cfg.reload()
            print(f"✓ 重新加载结果: {reloaded}")

            # 验证数据仍然存在
            reloaded_app_name = cfg.app_name
            reloaded_host = cfg.database.host
            print(f"✓ 重新加载后app_name: {reloaded_app_name}")
            print(f"✓ 重新加载后database.host: {reloaded_host}")

            # 测试复杂嵌套结构
            print("\n测试复杂嵌套结构...")
            cfg.server = {
                'host': 'example.com',
                'port': 8_080,
                'settings': {
                    'timeout': 30,
                    'ssl': True
                }
            }

            server_host = cfg.server.host
            server_timeout = cfg.server.settings.timeout
            print(f"✓ 复杂嵌套设置成功: host={server_host}, timeout={server_timeout:,}")

            print("\n🎉 所有调试测试通过！")

        except Exception as e:
            print(f"\n❌ 调试测试失败: {e}")
            print("\n完整错误信息:")
            traceback.print_exc()
        finally:
            _clear_instances_for_testing()
            print("\n✓ 清理完成")
    return


def debug_type_issues():
    """调试类型相关问题"""
    print("\n调试类型相关问题")
    print("=" * 30)

    from config_manager.config_node import ConfigNode
    from config_manager.config_manager import ConfigManager

    try:
        # 测试 ConfigNode.build 方法
        print("测试 ConfigNode.build 方法...")
        test_dict = {'key': 'value'}
        built_obj = ConfigNode.build(test_dict)
        print(f"✓ ConfigNode.build 结果类型: {type(built_obj)}")

        # 测试 ConfigManager.build 方法
        print("测试 ConfigManager.build 方法...")
        built_obj2 = ConfigManager.build(test_dict)
        print(f"✓ ConfigManager.build 结果类型: {type(built_obj2)}")

        # 测试直接创建
        print("测试直接创建...")
        node = ConfigNode()
        node.test = {}
        print(f"✓ 直接设置字典成功，类型: {type(node.test)}")

    except Exception as e:
        print(f"❌ 类型调试失败: {e}")
        traceback.print_exc()
    return


if __name__ == "__main__":
    debug_basic_functionality()
    debug_type_issues()