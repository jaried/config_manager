# src/demo/demo_config_manager_advanced.py
from __future__ import annotations
from datetime import datetime

start_time = datetime.now()

import time
import tempfile
import os
from config_manager import get_config_manager


def demo_snapshots_and_restore():
    """演示快照和恢复功能"""
    print("快照和恢复功能演示")
    print("=" * 50)

    # 创建临时配置文件
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as tmp:
        demo_config_path = tmp.name

    try:
        cfg = get_config_manager(
            config_path=demo_config_path,
            watch=False,
            autosave_delay=0.5
        )

        # 1. 设置初始配置
        print("\n1. 设置初始配置")
        cfg.app_state = "production"
        cfg.feature_flags = {}
        cfg.feature_flags.new_dashboard = True
        cfg.feature_flags.beta_features = False
        cfg.performance = {}
        cfg.performance.cache_size = 1_000
        cfg.performance.max_workers = 8

        app_state = cfg.app_state
        new_dashboard = cfg.feature_flags.new_dashboard
        cache_size = cfg.performance.cache_size
        print(f"应用状态: {app_state}")
        print(f"新仪表板: {new_dashboard}")
        print(f"缓存大小: {cache_size:,}")

        # 2. 创建快照
        print("\n2. 创建配置快照")
        production_snapshot = cfg.snapshot()
        print("✓ 生产环境快照已创建")

        # 3. 修改配置进行测试
        print("\n3. 修改配置进行测试")
        cfg.app_state = "testing"
        cfg.feature_flags.beta_features = True
        cfg.feature_flags.experimental_ui = True
        cfg.performance.cache_size = 500
        cfg.test_settings = {}
        cfg.test_settings.mock_data = True
        cfg.test_settings.log_level = "DEBUG"

        modified_state = cfg.app_state
        beta_features = cfg.feature_flags.beta_features
        mock_data = cfg.test_settings.mock_data
        print(f"修改后状态: {modified_state}")
        print(f"Beta功能: {beta_features}")
        print(f"模拟数据: {mock_data}")

        # 4. 恢复到快照
        print("\n4. 恢复到生产环境快照")
        cfg.restore(production_snapshot)

        # 使用get方法安全访问恢复后的数据
        restored_state = cfg.get('app_state', 'unknown')
        restored_dashboard = cfg.get('feature_flags.new_dashboard', False)
        restored_cache = cfg.get('performance.cache_size', 0)
        restored_test = cfg.get('test_settings.mock_data', None)

        print(f"恢复后状态: {restored_state}")
        print(f"新仪表板: {restored_dashboard}")
        print(f"缓存大小: {restored_cache:,}")
        print(f"测试设置: {restored_test} (应该为None)")
        print("✓ 成功恢复到生产环境配置")

        return demo_config_path

    except Exception as e:
        print(f"❌ 快照演示失败: {e}")
        if os.path.exists(demo_config_path):
            os.unlink(demo_config_path)
        raise


def demo_temporary_context():
    """演示临时配置上下文"""
    print("\n" + "=" * 50)
    print("临时配置上下文演示")
    print("=" * 50)

    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as tmp:
        demo_config_path = tmp.name

    try:
        cfg = get_config_manager(
            config_path=demo_config_path,
            watch=False,
            autosave_delay=0.5
        )

        # 1. 设置基础配置
        print("\n1. 设置基础配置")
        cfg.environment = "production"
        cfg.logging = {}
        cfg.logging.level = "INFO"
        cfg.logging.detailed = False
        cfg.database = {}
        cfg.database.pool_size = 10

        env = cfg.environment
        log_level = cfg.logging.level
        pool_size = cfg.database.pool_size
        print(f"环境: {env}")
        print(f"日志级别: {log_level}")
        print(f"数据库连接池: {pool_size:,}")

        # 2. 使用临时上下文进行调试
        print("\n2. 使用临时上下文进行调试")
        debug_changes = {
            "environment": "debug",
            "logging.level": "DEBUG",
            "logging.detailed": True,
            "database.pool_size": 5,
            "debug_flags.enable_profiling": True,
            "debug_flags.slow_query_log": True
        }

        print("进入调试上下文...")
        with cfg.temporary(debug_changes) as debug_cfg:
            # 在临时上下文中访问配置
            temp_env = debug_cfg.get('environment')
            temp_log_level = debug_cfg.get('logging.level')
            temp_detailed = debug_cfg.get('logging.detailed')
            temp_profiling = debug_cfg.get('debug_flags.enable_profiling')

            print(f"  临时环境: {temp_env}")
            print(f"  临时日志级别: {temp_log_level}")
            print(f"  详细日志: {temp_detailed}")
            print(f"  性能分析: {temp_profiling}")

            # 在临时上下文中模拟一些操作
            print("  在调试模式下执行操作...")
            time.sleep(0.1)

        # 3. 验证上下文退出后配置恢复
        print("\n3. 验证配置已恢复")
        final_env = cfg.environment
        final_log_level = cfg.logging.level
        final_detailed = cfg.logging.detailed
        final_pool_size = cfg.database.pool_size
        final_profiling = cfg.get('debug_flags.enable_profiling', None)

        print(f"最终环境: {final_env}")
        print(f"最终日志级别: {final_log_level}")
        print(f"详细日志: {final_detailed}")
        print(f"连接池大小: {final_pool_size:,}")
        print(f"性能分析标志: {final_profiling} (应该为None)")
        print("✓ 临时上下文退出后配置已恢复")

        return demo_config_path

    except Exception as e:
        print(f"❌ 临时上下文演示失败: {e}")
        if os.path.exists(demo_config_path):
            os.unlink(demo_config_path)
        raise


def demo_config_id_generation():
    """演示配置ID生成功能"""
    print("\n" + "=" * 50)
    print("配置ID生成功能演示")
    print("=" * 50)

    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as tmp:
        demo_config_path = tmp.name

    try:
        cfg = get_config_manager(
            config_path=demo_config_path,
            watch=False,
            autosave_delay=0.5
        )

        # 1. 生成实验配置ID
        print("\n1. 生成实验配置ID")
        experiments = {}

        for i in range(3):
            experiment_id = cfg.generate_config_id()
            experiment_name = f"实验_{i + 1:02d}"

            # 使用set方法设置嵌套配置
            cfg.set(f"experiments.{experiment_id}.name", experiment_name)
            cfg.set(f"experiments.{experiment_id}.status", "active")
            cfg.set(f"experiments.{experiment_id}.start_time", datetime.now().isoformat())
            cfg.set(f"experiments.{experiment_id}.parameters.learning_rate", 0.001 * (i + 1))
            cfg.set(f"experiments.{experiment_id}.parameters.batch_size", 32 * (2 ** i))

            experiments[experiment_id] = experiment_name

            exp_name = cfg.get(f"experiments.{experiment_id}.name")
            exp_status = cfg.get(f"experiments.{experiment_id}.status")
            exp_lr = cfg.get(f"experiments.{experiment_id}.parameters.learning_rate")
            exp_batch = cfg.get(f"experiments.{experiment_id}.parameters.batch_size")

            print(f"实验ID: {experiment_id}")
            print(f"  名称: {exp_name}")
            print(f"  状态: {exp_status}")
            print(f"  学习率: {exp_lr}")
            print(f"  批次大小: {exp_batch:,}")

        # 2. 会话管理
        print("\n2. 会话管理演示")
        active_sessions = {}

        for i in range(2):
            session_id = cfg.generate_config_id()
            user_id = f"user_{1000 + i:,}"

            cfg.set(f"sessions.{session_id}.user_id", user_id)
            cfg.set(f"sessions.{session_id}.login_time", datetime.now().isoformat())
            cfg.set(f"sessions.{session_id}.active", True)
            cfg.set(f"sessions.{session_id}.permissions", ["read", "write"])

            active_sessions[session_id] = user_id

            session_user = cfg.get(f"sessions.{session_id}.user_id")
            session_active = cfg.get(f"sessions.{session_id}.active")
            session_perms = cfg.get(f"sessions.{session_id}.permissions")

            print(f"会话ID: {session_id}")
            print(f"  用户: {session_user}")
            print(f"  活跃: {session_active}")
            print(f"  权限: {session_perms}")

        print(f"\n✓ 生成了 {len(experiments):,} 个实验和 {len(active_sessions):,} 个会话")

        return demo_config_path

    except Exception as e:
        print(f"❌ ID生成演示失败: {e}")
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
        print("配置管理器高级功能演示")
        print("=" * 60)

        # 运行各种高级功能演示
        file1 = demo_snapshots_and_restore()
        demo_files.append(file1)

        file2 = demo_temporary_context()
        demo_files.append(file2)

        file3 = demo_config_id_generation()
        demo_files.append(file3)

        print("\n" + "=" * 60)
        print("高级功能演示完成！")
        print("=" * 60)
        print("\n主要高级特性:")
        print("• 配置快照和恢复")
        print("• 临时配置上下文管理")
        print("• 唯一ID生成用于实验和会话管理")
        print("• 嵌套配置的动态设置和访问")
        print("• 线程安全的并发操作")

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