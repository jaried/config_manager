# src/tools/autosave_test.py
from __future__ import annotations
from datetime import datetime

start_time = datetime.now()

import tempfile
import os
import sys
import time
import yaml

# 添加src到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from config_manager.config_manager import get_config_manager, _clear_instances_for_testing


def autosave_test():
    """测试自动保存功能"""
    print("自动保存功能测试")
    print("=" * 20)

    with tempfile.TemporaryDirectory() as tmpdir:
        config_file = os.path.join(tmpdir, 'autosave_test.yaml')

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

            # 设置值
            cfg.autosave_test = "auto_value"
            print(f"✓ 设置值: {cfg.autosave_test}")
            print(f"  _data 内容: {cfg._data}")

            # 等待自动保存
            print("等待自动保存...")
            time.sleep(0.2)

            # 检查文件是否存在
            file_exists = os.path.exists(config_file)
            print(f"✓ 文件存在: {file_exists}")

            if file_exists:
                # 检查文件内容
                with open(config_file, 'r', encoding='utf-8') as f:
                    file_content = f.read()
                    print(f"✓ 自动保存的文件内容:\n{file_content}")

                # 解析内容
                with open(config_file, 'r', encoding='utf-8') as f:
                    parsed_content = yaml.safe_load(f)
                    print(f"✓ 解析后内容: {parsed_content}")

                    data_section = parsed_content.get('__data__', {})
                    print(f"✓ 数据段: {data_section}")

                    if 'autosave_test' in data_section:
                        print(f"✓ 找到自动保存的值: {data_section['autosave_test']}")
                    else:
                        print("❌ 没有找到自动保存的值")
                        print(f"  可用键: {list(data_section.keys())}")

            # 重新加载测试
            print("\n测试重新加载...")
            reloaded = cfg.reload()
            print(f"✓ 重新加载结果: {reloaded}")
            print(f"  重新加载后 _data: {cfg._data}")

            # 测试访问
            try:
                reloaded_value = cfg.autosave_test
                print(f"✓ 重新加载后值: {reloaded_value}")
            except Exception as e:
                print(f"❌ 访问失败: {e}")
                # 尝试直接从_data访问
                direct_value = cfg._data.get('autosave_test')
                print(f"  直接从_data访问: {direct_value}")

        except Exception as e:
            print(f"❌ 测试失败: {e}")
            import traceback
            traceback.print_exc()
        finally:
            _clear_instances_for_testing()
    return


if __name__ == "__main__":
    autosave_test()