# src/tools/simple_save_load_test.py
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


def simple_save_load_test():
    """简单的保存加载测试"""
    print("简单保存加载测试")
    print("=" * 20)

    with tempfile.TemporaryDirectory() as tmpdir:
        config_file = os.path.join(tmpdir, 'simple_test.yaml')

        try:
            # 清理实例
            _clear_instances_for_testing()

            # 创建配置管理器
            cfg = get_config_manager(config_path=config_file, watch=False)
            print("✓ 配置管理器创建成功")

            # 设置简单值
            cfg.simple_value = "test123"
            print(f"✓ 设置简单值: {cfg.simple_value}")
            print(f"  _data 内容: {cfg._data}")

            # 测试 to_dict
            dict_result = cfg.to_dict()
            print(f"✓ to_dict 结果: {dict_result}")

            # 保存
            print("开始保存...")
            saved = cfg.save()
            print(f"✓ 保存结果: {saved}")

            # 检查文件内容
            if os.path.exists(config_file):
                with open(config_file, 'r', encoding='utf-8') as f:
                    file_content = f.read()
                    print(f"✓ 文件内容:\n{file_content}")

                # 解析YAML
                with open(config_file, 'r', encoding='utf-8') as f:
                    parsed_content = yaml.safe_load(f)
                    print(f"✓ 解析后内容: {parsed_content}")
            else:
                print("❌ 文件不存在")
                return

            # 重新加载
            print("\n开始重新加载...")
            reloaded = cfg.reload()
            print(f"✓ 重新加载结果: {reloaded}")
            print(f"  重新加载后 _data: {cfg._data}")

            # 测试访问
            try:
                reloaded_value = cfg.simple_value
                print(f"✓ 重新加载后值: {reloaded_value}")
            except Exception as e:
                print(f"❌ 访问失败: {e}")

            # 测试get方法
            get_value = cfg.get('simple_value')
            print(f"✓ get方法结果: {get_value}")

        except Exception as e:
            print(f"❌ 测试失败: {e}")
            import traceback
            traceback.print_exc()
        finally:
            _clear_instances_for_testing()
    return


if __name__ == "__main__":
    simple_save_load_test()