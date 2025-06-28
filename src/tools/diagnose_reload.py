# src/tools/diagnose_reload.py
from __future__ import annotations
from datetime import datetime

start_time = datetime.now()

import tempfile
import os
import sys
import yaml

# 添加src到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from config_manager.config_manager import get_config_manager, _clear_instances_for_testing


def diagnose_reload_issue():
    """诊断重新加载问题"""
    print("诊断重新加载问题")
    print("=" * 30)

    with tempfile.TemporaryDirectory() as tmpdir:
        config_file = os.path.join(tmpdir, 'diagnose_config.yaml')

        try:
            # 清理实例
            _clear_instances_for_testing()

            # 创建配置管理器
            cfg = get_config_manager(config_path=config_file, watch=False)
            print("✓ 配置管理器创建成功")

            # 设置测试值
            cfg.test_value = "original_value"
            print(f"✓ 设置 test_value: {cfg.test_value}")

            # 设置嵌套值
            cfg.nested = {}
            cfg.nested.deep_value = "deep_original"
            print(f"✓ 设置嵌套值: {cfg.nested.deep_value}")

            # 检查设置后的 _data
            print(f"设置后 _data 内容: {cfg._data}")

            # 手动保存配置并检查保存前的数据
            print("开始保存...")
            print(f"保存前 to_dict() 结果: {cfg.to_dict()}")

            saved = cfg.save()
            print(f"✓ 保存结果: {saved}")

            # 检查保存的文件内容
            if os.path.exists(config_file):
                with open(config_file, 'r', encoding='utf-8') as f:
                    saved_content = yaml.safe_load(f)
                print(f"✓ 保存的文件内容: {saved_content}")
            else:
                print("❌ 配置文件不存在")

            # 重新加载前的状态
            print(f"\n重新加载前:")
            print(f"  - test_value: {cfg.test_value}")
            print(f"  - nested.deep_value: {cfg.nested.deep_value}")
            print(f"  - _data 内容: {cfg._data}")

            # 重新加载
            print("\n开始重新加载...")
            reloaded = cfg.reload()
            print(f"✓ 重新加载结果: {reloaded}")

            # 重新加载后的状态
            print(f"\n重新加载后:")
            print(f"  - _data 内容: {cfg._data}")
            print(f"  - _data 键: {list(cfg._data.keys()) if cfg._data else '空'}")

            # 测试属性访问
            try:
                test_value_after = cfg.test_value
                print(f"✓ 重新加载后 test_value: {test_value_after}")
            except AttributeError as e:
                print(f"❌ test_value 访问失败: {e}")

            try:
                nested_value_after = cfg.nested.deep_value
                print(f"✓ 重新加载后 nested.deep_value: {nested_value_after}")
            except AttributeError as e:
                print(f"❌ nested.deep_value 访问失败: {e}")

            # 测试 get 方法
            get_test = cfg.get('test_value')
            get_nested = cfg.get('nested.deep_value')
            print(f"✓ get 方法 - test_value: {get_test}")
            print(f"✓ get 方法 - nested.deep_value: {get_nested}")

        except Exception as e:
            print(f"❌ 诊断失败: {e}")
            import traceback
            traceback.print_exc()
        finally:
            _clear_instances_for_testing()
    return


if __name__ == "__main__":
    diagnose_reload_issue()