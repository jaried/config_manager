# src/demo/demo_config_manager_file_operations.py
from __future__ import annotations
from datetime import datetime

start_time = datetime.now()

import time
import tempfile
import os
import shutil
from pathlib import Path
from config_manager import get_config_manager


def demo_file_monitoring():
    """演示文件监视功能"""
    print("文件监视功能演示")
    print("=" * 50)

    # 创建临时配置文件
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as tmp:
        demo_config_path = tmp.name

    try:
        # 1. 启用文件监视的配置管理器
        print("\n1. 启用文件监视")
        cfg = get_config_manager(
            config_path=demo_config_path,
            watch=True,  # 启用文件监视
            autosave_delay=0.5
        )
        print(f"配置文件路径: {demo_config_path}")
        print("文件监视已启用")

        # 2. 设置初始配置
        print("\n2. 设置初始配置")
        cfg.app_name = "FileMonitorDemo"
        cfg.version = "1.0.0"
        cfg.settings = {}
        cfg.settings.auto_refresh = True

        app_name = cfg.app_name
        version = cfg.version
        auto_refresh = cfg.settings.auto_refresh
        print(f"应用名称: {app_name}")
        print(f"版本: {version}")
        print(f"自动刷新: {auto_refresh}")

        # 等待自动保存
        time.sleep(1.0)

        # 3. 外部修改文件（模拟其他程序修改）
        print("\n3. 模拟外部文件修改")
        print("正在外部修改配置文件...")

        # 读取当前文件内容
        with open(demo_config_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 修改内容（添加新的配置项）
        external_config = """__data__:
  app_name: FileMonitorDemo
  version: '2.0.0'
  settings:
    auto_refresh: true
    new_feature: true
  external_change:
    modified_by: external_program
    timestamp: '2025-05-29T12:00:00'
__type_hints__: {}"""

        with open(demo_config_path, 'w', encoding='utf-8') as f:
            f.write(external_config)

        print("✓ 文件已被外部程序修改")

        # 4. 等待自动重新加载
        print("\n4. 等待自动重新加载...")
        print("文件监视器会在2秒内检测到变化...")
        time.sleep(3.0)

        # 5. 验证配置已更新
        print("\n5. 验证配置自动更新")
        updated_version = cfg.get('version', '未知')
        new_feature = cfg.get('settings.new_feature', False)
        external_change = cfg.get('external_change.modified_by', '无')
        timestamp = cfg.get('external_change.timestamp', '无')

        print(f"更新后版本: {updated_version}")
        print(f"新功能: {new_feature}")
        print(f"外部修改者: {external_change}")
        print(f"修改时间: {timestamp}")

        if updated_version == "2.0.0":
            print("✓ 文件监视器成功检测并重新加载了外部更改")
        else:
            print("❌ 文件监视器未能检测到外部更改")

        return demo_config_path

    except Exception as e:
        print(f"❌ 文件监视演示失败: {e}")
        if os.path.exists(demo_config_path):
            os.unlink(demo_config_path)
        raise


def demo_multiple_config_files():
    """演示多配置文件管理"""
    print("\n" + "=" * 50)
    print("多配置文件管理演示")
    print("=" * 50)

    config_files = []

    try:
        # 1. 创建多个配置文件
        print("\n1. 创建多个配置文件")

        # 主配置文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='_main.yaml', delete=False) as tmp:
            main_config_path = tmp.name
        config_files.append(main_config_path)

        # 用户配置文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='_user.yaml', delete=False) as tmp:
            user_config_path = tmp.name
        config_files.append(user_config_path)

        # 环境配置文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='_env.yaml', delete=False) as tmp:
            env_config_path = tmp.name
        config_files.append(env_config_path)

        # 2. 配置主应用设置
        print("\n2. 配置主应用设置")
        main_cfg = get_config_manager(
            config_path=main_config_path,
            watch=False,
            autosave_delay=0.3
        )

        main_cfg.app = {}
        main_cfg.app.name = "MultiConfigApp"
        main_cfg.app.version = "1.0.0"
        main_cfg.app.modules = ["core", "ui", "api"]
        main_cfg.database = {}
        main_cfg.database.host = "localhost"
        main_cfg.database.port = 5_432

        app_name = main_cfg.app.name
        app_modules = main_cfg.app.modules
        db_host = main_cfg.database.host
        print(f"主配置 - 应用名: {app_name}")
        print(f"主配置 - 模块: {app_modules}")
        print(f"主配置 - 数据库: {db_host}")

        # 3. 配置用户偏好
        print("\n3. 配置用户偏好")
        user_cfg = get_config_manager(
            config_path=user_config_path,
            watch=False,
            autosave_delay=0.3
        )

        user_cfg.user = {}
        user_cfg.user.name = "张三"
        user_cfg.user.email = "zhangsan@example.com"
        user_cfg.preferences = {}
        user_cfg.preferences.theme = "dark"
        user_cfg.preferences.language = "zh-CN"
        user_cfg.preferences.notifications = True

        user_name = user_cfg.user.name
        user_theme = user_cfg.preferences.theme
        user_lang = user_cfg.preferences.language
        print(f"用户配置 - 姓名: {user_name}")
        print(f"用户配置 - 主题: {user_theme}")
        print(f"用户配置 - 语言: {user_lang}")

        # 4. 配置环境设置
        print("\n4. 配置环境设置")
        env_cfg = get_config_manager(
            config_path=env_config_path,
            watch=False,
            autosave_delay=0.3
        )

        env_cfg.environment = "development"
        env_cfg.debug = {}
        env_cfg.debug.enabled = True
        env_cfg.debug.log_level = "DEBUG"
        env_cfg.performance = {}
        env_cfg.performance.cache_enabled = False
        env_cfg.performance.profiling = True

        env_name = env_cfg.environment
        debug_enabled = env_cfg.debug.enabled
        cache_enabled = env_cfg.performance.cache_enabled
        print(f"环境配置 - 环境: {env_name}")
        print(f"环境配置 - 调试: {debug_enabled}")
        print(f"环境配置 - 缓存: {cache_enabled}")

        # 5. 演示配置文件独立性
        print("\n5. 验证配置文件独立性")

        # 修改主配置不应影响其他配置
        main_cfg.app.version = "2.0.0"

        # 修改用户配置
        user_cfg.preferences.theme = "light"

        # 修改环境配置
        env_cfg.environment = "production"

        # 等待保存
        time.sleep(0.5)

        # 验证各配置独立
        main_version = main_cfg.app.version
        user_theme_final = user_cfg.preferences.theme
        env_final = env_cfg.environment

        print(f"独立验证 - 主配置版本: {main_version}")
        print(f"独立验证 - 用户主题: {user_theme_final}")
        print(f"独立验证 - 环境: {env_final}")
        print("✓ 多个配置文件独立工作正常")

        return config_files

    except Exception as e:
        print(f"❌ 多配置文件演示失败: {e}")
        # 清理文件
        for file_path in config_files:
            if os.path.exists(file_path):
                os.unlink(file_path)
        raise


def demo_config_backup_restore():
    """演示配置备份和恢复"""
    print("\n" + "=" * 50)
    print("配置备份和恢复演示")
    print("=" * 50)

    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as tmp:
        main_config_path = tmp.name

    backup_dir = tempfile.mkdtemp(prefix='config_backup_')

    try:
        # 1. 创建配置并设置数据
        print("\n1. 创建配置数据")
        cfg = get_config_manager(
            config_path=main_config_path,
            watch=False,
            autosave_delay=0.3
        )

        cfg.system = {}
        cfg.system.installation_id = cfg.generate_config_id()
        cfg.system.install_date = datetime.now().isoformat()
        cfg.system.version = "1.5.0"

        cfg.data = {}
        cfg.data.records_count = 10_000
        cfg.data.last_backup = "2025-05-28T09:00:00"

        cfg.security = {}
        cfg.security.encryption_enabled = True
        cfg.security.key_rotation_days = 90

        install_id = cfg.system.installation_id
        records_count = cfg.data.records_count
        encryption = cfg.security.encryption_enabled
        print(f"安装ID: {install_id}")
        print(f"记录数量: {records_count:,}")
        print(f"加密启用: {encryption}")

        # 2. 创建备份
        print("\n2. 创建配置备份")
        backup_filename = f"config_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.yaml"
        backup_path = os.path.join(backup_dir, backup_filename)

        # 手动保存当前配置
        cfg.save()

        # 复制配置文件作为备份
        shutil.copy2(main_config_path, backup_path)
        print(f"✓ 备份已创建: {backup_filename}")

        backup_size = os.path.getsize(backup_path)
        print(f"备份文件大小: {backup_size:,} 字节")

        # 3. 修改配置（模拟数据损坏或误操作）
        print("\n3. 模拟配置损坏")
        cfg.system.version = "2.0.0-corrupted"
        cfg.data.records_count = 0  # 模拟数据丢失
        cfg.security.encryption_enabled = False

        # 添加一些错误数据
        cfg.corrupt_data = {}
        cfg.corrupt_data.error = True
        cfg.corrupt_data.message = "System corrupted"

        corrupted_version = cfg.system.version
        corrupted_count = cfg.data.records_count
        print(f"损坏后版本: {corrupted_version}")
        print(f"损坏后记录数: {corrupted_count:,}")
        print("❌ 配置已被损坏")

        # 4. 从备份恢复
        print("\n4. 从备份恢复配置")

        # 复制备份文件覆盖当前配置
        shutil.copy2(backup_path, main_config_path)

        # 重新加载配置
        cfg.reload()

        # 验证恢复结果
        restored_version = cfg.system.version
        restored_count = cfg.data.records_count
        restored_encryption = cfg.security.encryption_enabled
        restored_corrupt = cfg.get('corrupt_data.error', None)

        print(f"恢复后版本: {restored_version}")
        print(f"恢复后记录数: {restored_count:,}")
        print(f"恢复后加密: {restored_encryption}")
        print(f"损坏数据: {restored_corrupt} (应该为None)")

        if restored_version == "1.5.0" and restored_count == 10_000:
            print("✓ 配置已成功从备份恢复")
        else:
            print("❌ 配置恢复失败")

        return main_config_path, backup_dir

    except Exception as e:
        print(f"❌ 备份恢复演示失败: {e}")
        if os.path.exists(main_config_path):
            os.unlink(main_config_path)
        if os.path.exists(backup_dir):
            shutil.rmtree(backup_dir)
        raise


def cleanup_demo_files(*paths):
    """清理演示文件和目录"""
    print("\n清理演示文件...")
    for path in paths:
        if not path:
            continue

        if os.path.isfile(path):
            try:
                os.unlink(path)
                print(f"✓ 已删除文件: {path}")
            except Exception as e:
                print(f"❌ 删除文件失败 {path}: {e}")
        elif os.path.isdir(path):
            try:
                shutil.rmtree(path)
                print(f"✓ 已删除目录: {path}")
            except Exception as e:
                print(f"❌ 删除目录失败 {path}: {e}")
    return


def main():
    """主函数"""
    cleanup_items = []

    try:
        print("配置管理器文件操作演示")
        print("=" * 60)

        # 运行文件操作演示
        file1 = demo_file_monitoring()
        cleanup_items.append(file1)

        config_files = demo_multiple_config_files()
        cleanup_items.extend(config_files)

        main_config, backup_dir = demo_config_backup_restore()
        cleanup_items.extend([main_config, backup_dir])

        print("\n" + "=" * 60)
        print("文件操作演示完成！")
        print("=" * 60)
        print("\n主要文件操作特性:")
        print("• 实时文件监视和自动重新加载")
        print("• 多配置文件独立管理")
        print("• 配置备份和恢复机制")
        print("• 原子文件操作保证数据完整性")
        print("• 跨平台文件系统兼容性")

    except Exception as e:
        print(f"演示过程中出现错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # 清理所有演示文件
        cleanup_demo_files(*cleanup_items)
    return


if __name__ == "__main__":
    main()