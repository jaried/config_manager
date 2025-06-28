# src/demo/demo_config_manager_autosave.py
from __future__ import annotations
from datetime import datetime

start_time = datetime.now()

import time
import tempfile
import os
from config_manager import get_config_manager


def demo_autosave_basic():
    """演示基本自动保存功能"""
    print("基本自动保存功能演示")
    print("=" * 50)

    # 创建临时配置文件用于演示
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as tmp:
        demo_config_path = tmp.name

    try:
        # 1. 创建启用自动保存的配置管理器
        print("\n1. 初始化自动保存配置管理器")
        cfg = get_config_manager(
            config_path=demo_config_path,
            watch=False,  # 演示时关闭文件监视
            autosave_delay=1.0  # 1秒延迟，便于观察
        )
        print(f"配置文件路径: {demo_config_path}")
        print("自动保存延迟: 1.0秒")

        # 2. 设置配置值触发自动保存
        print("\n2. 设置配置值（将触发自动保存）")
        cfg.session_id = "demo_session_001"
        cfg.user_preferences = {}
        cfg.user_preferences.theme = "dark"
        cfg.user_preferences.language = "zh-CN"

        session_id = cfg.session_id
        theme = cfg.user_preferences.theme
        language = cfg.user_preferences.language
        print(f"会话ID: {session_id}")
        print(f"主题: {theme}")
        print(f"语言: {language}")

        # 3. 等待自动保存完成
        print("\n3. 等待自动保存...")
        print("正在等待1.5秒让自动保存完成...")
        time.sleep(1.5)

        # 4. 验证文件已更新
        print("\n4. 验证自动保存")
        file_exists = os.path.exists(demo_config_path)
        if file_exists:
            file_size = os.path.getsize(demo_config_path)
            print(f"✓ 配置文件已自动保存")
            print(f"  文件大小: {file_size:,} 字节")
        else:
            print("❌ 配置文件未找到")

        # 5. 连续修改测试
        print("\n5. 连续修改测试")
        print("快速连续设置多个值...")
        cfg.stats = {}
        cfg.stats.login_count = 5
        cfg.stats.last_login = "2025-05-29T10:30:00"
        cfg.stats.total_sessions = 127

        login_count = cfg.stats.login_count
        last_login = cfg.stats.last_login
        total_sessions = cfg.stats.total_sessions
        print(f"登录次数: {login_count:,}")
        print(f"最后登录: {last_login}")
        print(f"总会话数: {total_sessions:,}")

        print("等待自动保存...")
        time.sleep(1.5)
        print("✓ 连续修改的自动保存完成")

        return cfg, demo_config_path

    except Exception as e:
        print(f"❌ 自动保存演示失败: {e}")
        # 清理临时文件
        if os.path.exists(demo_config_path):
            os.unlink(demo_config_path)
        raise


def demo_autosave_delay_control():
    """演示自动保存延迟控制"""
    print("\n" + "=" * 50)
    print("自动保存延迟控制演示")
    print("=" * 50)

    # 创建临时配置文件
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as tmp:
        demo_config_path = tmp.name

    try:
        # 1. 短延迟配置管理器
        print("\n1. 短延迟自动保存（0.2秒）")
        cfg_fast = get_config_manager(
            config_path=demo_config_path,
            watch=False,
            autosave_delay=0.2
        )

        start_time_val = time.time()
        cfg_fast.fast_save_test = "quick_value"
        print("设置值，等待快速自动保存...")
        time.sleep(0.5)
        fast_duration = time.time() - start_time_val
        print(f"✓ 快速保存完成，耗时: {fast_duration:.2f}秒")

        # 2. 较长延迟的影响
        print("\n2. 延迟期间的多次修改")
        print("在自动保存触发前进行多次修改...")

        cfg_fast.rapid_changes = {}
        time.sleep(0.05)
        cfg_fast.rapid_changes.change1 = "value1"
        time.sleep(0.05)
        cfg_fast.rapid_changes.change2 = "value2"
        time.sleep(0.05)
        cfg_fast.rapid_changes.change3 = "value3"

        print("等待最终自动保存...")
        time.sleep(0.5)

        change1 = cfg_fast.rapid_changes.change1
        change2 = cfg_fast.rapid_changes.change2
        change3 = cfg_fast.rapid_changes.change3
        print(f"✓ 所有快速修改都已保存:")
        print(f"  变更1: {change1}")
        print(f"  变更2: {change2}")
        print(f"  变更3: {change3}")

        return demo_config_path

    except Exception as e:
        print(f"❌ 延迟控制演示失败: {e}")
        if os.path.exists(demo_config_path):
            os.unlink(demo_config_path)
        raise


def demo_autosave_performance():
    """演示自动保存性能特性"""
    print("\n" + "=" * 50)
    print("自动保存性能特性演示")
    print("=" * 50)

    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as tmp:
        demo_config_path = tmp.name

    try:
        cfg = get_config_manager(
            config_path=demo_config_path,
            watch=False,
            autosave_delay=0.3
        )

        # 1. 大量数据保存测试
        print("\n1. 大量数据自动保存测试")
        print("创建包含大量数据的配置...")

        cfg.large_dataset = {}
        for i in range(100):
            cfg.large_dataset[f"item_{i:03d}"] = {
                "id": i,
                "name": f"项目_{i:,}",
                "value": i * 1.234,
                "active": i % 2 == 0,
                "tags": [f"tag_{j}" for j in range(i % 5)]
            }

        print("✓ 创建了100个复杂数据项")
        print("等待大量数据自动保存...")

        save_start = time.time()
        time.sleep(0.5)
        save_duration = time.time() - save_start

        # 检查文件大小
        if os.path.exists(demo_config_path):
            file_size = os.path.getsize(demo_config_path)
            print(f"✓ 大量数据保存完成")
            print(f"  保存时长: {save_duration:.2f}秒")
            print(f"  文件大小: {file_size:,} 字节")

        # 2. 数据完整性验证
        print("\n2. 数据完整性验证")
        item_50 = cfg.large_dataset.item_050
        item_99 = cfg.large_dataset.item_099

        print(f"第50项: ID={item_50.id}, 名称={item_50.name}")
        print(f"第99项: ID={item_99.id}, 值={item_99.value:.3f}")
        print("✓ 大量数据保存后访问正常")

        return demo_config_path

    except Exception as e:
        print(f"❌ 性能演示失败: {e}")
        if os.path.exists(demo_config_path):
            os.unlink(demo_config_path)
        raise


def cleanup_demo_files(*file_paths):
    """清理演示文件"""
    print("\n清理演示文件...")
    for file_path in file_paths:
        if file_path and os.path.exists(file_path):
            try:
                os.unlink(file_path)
                print(f"✓ 已删除: {file_path}")
            except Exception as e:
                print(f"❌ 删除失败 {file_path}: {e}")
    return


def main():
    """主函数"""
    demo_files = []

    try:
        print("配置管理器自动保存功能演示")
        print("=" * 60)

        # 运行各种自动保存演示
        cfg, file1 = demo_autosave_basic()
        demo_files.append(file1)

        file2 = demo_autosave_delay_control()
        demo_files.append(file2)

        file3 = demo_autosave_performance()
        demo_files.append(file3)

        print("\n" + "=" * 60)
        print("自动保存功能演示完成！")
        print("=" * 60)
        print("\n主要特性:")
        print("• 自动保存延迟可配置")
        print("• 支持连续修改的智能合并")
        print("• 大量数据的高效保存")
        print("• 线程安全的保存机制")

    except Exception as e:
        print(f"演示过程中出现错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # 清理所有演示文件
        cleanup_demo_files(*demo_files)
    return


if __name__ == "__main__":
    main()