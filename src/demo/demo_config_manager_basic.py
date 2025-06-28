# src/demo/demo_config_manager_basic.py
from __future__ import annotations
from datetime import datetime

start_time = datetime.now()

import os
from pathlib import Path
from config_manager import get_config_manager


def demo_basic_operations():
    """演示基本配置操作"""
    print("配置管理器基本操作演示")
    print("=" * 50)

    # 1. 初始化配置管理器
    print("\n1. 初始化配置管理器")
    cfg = get_config_manager()
    config_path = cfg.get_config_path()
    print(f"配置文件路径: {config_path}")

    # 2. 基本属性设置和获取
    print("\n2. 基本属性设置和获取")
    cfg.app_name = "MyAwesomeApp"
    cfg.app_version = "1.0.0"
    cfg.debug_mode = False

    app_name = cfg.app_name
    app_version = cfg.app_version
    debug_mode = cfg.debug_mode
    print(f"应用名称: {app_name}")
    print(f"应用版本: {app_version}")
    print(f"调试模式: {debug_mode}")

    # 3. 嵌套配置结构
    print("\n3. 嵌套配置结构")
    cfg.database = {}
    cfg.database.host = "db.example.com"
    cfg.database.port = 5_432
    cfg.database.credentials = {}
    cfg.database.credentials.username = "admin"

    # 使用环境变量设置密码
    db_password = os.getenv("DB_PASSWORD", "default_password")
    cfg.database.credentials.password = db_password

    db_host = cfg.database.host
    db_port = cfg.database.port
    db_username = cfg.database.credentials.username
    print(f"数据库主机: {db_host}")
    print(f"数据库端口: {db_port:,}")
    print(f"数据库用户: {db_username}")

    # 4. 使用get方法安全访问
    print("\n4. 使用get方法安全访问")
    timeout = cfg.get("database.timeout", default=30)
    max_connections = cfg.get("database.max_connections", default=100)
    print(f"连接超时: {timeout}秒")
    print(f"最大连接数: {max_connections:,}")

    return cfg


def demo_type_support():
    """演示类型支持功能"""
    print("\n" + "=" * 50)
    print("类型支持演示")
    print("=" * 50)

    cfg = get_config_manager()

    # 1. 路径类型支持
    print("\n1. 路径类型支持")
    log_path = Path("/var/log/myapp")
    cfg.set("logging.path", log_path, type_hint=Path)

    # 获取路径值
    log_dir = cfg.get_path("logging.path")
    log_dir_type = type(log_dir)
    print(f"日志目录: {log_dir}")
    print(f"日志目录类型: {log_dir_type}")

    # 2. 类型转换
    print("\n2. 类型转换")
    cfg.set("server.port", "8080", type_hint=int)
    cfg.set("server.timeout", "30.5", type_hint=float)

    server_port = cfg.get("server.port", as_type=int)
    server_timeout = cfg.get("server.timeout", as_type=float)
    print(f"服务器端口: {server_port:,} (类型: {type(server_port).__name__})")
    print(f"服务器超时: {server_timeout} (类型: {type(server_timeout).__name__})")

    # 3. 类型提示查询
    print("\n3. 类型提示查询")
    port_hint = cfg.get_type_hint("server.port")
    timeout_hint = cfg.get_type_hint("server.timeout")
    path_hint = cfg.get_type_hint("logging.path")
    print(f"端口类型提示: {port_hint}")
    print(f"超时类型提示: {timeout_hint}")
    print(f"路径类型提示: {path_hint}")

    return cfg


def demo_batch_operations():
    """演示批量操作"""
    print("\n" + "=" * 50)
    print("批量操作演示")
    print("=" * 50)

    cfg = get_config_manager()

    # 1. 批量更新配置
    print("\n1. 批量更新配置")
    cfg.update({
        "app_version": "1.1.0",
        "database.port": 6_432,
        "logging.level": "INFO",
        "features.new_ui": True,
        "features.experimental": False
    })

    updated_version = cfg.app_version
    updated_port = cfg.database.port
    log_level = cfg.logging.level
    new_ui = cfg.features.new_ui
    print(f"更新后的应用版本: {updated_version}")
    print(f"更新后的数据库端口: {updated_port:,}")
    print(f"日志级别: {log_level}")
    print(f"新UI功能: {new_ui}")

    # 2. 复杂嵌套结构批量设置
    print("\n2. 复杂嵌套结构批量设置")
    cfg.update({
        "api": {
            "endpoints": {
                "users": "/api/v1/users",
                "orders": "/api/v1/orders",
                "products": "/api/v1/products"
            },
            "rate_limits": {
                "requests_per_minute": 1_000,
                "burst_limit": 50
            },
            "authentication": {
                "method": "jwt",
                "token_expiry": 3_600
            }
        }
    })

    users_endpoint = cfg.api.endpoints.users
    rate_limit = cfg.api.rate_limits.requests_per_minute
    auth_method = cfg.api.authentication.method
    print(f"用户端点: {users_endpoint}")
    print(f"速率限制: {rate_limit:,} 请求/分钟")
    print(f"认证方法: {auth_method}")

    return cfg


def main():
    """主函数"""
    try:
        # 运行基本操作演示
        cfg = demo_basic_operations()

        # 运行类型支持演示
        demo_type_support()

        # 运行批量操作演示
        demo_batch_operations()

        # 6. 保存和重新加载演示
        print("\n" + "=" * 50)
        print("保存和重新加载演示")
        print("=" * 50)

        print("\n保存配置...")
        saved = cfg.save()
        print(f"保存结果: {saved}")

        print("\n重新加载配置...")
        reloaded = cfg.reload()
        print(f"重新加载结果: {reloaded}")
        print("配置已重新加载，所有设置保持完整")

        print("\n" + "=" * 50)
        print("基本功能演示完成！")
        print("=" * 50)

    except Exception as e:
        print(f"演示过程中出现错误: {e}")
        import traceback
        traceback.print_exc()
    return


if __name__ == "__main__":
    main()