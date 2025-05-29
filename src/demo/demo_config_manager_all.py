# src/demo/demo_config_manager_all.py
from __future__ import annotations
from datetime import datetime

start_time = datetime.now()

import sys
import os

# 添加src到路径以便导入其他演示模块
sys.path.insert(0, os.path.dirname(__file__))

from demo_config_manager_basic import main as demo_basic_main
from demo_config_manager_autosave import main as demo_autosave_main
from demo_config_manager_advanced import main as demo_advanced_main
from demo_config_manager_file_operations import main as demo_file_ops_main


def print_banner(title: str):
    """打印标题横幅"""
    banner_length = 80
    print("\n" + "=" * banner_length)
    print(f" {title.center(banner_length - 2)} ")
    print("=" * banner_length)
    return


def print_section_separator():
    """打印章节分隔符"""
    print("\n" + "-" * 80)
    print("按回车键继续下一个演示，或输入 'q' 退出...")
    user_input = input()
    if user_input.lower() == 'q':
        return False
    return True


def main():
    """运行所有配置管理器演示"""
    print_banner("配置管理器完整功能演示")

    print("\n欢迎使用配置管理器演示程序！")
    print("\n本演示将展示配置管理器的所有主要功能：")
    print("• 基本操作：属性设置、类型支持、批量操作")
    print("• 自动保存：智能保存、延迟控制、性能优化")
    print("• 高级功能：快照恢复、临时上下文、ID生成")
    print("• 文件操作：文件监视、多配置管理、备份恢复")

    demos = [
        ("基本功能演示", demo_basic_main),
        ("自动保存功能演示", demo_autosave_main),
        ("高级功能演示", demo_advanced_main),
        ("文件操作演示", demo_file_ops_main)
    ]

    try:
        for i, (demo_name, demo_func) in enumerate(demos, 1):
            print_banner(f"第 {i} 部分：{demo_name}")

            try:
                demo_func()
                print(f"\n✓ {demo_name} 完成")
            except Exception as e:
                print(f"\n❌ {demo_name} 失败: {e}")
                import traceback
                traceback.print_exc()

            # 如果不是最后一个演示，询问是否继续
            if i < len(demos):
                if not print_section_separator():
                    print("\n演示已中断。")
                    return

        # 最终总结
        print_banner("演示总结")
        print("\n🎉 恭喜！您已完成配置管理器的完整功能演示。")
        print("\n配置管理器的主要优势：")
        print("• 🚀 简单易用：直观的点操作语法")
        print("• 💾 自动保存：智能的数据持久化")
        print("• 🔒 线程安全：并发环境下的可靠性")
        print("• 🎯 类型安全：完整的类型提示支持")
        print("• 📁 文件监视：实时的配置同步")
        print("• 🔄 快照恢复：便捷的状态管理")
        print("• ⚡ 高性能：优化的内存和IO操作")

        print("\n使用场景：")
        print("• 应用程序配置管理")
        print("• 实验参数记录")
        print("• 用户偏好设置")
        print("• 系统状态跟踪")
        print("• 开发环境配置")

        print("\n开始使用：")
        print("```python")
        print("from config_manager import get_config_manager")
        print("")
        print("# 获取配置管理器")
        print("cfg = get_config_manager()")
        print("")
        print("# 设置配置")
        print("cfg.app_name = 'MyApp'")
        print("cfg.database.host = 'localhost'")
        print("")
        print("# 自动保存和类型安全！")
        print("```")

        print("\n感谢您使用配置管理器！")

    except KeyboardInterrupt:
        print("\n\n演示被用户中断。")
    except Exception as e:
        print(f"\n\n演示过程中出现意外错误: {e}")
        import traceback
        traceback.print_exc()
    return


if __name__ == "__main__":
    main()
