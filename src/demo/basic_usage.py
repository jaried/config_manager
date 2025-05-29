# src/demo/basic_usage.py
from __future__ import annotations
from datetime import datetime

start_time = datetime.now()

import os
from pathlib import Path
from config_manager import get_config_manager


def main():
    print("配置管理器基本使用示例")
    print("=" * 50)

    # 1. 初始化配置管理器（使用默认路径）
    print("\n1. 初始化配置管理器")
    cfg = get_config_manager()
    print(f"配置文件路径: {cfg.get_config_path()}")

    # 2. 设置基本配置
    print("\n2. 设置基本配置")
    cfg.app_name = "MyAwesomeApp"
    cfg.app_version = "1.0.0"
    cfg.debug_mode = False

    print(f"应用名称: {cfg.app_name}")
    print(f"应用版本: {cfg.app_version}")
    print(f"调试模式: {cfg.debug_mode}")

    # 3. 设置嵌套配置
    print("\n3. 设置嵌套配置")
    cfg.database = {}
    cfg.database.host = "db.example.com"
    cfg.database.port = 5432
    cfg.database.credentials = {}
    cfg.database.credentials.username = "admin"

    # 使用环境变量设置密码
    db_password = os.getenv("DB_PASSWORD", "default_password")
    cfg.database.credentials.password = db_password

    print(f"数据库主机: {cfg.database.host}")
    print(f"数据库端口: {cfg.database.port}")
    print(f"数据库用户: {cfg.database.credentials.username}")

    # 4. 使用路径类型
    print("\n4. 使用路径类型")
    log_path = Path("/var/log/myapp")
    cfg.set("logging.path", log_path, type_hint=Path)

    # 获取路径值
    log_dir = cfg.get_path("logging.path")
    print(f"日志目录: {log_dir}")
    print(f"日志目录类型: {type(log_dir)}")

    # 5. 批量更新配置
    print("\n5. 批量更新配置")
    cfg.update({
        "app_version": "1.1.0",
        "database.port": 6432,
        "logging.level": "INFO"
    })

    print(f"更新后的应用版本: {cfg.app_version}")
    print(f"更新后的数据库端口: {cfg.database.port}")

    # 6. 重新加载配置
    print("\n6. 重新加载配置")
    cfg.reload()
    print("配置已重新加载")

    print("\n基本使用示例完成！")
    return


if __name__ == "__main__":
    main()