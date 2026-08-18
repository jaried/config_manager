# 配置管理器 (Config Manager)

一个强大、易用的 Python 配置管理库，支持自动保存、类型提示、文件监视、**YAML注释保留**、**测试模式**等高级功能。

## 目录

- [特性](#特性)
- [安装](#安装)
- [快速开始](#快速开始)
- [进阶使用](#进阶使用)
- [高级功能](#高级功能)
  - [自动路径配置管理](#4-自动路径配置管理) 🏗️
  - [配置文件注释管理](#6-配置文件注释管理) 💬
- [配置文件格式](#配置文件格式)
  - [YAML注释保留功能](#yaml注释保留功能) 💬
- [测试中的配置管理](#测试中的配置管理)
  - [测试模式功能](#测试模式功能) 🧪
  - [测试环境管理](#测试环境管理)
- [完整示例](#完整示例)
- [常见问题](#常见问题)

## 特性

- 🚀 **简单易用**：直观的点操作语法访问配置项
- 💾 **自动保存**：配置变更时自动保存到文件
- 🔒 **线程安全**：支持多线程环境安全使用
- 🎯 **类型安全**：完整的类型提示支持
- 📁 **文件监视**：实时监控配置文件变化并自动重载
- 🔄 **快照恢复**：便捷的配置状态保存和恢复
- 📍 **路径感知**：配置对象知道自己的配置文件路径
- 💬 **注释保留**：完美保留YAML配置文件中的注释和格式
- 📄 **多格式支持**：支持标准格式和原始YAML格式，自动识别
- 🧪 **测试模式**：一键创建隔离的测试环境，智能路径替换，简化测试代码编写
- 🏗️ **自动路径管理**：智能生成项目目录结构，支持调试模式和时间戳，自动创建所需目录
- ⚡ **高性能**：优化的内存和 I/O 操作
- 🌐 **跨平台**：支持 Windows、Linux、macOS

## 安装

从源代码仓库安装：

```bash
git clone https://github.com/jaried/config_manager.git
cd config_manager
pip install -e .
```

### 依赖要求

- Python 3.8+
- ruamel.yaml (用于YAML注释保留)
- pytest (用于测试)

## API 参考

### get_config_manager() 函数

配置管理器的主要入口函数，用于获取配置管理器实例。

```python
def get_config_manager(
    config_path: str = None,
    watch: bool = False,
    auto_create: bool = False,
    autosave_delay: float = None,
    first_start_time: datetime = None,
    test_mode: bool = False
) -> ConfigManager:
```

#### 参数说明

| 参数  | 类型  | 默认值 | 是否必需 | 说明  |
| --- | --- | --- | --- | --- |
| `config_path` | `str` | `None` | 否   | 配置文件路径。如果为 `None`，会自动查找项目根目录并使用 `src/config/config.yaml` |
| `watch` | `bool` | `False` | 否   | 是否启用文件监视。为 `True` 时会监控配置文件变化并自动重载 |
| `auto_create` | `bool` | `False` | 否   | 配置文件不存在时是否自动创建。为 `True` 时会在指定路径创建新的配置文件 |
| `autosave_delay` | `float` | `None` | 否   | 自动保存延迟时间（秒）。配置修改后延迟指定时间再保存，避免频繁 I/O |
| `first_start_time` | `datetime` | `None` | 主程序需要 | 应用首次启动时间。**主程序调用时必须提供**，用于记录启动时间和生成备份文件时间戳 |
| `test_mode` | `bool` | `False` | 否   | 是否启用测试模式。为 `True` 时创建隔离的测试环境，自动生成临时路径 |

#### 返回值

返回 `ConfigManager` 实例，提供配置管理的所有功能。

## 快速开始

### 1. 最简单的使用

```python
from config_manager import get_config_manager
from datetime import datetime

# 主程序中必须传递启动时间
start_time = datetime.now()
cfg = get_config_manager(first_start_time=start_time)

# 设置配置
cfg.app_name = "我的应用"
cfg.version = "1.0.0"

# 读取配置
print(f"应用名称: {cfg.app_name}")
print(f"版本号: {cfg.version}")
```

### 2. 库/模块调用（不需要 first_start_time）

```python
from config_manager import get_config_manager

# 在库或子模块中可以不传递 first_start_time
def some_library_function():
    cfg = get_config_manager()  # 使用默认参数
    return cfg.some_setting
```

### 3. 嵌套配置

```python
from datetime import datetime

# 主程序中使用
start_time = datetime.now()
cfg = get_config_manager(first_start_time=start_time)

# 设置嵌套配置
cfg.database = {}
cfg.database.host = "localhost"
cfg.database.port = 5432
cfg.database.username = "admin"

# 读取嵌套配置
print(f"数据库地址: {cfg.database.host}:{cfg.database.port}")
print(f"用户名: {cfg.database.username}")
```

### 4. 批量设置配置

```python
from datetime import datetime

start_time = datetime.now()
cfg = get_config_manager(first_start_time=start_time)

# 使用 update 方法批量设置
cfg.update({
    "app_name": "新应用名称",
    "database": {
        "host": "192.168.1.100",
        "port": 3306,
        "ssl": True
    },
    "features": {
        "cache_enabled": True,
        "debug_mode": False
    }
})
```

## 进阶使用

### 1. 主程序完整初始化

```python
from datetime import datetime

# 主程序中的完整初始化
start_time = datetime.now()

cfg = get_config_manager(
    config_path="./config/my_config.yaml",
    auto_create=True,  # 文件不存在时自动创建
    watch=True,        # 启用文件监视
    autosave_delay=1.0,  # 1秒自动保存延迟
    first_start_time=start_time  # 主程序必须提供
)
```

### 2. 子模块中的简单使用

```python
# 在子模块、工具函数或库代码中
def get_database_config():
    cfg = get_config_manager()  # 不需要 first_start_time
    return {
        'host': cfg.database.host,
        'port': cfg.database.port,
        'username': cfg.database.username
    }
```

### 3. 启用文件监视

```python
from datetime import datetime

start_time = datetime.now()

# 启用文件监视，当配置文件被外部修改时自动重载
cfg = get_config_manager(
    watch=True,  # 启用文件监视
    autosave_delay=0.5,  # 设置自动保存延迟（秒）
    first_start_time=start_time  # 主程序中必须提供
)

# 现在当你用其他程序修改配置文件时，配置会自动重载
```

### 4. 完整参数示例

```python
from datetime import datetime

start_time = datetime.now()

# 使用所有参数的完整示例（主程序）
cfg = get_config_manager(
    config_path="./data/production_config.yaml",  # 自定义配置文件路径
    watch=True,                                   # 启用文件监视
    auto_create=True,                            # 文件不存在时自动创建
    autosave_delay=2.0,                          # 2秒自动保存延迟
    first_start_time=start_time                  # 主程序必须提供
)
```

### 5. 安全的配置访问

```python
# 可以在任何地方使用（主程序或子模块）
cfg = get_config_manager()

# 使用 get 方法安全访问，提供默认值
timeout = cfg.get("database.timeout", default=30)
max_connections = cfg.get("database.max_connections", default=100)

# 指定类型转换
port = cfg.get("server.port", default="8080", as_type=int)
```

### 6. 类型提示和转换

```python
from pathlib import Path

cfg = get_config_manager()

# 设置类型提示
cfg.set("log_directory", "/var/log/myapp", type_hint=Path)
cfg.set("server.port", "8080", type_hint=int)
cfg.set("server.timeout", "30.5", type_hint=float)

# 获取带类型转换的值
log_dir = cfg.get_path("log_directory")  # 返回 Path 对象
port = cfg.get("server.port", as_type=int)  # 返回 int 类型
```

## 高级功能

### 1. 配置快照和恢复

```python
cfg = get_config_manager()

# 创建配置快照
snapshot = cfg.snapshot()

# 修改配置
cfg.database.host = "new-host"
cfg.app_name = "修改后的名称"

# 从快照恢复配置
cfg.restore(snapshot)
print(cfg.database.host)  # 恢复到原来的值
```

### 2. 临时配置上下文

```python
cfg = get_config_manager()

# 使用临时配置，退出上下文后自动恢复
with cfg.temporary({
    "debug_mode": True,
    "database.timeout": 5,
    "logging.level": "DEBUG"
}) as temp_cfg:
    # 在这个上下文中使用临时配置
    print(f"调试模式: {temp_cfg.debug_mode}")  # True
    # 执行需要调试配置的代码...

# 退出上下文后配置自动恢复
print(f"调试模式: {cfg.debug_mode}")  # 原来的值
```

### 3. 配置文件路径访问

```python
cfg = get_config_manager(config_path="/path/to/config.yaml")

# 获取配置文件的绝对路径
config_path = cfg.get_config_file_path()
print(f"配置文件路径: {config_path}")

# 也可以直接从配置数据中访问
config_path = cfg.config_file_path

# 基于配置文件路径创建相关目录
import os
config_dir = os.path.dirname(config_path)
log_dir = os.path.join(config_dir, "logs")
data_dir = os.path.join(config_dir, "data")

os.makedirs(log_dir, exist_ok=True)
os.makedirs(data_dir, exist_ok=True)

# 将路径信息保存到配置中
cfg.paths = {}
cfg.paths.config_file = config_path
cfg.paths.config_dir = config_dir
cfg.paths.log_dir = log_dir
cfg.paths.data_dir = data_dir

# 访问路径配置（推荐方式）
print(f"配置目录: {cfg.paths.config_dir}")
print(f"日志目录: {cfg.paths.log_dir}")
print(f"数据目录: {cfg.paths.data_dir}")
```

### 4. 自动路径配置管理

配置管理器提供强大的路径配置功能，能够自动生成和管理项目所需的各种目录路径：

```python
from datetime import datetime

# 主程序中初始化配置管理器
start_time = datetime.now()
cfg = get_config_manager(
    config_path="./config/project_config.yaml",
    auto_create=True,
    first_start_time=start_time
)

# 设置基础路径配置
cfg.base_dir = "d:/logs"
cfg.project_name = "my_project"
cfg.experiment_name = "experiment_001"
cfg.debug_mode = False

# 路径配置会自动生成，通过 config.paths.xxx 访问
print(f"工作目录: {cfg.paths.work_dir}")           # d:/logs/my_project/experiment_001
print(f"检查点目录: {cfg.paths.checkpoint_dir}")    # d:/logs/my_project/experiment_001/checkpoint
print(f"最佳检查点: {cfg.paths.best_checkpoint_dir}") # d:/logs/my_project/experiment_001/checkpoint/best
print(f"调试目录: {cfg.paths.debug_dir}")          # d:/logs/my_project/experiment_001/debug
print(f"日志目录: {cfg.paths.log_dir}")           # d:/logs/my_project/experiment_001/logs/2025-01-08/103000
print(f"TensorBoard: {cfg.paths.tsb_logs_dir}")   # d:/logs/my_project/experiment_001/tsb_logs/2025-01-08/103000

# 所有目录会自动创建，无需手动处理
```

**路径配置特性：**

- 🏗️ **自动生成**：基于项目名称、实验名称自动生成标准化目录结构
- 📁 **自动创建**：配置的所有路径目录会自动创建
- 🐛 **调试模式支持**：调试模式下会在路径中添加debug标识
- ⏰ **时间戳支持**：日志目录基于启动时间自动生成时间戳子目录
- 🎯 **标准化结构**：提供机器学习项目的标准目录结构

**路径访问方式：**

```python
# 推荐方式：通过paths命名空间访问
work_dir = cfg.paths.work_dir
log_dir = cfg.paths.log_dir
debug_dir = cfg.paths.debug_dir

# 备选方式：通过get方法访问
work_dir = cfg.get('paths.work_dir')
log_dir = cfg.get('paths.log_dir')
debug_dir = cfg.get('paths.debug_dir')
```

### 5. 生成唯一 ID

```python
cfg = get_config_manager()

# 为实验、会话等生成唯一 ID
experiment_id = cfg.generate_config_id()
cfg.experiments[experiment_id] = {
    "name": "实验A",
    "parameters": {"learning_rate": 0.01},
    "status": "running"
}
```

### 6. 配置文件注释管理

配置管理器完美支持YAML注释，让你可以在配置文件中添加详细的文档说明：

```python
# 创建带注释的配置文件
cfg = get_config_manager(config_path="./config/documented_config.yaml", auto_create=True)

# 手动创建带注释的配置文件内容
config_with_comments = """# 应用配置文件
# 版本: 1.0
# 最后更新: 2025-06-06

__data__:
  # 应用基本信息
  app_name: "我的应用"    # 应用名称，显示在标题栏
  version: "1.0.0"       # 语义化版本号

  # 数据库连接配置
  database:
    host: "localhost"    # 数据库服务器地址
    port: 5432          # PostgreSQL默认端口
    name: "myapp_db"    # 数据库名称
    timeout: 30         # 连接超时时间（秒）

  # 性能调优参数
  performance:
    max_workers: 4      # 最大工作线程数
    cache_size: 1000    # 缓存大小（条目数）
    batch_size: 100     # 批处理大小

  # 功能开关
  features:
    enable_cache: true   # 启用缓存功能
    debug_mode: false   # 调试模式（生产环境请关闭）
    log_sql: false      # 是否记录SQL语句

__type_hints__:
  database.port: int
  database.timeout: int
  performance.max_workers: int

# 配置文件说明：
# 1. 修改配置后会自动保存
# 2. 所有注释都会被保留
# 3. 支持嵌套配置结构
"""

# 将带注释的内容写入文件
with open("./config/documented_config.yaml", "w", encoding="utf-8") as f:
    f.write(config_with_comments)

# 现在通过配置管理器修改配置
cfg = get_config_manager(config_path="./config/documented_config.yaml")
cfg.app_name = "更新后的应用名"
cfg.database.host = "production-server"
cfg.new_setting = "新增的配置项"

# 保存后，所有注释都会被完美保留！
cfg.save()

print("配置已更新，注释完整保留！")
```

**注释保留的优势：**

- 📝 **文档化配置**：直接在配置文件中编写说明文档
- 🔧 **运维友好**：运维人员可以直接查看配置说明
- 📚 **知识传承**：配置的历史和用途得以保留
- 🎯 **减少错误**：清晰的注释减少配置错误
- 🔄 **版本控制友好**：Git等版本控制工具能更好地跟踪变化

## 测试中的配置管理

在测试用例中，经常需要临时修改配置以测试不同的场景。配置管理器提供了**测试模式**和多种传统方法来安全地进行测试配置管理。

## 测试模式功能 🧪

### 一键测试环境

**测试模式**是配置管理器v2.0的重要新功能，通过一个参数即可创建完全隔离的测试环境：

```python
from config_manager import get_config_manager

def test_my_feature():
    # 一行代码创建隔离的测试环境
    cfg = get_config_manager(test_mode=True)

    # 测试逻辑 - 完全隔离，不影响生产环境
    cfg.test_setting = "test_value"
    cfg.debug_mode = True

    # 执行测试
    assert cfg.test_setting == "test_value"

    # 测试结束后自动清理，无需手动处理
```

### 核心特性

- 🔒 **完全隔离**：测试和生产环境完全分离，避免数据污染
- 🚀 **一键启用**：只需设置 `test_mode=True`
- 📁 **自动路径**：基于时间戳自动生成唯一测试路径
- 📋 **配置复制**：自动从生产环境复制配置到测试环境
- 🛠️ **智能路径替换**：自动识别并替换配置中的所有路径字段为测试环境路径
- 🔄 **时间保留**：保留原配置中的first_start_time，确保时间一致性
- 💾 **备份隔离**：自动备份功能完全隔离到测试环境
- 🧹 **自动清理**：测试环境自动管理，无需手动清理

### 测试路径格式

测试模式会在系统临时目录下创建唯一的测试环境：

```
{系统临时目录}/tests/{YYYYMMDD}/{HHMMSS}/src/config/config.yaml
```

例如：
```
d:\temp\tests\20250607\143052\src\config\config.yaml
```

### 使用固定时间（推荐用于测试）

```python
from datetime import datetime

def test_with_fixed_time():
    # 使用固定时间确保路径一致性
    fixed_time = datetime(2025, 6, 7, 10, 30, 0)
    cfg = get_config_manager(test_mode=True, first_start_time=fixed_time)

    # 路径将始终是: .../tests/20250607/103000/...
    config_path = cfg.get_config_file_path()
    assert "20250607" in config_path
    assert "103000" in config_path
```

### 与现有配置结合

```python
def test_with_production_config():
    # 从指定的生产配置创建测试环境
    cfg = get_config_manager(
        config_path="./config/production.yaml",
        test_mode=True
    )

    # 配置会被自动复制到测试环境
    # 所有路径字段会自动替换为测试环境路径
    # 可以安全地修改而不影响生产配置
    cfg.test_mode = True
    cfg.debug_level = "DEBUG"

    # 验证路径已被替换
    print(f"base_dir: {cfg.base_dir}")  # 输出测试环境路径
    print(f"log_dir: {cfg.paths.log_dir}")    # 输出测试环境路径
```

### 路径自动替换功能

测试模式会智能识别配置中的路径字段并自动替换：

```python
def test_path_replacement():
    # 原生产配置可能包含：
    # base_dir: "d:/logs/"
    # work_dir: "d:/logs/bakamh"
# paths.log_dir: "d:/logs/bakamh/logs"
    # data_dir: "d:/logs/bakamh/data"

    cfg = get_config_manager(test_mode=True)

    # 测试模式下，所有路径会被自动替换为：
    # base_dir: "/tmp/tests/20250607/143052"
    # work_dir: "/tmp/tests/20250607/143052"
# paths.log_dir: "/tmp/tests/20250607/143052/logs"
    # data_dir: "/tmp/tests/20250607/143052/data"

    assert cfg.base_dir.startswith("/tmp/tests/")
    assert cfg.paths.log_dir.endswith("/logs")
    assert cfg.data_dir.endswith("/data")
```

### 支持的路径字段

自动识别和替换的路径字段包括：

- **特殊字段映射**：`base_dir`、`work_dir`、`log_dir`、`data_dir`、`temp_dir`、`cache_dir`、`backup_dir`等
- **通用路径检测**：包含`dir`、`path`、`directory`、`folder`、`location`、`root`、`base`关键词的字段
- **嵌套结构**：支持配置中的嵌套字典和数组中的路径
- **路径格式**：自动识别Windows和Unix路径格式

### 备份系统隔离

测试模式下，自动备份功能也完全隔离：

```python
def test_backup_isolation():
    # 生产环境备份路径
    prod_cfg = get_config_manager()
    prod_backup = prod_cfg._get_backup_path()
    # 输出：{项目根}/src/config/backup/20250107/100000/config_20250107_100000.yaml

    # 测试环境备份路径
    test_cfg = get_config_manager(test_mode=True)
    test_backup = test_cfg._get_backup_path()
    # 输出：{临时目录}/tests/20250107/100000/src/config/backup/20250107/100000/config_20250107_100000.yaml

    # 完全不同的路径，确保隔离
    assert prod_backup != test_backup
```

## 测试环境管理

### 获取测试环境信息

```python
from config_manager.test_environment import TestEnvironmentManager

# 获取当前测试环境信息
info = TestEnvironmentManager.get_test_environment_info()
print(f"是否测试模式: {info['is_test_mode']}")
print(f"测试基础目录: {info['test_base_dir']}")
print(f"测试环境数量: {info['test_environments_count']}")
```

### 列出所有测试环境

```python
# 列出所有测试环境
environments = TestEnvironmentManager.list_test_environments()
for env in environments:
    print(f"日期: {env['date']}, 时间: {env['time']}, 大小: {env['size_formatted']}")
```

### 清理测试环境

```python
# 清理当前测试环境
TestEnvironmentManager.cleanup_current_test_environment()

# 清理指定日期的测试环境
TestEnvironmentManager.cleanup_old_test_environments(days_old=7)
```

### 测试模式 vs 传统方法对比

| 特性 | 测试模式 | 传统方法 |
|------|----------|----------|
| 环境隔离 | ✅ 完全隔离 | ⚠️ 需要手动管理 |
| 代码复杂度 | ✅ 一行代码 | ❌ 多行设置代码 |
| 路径管理 | ✅ 自动生成 | ❌ 手动指定 |
| 路径替换 | ✅ 智能识别替换 | ❌ 手动处理 |
| 配置复制 | ✅ 自动复制 | ❌ 手动处理 |
| 备份隔离 | ✅ 自动隔离 | ❌ 手动处理 |
| 时间保留 | ✅ 保留原时间 | ❌ 可能丢失 |
| 清理工作 | ✅ 自动清理 | ❌ 手动清理 |
| 并发安全 | ✅ 完全安全 | ⚠️ 可能冲突 |

## 传统测试方法

除了新的测试模式，配置管理器仍然支持传统的测试方法：

### 方法一：使用 temporary() 上下文管理器（推荐）

这是最安全和推荐的方式，确保配置在测试完成后自动恢复：

```python
# tests/01_unit_tests/test_example.py
from __future__ import annotations

import pytest
from config_manager import get_config_manager


class TestExample:
    """示例测试类"""

    def test_with_temporary_config(self):
        """使用临时配置的测试"""
        cfg = get_config_manager()

        # 获取原始值进行验证
        original_timeout = cfg.get('timeout', 30)

        # 使用临时配置上下文
        temp_changes = {
            "timeout": 10,
            "retry_count": 1,
            "test_mode": True
        }

        with cfg.temporary(temp_changes) as temp_cfg:
            # 在此上下文中，配置已被临时修改
            assert temp_cfg.timeout == 10
            assert temp_cfg.retry_count == 1
            assert temp_cfg.test_mode == True

            # 执行需要特定配置的测试逻辑
            result = some_function_that_uses_config(temp_cfg)
            assert result == expected_value

        # 退出上下文后，配置自动恢复
        assert cfg.get('timeout', 30) == original_timeout
        assert cfg.get('test_mode', None) is None
```

### 方法二：使用 pytest fixtures

对于需要在多个测试中使用相同临时配置的情况：

```python
# tests/conftest.py 或测试文件中
from __future__ import annotations

import pytest
from config_manager import get_config_manager


@pytest.fixture
def test_config():
    """提供测试专用配置的fixture"""
    cfg = get_config_manager()

    test_changes = {
        "timeout": 5,
        "retry_count": 1,
        "test_mode": True,
        "base_dir": "/tmp/test"
    }

    with cfg.temporary(test_changes) as temp_cfg:
        yield temp_cfg


class TestExample:
    """示例测试类"""

    def test_with_fixture_config(self, test_config):
        """使用fixture提供的测试配置"""
        assert test_config.timeout == 5
        assert test_config.test_mode == True

        # 执行测试逻辑
        result = function_that_uses_config(test_config)
        assert result == expected_value
```

### 方法三：使用 unittest.mock.patch

如果需要更精细的控制，可以使用 mock：

```python
# tests/01_unit_tests/test_example.py
from __future__ import annotations

import pytest
from unittest.mock import patch, MagicMock
from config_manager import get_config_manager


class TestExample:
    """示例测试类"""

    @patch('your_module.get_config_manager')
    def test_with_mocked_config(self, mock_get_config):
        """使用模拟配置的测试"""
        # 创建模拟配置对象
        mock_config = MagicMock()
        mock_config.timeout = 5
        mock_config.retry_count = 1
        mock_config.test_mode = True

        mock_get_config.return_value = mock_config

        # 执行测试
        result = function_that_uses_config()

        # 验证结果
        assert result == expected_value
        mock_get_config.assert_called_once()
```

### 方法四：使用快照和恢复

```python
# tests/01_unit_tests/test_example.py
from __future__ import annotations

import pytest
from config_manager import get_config_manager


class TestExample:
    """示例测试类"""

    def test_with_manual_config_management(self):
        """手动管理配置的测试"""
        cfg = get_config_manager()

        # 创建快照
        snapshot = cfg.snapshot()

        try:
            # 临时修改配置
            cfg.set('timeout', 10, autosave=False)
            cfg.set('test_mode', True, autosave=False)

            # 执行测试
            assert cfg.timeout == 10
            assert cfg.test_mode == True

            result = function_that_uses_config(cfg)
            assert result == expected_value

        finally:
            # 恢复配置
            cfg.restore(snapshot)
```

### 测试配置管理最佳实践

1. **优先使用 temporary() 方法**：这是最安全和最符合规范的方式
2. **避免直接修改全局配置**：这可能影响其他测试的执行
3. **确保配置恢复**：使用上下文管理器或 try/finally 确保配置能够恢复
4. **测试隔离**：每个测试都应该能够独立运行，不受其他测试的配置影响
5. **使用 autosave=False**：在测试中临时修改配置时，通常不希望这些修改被自动保存到文件

## 配置文件格式

配置管理器支持两种 YAML 配置文件格式：**标准格式**和**原始格式**，可以自动识别并正确处理。

### 标准格式（ConfigManager原生格式）

包含元数据和类型提示的完整格式：

```yaml
# 应用配置文件
# 这里可以添加配置说明和使用指南
__data__:
  app_name: "我的应用"
  version: "1.0.0"
  first_start_time: "2025-06-04T10:30:00.123456"
  config_file_path: "/absolute/path/to/config.yaml"  # 配置文件绝对路径

  # 数据库配置
  database:
    host: "localhost"     # 数据库主机地址
    port: 5432           # 数据库端口
    username: "admin"    # 数据库用户名

  # 功能开关
  features:
    cache_enabled: true   # 是否启用缓存
    debug_mode: false    # 调试模式开关

__type_hints__:
  server.port: int
  server.timeout: float
  log_directory: Path

# 配置文件末尾注释
```

### 原始格式（标准YAML格式）✨

直接的YAML配置格式，兼容第三方工具和手动编辑：

```yaml
# 应用配置文件
# 这里可以添加配置说明和使用指南
app_name: "我的应用"
version: "1.0.0"

# 数据库配置
database:
  host: "localhost"     # 数据库主机地址
  port: 5432           # 数据库端口
  username: "admin"    # 数据库用户名

# 功能开关
features:
  cache_enabled: true   # 是否启用缓存
  debug_mode: false    # 调试模式开关

# 支持复杂嵌套结构
application:
  modules:
    auth:
      enabled: true
      providers: ["local", "oauth", "ldap"]
      settings:
        session_timeout: 3600
        max_attempts: 3
```

### 格式自动识别

ConfigManager会自动识别配置文件格式：

- **包含 `__data__` 节点** → 标准格式处理
- **不包含 `__data__` 节点** → 原始格式处理

**使用示例**：

```python
from config_manager import get_config_manager
from datetime import datetime

# 两种格式都能正常加载
start_time = datetime.now()

# 加载原始格式配置文件
cfg = get_config_manager(
    config_path="./raw_config.yaml",  # 原始YAML格式
    first_start_time=start_time
)

# 所有配置项都能正常访问
print(f"应用名称: {cfg.app_name}")
print(f"数据库主机: {cfg.database.host}")
print(f"认证模块: {cfg.application.modules.auth.enabled}")

# hasattr() 和属性访问都正常工作
assert hasattr(cfg, 'app_name')
assert hasattr(cfg, 'database')
assert hasattr(cfg, 'application')
```

### 格式转换

原始格式配置文件在首次保存时会自动转换为标准格式，以支持ConfigManager的高级功能：

```yaml
# 转换后的标准格式
__data__:
  app_name: "我的应用"
  version: "1.0.0"
  database:
    host: "localhost"
    port: 5432
    username: "admin"
  features:
    cache_enabled: true
    debug_mode: false
  application:
    modules:
      auth:
        enabled: true
        providers: ["local", "oauth", "ldap"]

  # ConfigManager自动添加的元数据
  first_start_time: "2025-06-07T10:00:00.123456"
  config_file_path: "/absolute/path/to/raw_config.yaml"

__type_hints__: {}
```

### YAML注释保留功能

配置管理器使用 `ruamel.yaml` 库，**完美保留配置文件中的所有注释和格式**：

- ✅ **顶部注释**：文件开头的说明注释
- ✅ **行内注释**：配置项后的说明注释
- ✅ **节点注释**：配置节点上方的分组注释
- ✅ **末尾注释**：文件结尾的备注信息

**示例：注释保留效果**

修改前的配置文件：
```yaml
# 这是我的应用配置文件
__data__:
  # 应用基本信息
  app_name: "旧应用名"  # 应用名称
  version: "1.0.0"     # 版本号

  # 数据库配置
  database:
    host: "localhost"  # 数据库地址
    port: 5432        # 端口号
```

通过配置管理器修改后：
```yaml
# 这是我的应用配置文件
__data__:
  # 应用基本信息
  app_name: "新应用名"  # 应用名称
  version: "2.0.0"     # 版本号

  # 数据库配置
  database:
    host: "localhost"  # 数据库地址
    port: 5432        # 端口号

  # 新增配置项
  new_feature: true
```

**所有注释都被完美保留！**

## 环境变量支持

配置管理器支持通过环境变量注入敏感信息：

```python
import os

cfg = get_config_manager()

# 在配置中使用环境变量
cfg.database.password = os.getenv("DB_PASSWORD", "default_password")
cfg.api.secret_key = os.getenv("API_SECRET_KEY")
```

## 完整示例

### 主程序示例

```python
from config_manager import get_config_manager
from datetime import datetime
from pathlib import Path
import os

def main():
    # 记录应用启动时间（主程序必须）
    start_time = datetime.now()

    # 获取配置管理器（主程序完整初始化）
    cfg = get_config_manager(
        config_path="./config/app_config.yaml",
        watch=True,
        auto_create=True,
        autosave_delay=1.0,
        first_start_time=start_time  # 主程序必须提供
    )

    # 初始化应用配置
    if not hasattr(cfg, 'app_name'):
        cfg.update({
            "app_name": "示例应用",
            "version": "1.0.0",
            "database": {
                "host": "localhost",
                "port": 5432,
                "name": "myapp_db",
                "username": "admin",
                "password": os.getenv("DB_PASSWORD", "")
            },
            "server": {
                "host": "0.0.0.0",
                "port": 8080,
                "workers": 4
            },
            "logging": {
                "level": "INFO",
                "file": "app.log"
            }
        })

    # 设置类型提示
    cfg.set_type_hint("server.port", int)
    cfg.set_type_hint("logging.file", Path)

    # 使用配置
    print(f"启动 {cfg.app_name} v{cfg.version}")
    print(f"启动时间: {cfg.first_start_time}")
    print(f"数据库连接: {cfg.database.host}:{cfg.database.port}")
    print(f"服务器监听: {cfg.server.host}:{cfg.server.port}")

    # 调用子模块
    from my_module import process_data
    process_data()

    print("应用配置完成!")

if __name__ == "__main__":
    main()
```

### 子模块示例

```python
# my_module.py
from config_manager import get_config_manager

def process_data():
    """子模块中不需要传递 first_start_time"""
    cfg = get_config_manager()  # 简单调用

    # 直接使用配置
    batch_size = cfg.get("processing.batch_size", default=100)
    timeout = cfg.get("processing.timeout", default=30)

    print(f"数据处理批次大小: {batch_size}")
    print(f"处理超时时间: {timeout}")

    # 可以修改配置
    cfg.processing = cfg.processing or {}
    cfg.processing.last_run = datetime.now().isoformat()

def get_database_connection():
    """获取数据库连接配置的工具函数"""
    cfg = get_config_manager()
    return {
        'host': cfg.database.host,
        'port': cfg.database.port,
        'database': cfg.database.name,
        'username': cfg.database.username,
        'password': cfg.database.password
    }
```

## 运行演示

项目包含完整的演示代码，展示各种功能：

```bash
# 运行基本功能演示
python src/demo/demo_config_manager_basic.py

# 运行自动保存功能演示
python src/demo/demo_config_manager_autosave.py

# 运行高级功能演示
python src/demo/demo_config_manager_advanced.py

# 运行文件操作演示
python src/demo/demo_config_manager_file_operations.py

# 运行配置文件路径访问演示
python src/demo/demo_config_path_access.py

# 运行完整功能演示
python src/demo/demo_config_manager_all.py
```

## 测试

运行测试套件：

```bash
# 运行所有测试
pytest

# 运行单元测试
pytest tests/01_unit_tests/

# 运行集成测试
pytest tests/02_integration_tests/

# 运行特定测试文件
pytest tests/01_unit_tests/test_config_manager.py
```

## 重要提醒

### first_start_time 参数使用规则

**主程序必须提供 `first_start_time` 参数：**

```python
from datetime import datetime
from config_manager import get_config_manager

# ✅ 主程序中的正确用法
def main():
    start_time = datetime.now()
    cfg = get_config_manager(first_start_time=start_time)
    # ... 主程序逻辑

# ✅ 子模块中的正确用法
def some_function():
    cfg = get_config_manager()  # 不需要 first_start_time
    # ... 使用配置

# ❌ 主程序中的错误用法
def main():
    cfg = get_config_manager()  # 主程序应该提供 first_start_time
```

**使用场景：**

- **主程序（main.py、app.py）**：必须提供 `first_start_time`
- **库代码、工具函数、子模块**：可以不提供 `first_start_time`
- **测试代码**：通常不需要提供 `first_start_time`

`first_start_time` 参数用于：

- 记录应用的首次启动时间
- 生成配置文件的备份时间戳
- 提供时间相关的配置功能

## 常见问题

### Q: 配置文件存储在哪里？

A: 默认存储在 `src/config/config.yaml`。如果没有指定路径，会自动查找项目根目录并创建合适的配置目录。

### Q: 如何处理并发访问？

A: 配置管理器内置线程安全机制，支持多线程环境下的并发访问。

### Q: 如何备份配置？

A: 配置管理器会自动创建带时间戳的备份文件到 `backup/` 目录，也可以使用 `snapshot()` 方法手动创建快照。

### Q: 配置文件损坏怎么办？

A: 可以从自动备份恢复，或使用 `restore()` 方法从之前的快照恢复。

### Q: 什么时候需要传递 first_start_time？

A: 只有主程序（应用入口点）需要传递此参数。库代码、工具函数、子模块调用时不需要传递。

### Q: autosave_delay 设置多少合适？

A: 建议值：

- 开发环境：0.1-0.5 秒（快速响应）
- 生产环境：1-5 秒（减少 I/O 频率）
- 高频修改场景：2-10 秒（避免过度保存）

### Q: 什么时候需要启用 watch 功能？

A: 在以下场景建议启用：

- 多进程应用需要共享配置
- 需要支持热更新配置
- 运维人员需要在线修改配置
- 配置文件可能被外部工具修改

### Q: 配置文件中的注释会丢失吗？

A: **不会！** 配置管理器使用 `ruamel.yaml` 库，完美保留所有类型的YAML注释：

- 顶部注释、行内注释、节点注释、末尾注释
- 原始格式和缩进
- 引号风格和其他YAML格式特性

这意味着你可以在配置文件中添加详细的说明文档，这些注释在配置更新后会被完整保留。

### Q: 支持哪些配置文件格式？

A: ConfigManager支持两种YAML配置文件格式：

**标准格式**（ConfigManager原生）：
```yaml
__data__:
  app_name: "我的应用"
  database:
    host: "localhost"
__type_hints__:
  database.port: int
```

**原始格式**（标准YAML）：
```yaml
app_name: "我的应用"
database:
  host: "localhost"
  port: 5432
```

ConfigManager会自动识别格式并正确处理。原始格式特别适合：
- 从其他系统迁移的配置文件
- 需要与第三方工具共享的配置文件
- 手动编辑的简单配置文件

### Q: 原始格式配置文件会被修改吗？

A: 原始格式配置文件在**首次保存**时会自动转换为标准格式，以支持ConfigManager的高级功能（如类型提示、元数据管理等）。转换过程：

1. **加载时**：完全兼容，所有配置项正常访问
2. **首次保存时**：自动转换为标准格式
3. **后续使用**：使用标准格式，保持所有功能

如果需要保持原始格式不变，建议在修改前备份配置文件。

### Q: 测试中如何临时修改配置？

A: 推荐使用 `temporary()` 上下文管理器：

```python
with cfg.temporary({"test_mode": True}) as temp_cfg:
    # 使用临时配置进行测试
    pass
# 配置自动恢复
```

## 更新日志

### v2.1.1 (2025-06-07)

**🔧 重要修复：原始YAML格式支持**

- 🐛 **修复**：ConfigManager配置加载问题
  - 修复只能处理包含`__data__`节点的配置文件的限制
  - 现在支持标准YAML格式配置文件
  - 解决`hasattr()`和直接属性访问失败的问题
- ✨ **新增**：多格式自动识别
  - 自动识别标准格式和原始格式配置文件
  - 原始格式首次保存时自动转换为标准格式
  - 完全向后兼容现有配置文件
- 🧪 **测试**：新增原始YAML格式测试套件
  - 8个全面的测试用例覆盖各种场景
  - 验证格式识别、属性访问、嵌套结构等功能
  - 确保现有功能不受影响
- 📚 **文档**：完善配置文件格式说明
  - 新增原始YAML格式支持的详细文档
  - 更新架构设计和使用指南
  - 添加格式转换和最佳实践说明

**影响范围**：
- 解决所有使用原始YAML格式配置文件的问题
- 支持从其他系统迁移的配置文件
- 兼容第三方工具生成的标准YAML配置文件

### v2.1.0 (2025-06-06)

**🎉 重大功能更新：YAML注释保留**

- ✨ **新增**：完美的YAML注释保留功能
  - 支持顶部注释、行内注释、节点注释、末尾注释
  - 保留原始格式和缩进风格
  - 使用 `ruamel.yaml` 替代 `pyyaml` 实现
- 🔧 **改进**：智能数据合并策略
  - 更新配置时保留原始YAML结构
  - 新增配置项时保持格式一致性
- 🧪 **测试**：增强多线程测试稳定性
  - 优化多线程环境下的输出捕获
  - 改进测试用例的健壮性
- 📚 **文档**：完善注释保留功能说明
  - 新增详细的使用示例
  - 添加最佳实践指南

**迁移说明**：
- 依赖从 `pyyaml` 更新为 `ruamel.yaml`
- API保持完全兼容，无需修改现有代码
- 现有配置文件格式完全兼容

### v2.0.x

- 基础配置管理功能
- 自动保存和文件监视
- 类型提示和快照恢复
- 多线程安全支持

## 许可证

本项目采用 MIT 许可证。详见 LICENSE 文件。