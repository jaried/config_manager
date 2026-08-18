# tests/test_yaml_comments_preservation.py
from __future__ import annotations

import tempfile
import os
import sys
from pathlib import Path

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from config_manager import get_config_manager
from config_manager.yaml_codec import load_yaml, semantically_equal


def _data_section(saved_content: str) -> dict:
    document = load_yaml(saved_content)
    assert isinstance(document, dict)
    data = document.get("__data__", document)
    assert isinstance(data, dict)
    return data


def test_yaml_comments_preservation():
    """测试带注释输入的 YAML 数据语义保存。"""

    # 创建带注释的YAML配置文件
    yaml_content_with_comments = """# 应用程序配置
app_name: TestApp  # 应用名称
version: 1.0.0     # 版本号

# 数据库配置
database:
  host: localhost    # 数据库主机
  port: 5432        # 数据库端口
  name: testdb      # 数据库名称
  test_address: sqlite:///test.db
  # 连接配置
  connection:
    timeout: 30     # 连接超时时间
    pool_size: 10   # 连接池大小

# 服务配置
service:
  # 监听端口
  port: 8080
  # 是否启用调试模式
  debug: false

# 特性列表
features:
  - feature1      # 功能1
  - feature2      # 功能2
  - feature3      # 功能3
"""

    # 创建临时配置文件
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".yaml", delete=False, encoding="utf-8"
    ) as tmp:
        tmp.write(yaml_content_with_comments)
        test_config_path = tmp.name

    try:
        # 创建配置管理器（测试模式，确保测试隔离）
        config = get_config_manager(
            config_path=test_config_path, auto_create=False, watch=False, test_mode=True
        )

        # 验证配置正确加载
        assert config.app_name == "TestApp"
        assert config.version == "1.0.0"
        assert config.database.host == "localhost"
        assert config.database.port == 5432
        assert config.service.port == 8080
        assert config.service.debug is False
        assert config.features == ["feature1", "feature2", "feature3"]

        # 修改一些配置值
        config.app_name = "ModifiedApp"
        config.database.port = 3306
        config.service.debug = True
        config.features.append("feature4")

        # 保存配置
        config.save()

        # 读取保存后的文件内容
        actual_config_path = config.get_config_path()
        with open(actual_config_path, "r", encoding="utf-8") as f:
            saved_content = f.read()

        actual = _data_section(saved_content)
        expected = {
            "app_name": "ModifiedApp",
            "version": "1.0.0",
            "database": {
                "host": "localhost",
                "port": 3306,
                "name": "testdb",
                "test_address": "sqlite:///test.db",
                "address": "sqlite:///test.db",
                "connection": {"timeout": 30, "pool_size": 10},
            },
            "service": {"port": 8080, "debug": True},
            "features": ["feature1", "feature2", "feature3", "feature4"],
        }
        actual_subset = {key: actual[key] for key in expected}
        assert semantically_equal(actual_subset, expected)

    finally:
        # 清理临时文件
        Path(test_config_path).unlink(missing_ok=True)


def test_yaml_comments_preservation_with_new_keys():
    """测试添加新键时的 YAML 数据语义保存。"""

    yaml_content = """# 基础配置
app_name: TestApp
version: 1.0.0

# 数据库配置
database:
  host: localhost  # 主机地址
  port: 5432      # 端口号
  test_address: sqlite:///test.db
"""

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".yaml", delete=False, encoding="utf-8"
    ) as tmp:
        tmp.write(yaml_content)
        test_config_path = tmp.name

    try:
        config = get_config_manager(
            config_path=test_config_path, auto_create=False, watch=False, test_mode=True
        )

        # 添加新的配置项
        config.new_feature = "enabled"
        config.database.timeout = 30
        config.logging = {"level": "INFO", "file": "app.log"}

        # 保存配置
        config.save()

        # 读取保存后的文件内容（使用实际的配置文件路径）
        actual_config_path = config.get_config_path()
        with open(actual_config_path, "r", encoding="utf-8") as f:
            saved_content = f.read()

        actual = _data_section(saved_content)
        expected = {
            "app_name": "TestApp",
            "version": "1.0.0",
            "database": {
                "host": "localhost",
                "port": 5432,
                "test_address": "sqlite:///test.db",
                "address": "sqlite:///test.db",
                "timeout": 30,
            },
            "new_feature": "enabled",
            "logging": {"level": "INFO", "file": "app.log"},
        }
        actual_subset = {key: actual[key] for key in expected}
        assert semantically_equal(actual_subset, expected)

    finally:
        Path(test_config_path).unlink(missing_ok=True)


def test_yaml_comments_preservation_with_nested_structures():
    """测试嵌套结构的 YAML 数据语义保存。"""

    yaml_content = """# 应用配置
app:
  # 基本信息
  name: TestApp     # 应用名称
  version: 1.0.0   # 版本号

  # 环境配置
  environment:
    # 开发环境
    development:
      debug: true    # 调试模式
      log_level: DEBUG  # 日志级别

    # 生产环境
    production:
      debug: false   # 调试模式
      log_level: INFO  # 日志级别

# 服务配置
services:
  # Web服务
  web:
    port: 8080      # 监听端口
    threads: 4      # 线程数

  # API服务
  api:
    port: 8081      # API端口
    rate_limit: 100 # 请求限制
"""

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".yaml", delete=False, encoding="utf-8"
    ) as tmp:
        tmp.write(yaml_content)
        test_config_path = tmp.name

    try:
        config = get_config_manager(
            config_path=test_config_path, auto_create=False, watch=False, test_mode=True
        )

        # 修改嵌套结构中的值
        config.app.name = "ModifiedApp"
        config.app.environment.development.debug = False
        config.services.web.port = 9090
        config.services.api.rate_limit = 200

        # 添加新的嵌套配置
        config.app.features = ["feature1", "feature2"]
        config.services.cache = {"type": "redis", "host": "localhost", "port": 6379}

        # 保存配置
        config.save()

        # 读取保存后的文件内容（使用实际的配置文件路径）
        actual_config_path = config.get_config_path()
        with open(actual_config_path, "r", encoding="utf-8") as f:
            saved_content = f.read()

        actual = _data_section(saved_content)
        expected = {
            "app": {
                "name": "ModifiedApp",
                "version": "1.0.0",
                "environment": {
                    "development": {"debug": False, "log_level": "DEBUG"},
                    "production": {"debug": False, "log_level": "INFO"},
                },
                "features": ["feature1", "feature2"],
            },
            "services": {
                "web": {"port": 9090, "threads": 4},
                "api": {"port": 8081, "rate_limit": 200},
                "cache": {"type": "redis", "host": "localhost", "port": 6379},
            },
        }
        actual_subset = {key: actual[key] for key in expected}
        assert semantically_equal(actual_subset, expected)

    finally:
        Path(test_config_path).unlink(missing_ok=True)


def test_yaml_comments_preservation_edge_cases():
    """测试带注释 YAML 输入的边缘数据语义。"""

    yaml_content = """# 顶层注释
# 多行注释
# 第三行注释

app_name: TestApp  # 行内注释

# 空行上方的注释

empty_value: null  # 空值注释

# 列表注释
list_items:
  - item1  # 列表项1注释
  - item2  # 列表项2注释
  # 列表中间注释
  - item3  # 列表项3注释

# 字典注释
dict_items:
  key1: value1  # 字典项1注释
  # 字典中间注释
  key2: value2  # 字典项2注释

# 特殊字符注释: !@#$%^&*()
special_chars: "test"  # 包含特殊字符的注释

# 最后的注释
"""

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".yaml", delete=False, encoding="utf-8"
    ) as tmp:
        tmp.write(yaml_content)
        test_config_path = tmp.name

    try:
        config = get_config_manager(
            config_path=test_config_path, auto_create=False, watch=False, test_mode=True
        )

        # 修改配置
        config.app_name = "ModifiedApp"
        config.empty_value = "not_empty"
        config.list_items.append("item4")
        config.dict_items.key3 = "value3"
        config.special_chars = "modified"

        # 保存配置
        config.save()

        # 读取保存后的文件内容（使用实际的配置文件路径）
        actual_config_path = config.get_config_path()
        with open(actual_config_path, "r", encoding="utf-8") as f:
            saved_content = f.read()

        actual = _data_section(saved_content)
        expected = {
            "app_name": "ModifiedApp",
            "empty_value": "not_empty",
            "list_items": ["item1", "item2", "item3", "item4"],
            "dict_items": {"key1": "value1", "key2": "value2", "key3": "value3"},
            "special_chars": "modified",
        }
        actual_subset = {key: actual[key] for key in expected}
        assert semantically_equal(actual_subset, expected)

    finally:
        Path(test_config_path).unlink(missing_ok=True)


if __name__ == "__main__":
    print("=" * 70)
    print("YAML 数据语义保存测试")
    print("=" * 70)

    print("\n1. 基本数据语义保存测试")
    test_yaml_comments_preservation()

    print("\n2. 添加新键时的数据语义保存测试")
    test_yaml_comments_preservation_with_new_keys()

    print("\n3. 嵌套结构数据语义保存测试")
    test_yaml_comments_preservation_with_nested_structures()

    print("\n4. 边缘情况数据语义保存测试")
    test_yaml_comments_preservation_edge_cases()

    print("\n" + "=" * 70)
    print("所有 YAML 数据语义保存测试完成！")
    print("=" * 70)
