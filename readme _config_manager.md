配置管理器 (Configuration Manager)
目录
概述

主要特性

安装

快速开始

使用示例

高级功能

测试

贡献指南

许可证

概述
配置管理器是一个强大的Python库，旨在简化应用程序配置的管理过程。它提供了直观的点操作语法、自动保存功能、类型提示支持以及多种高级配置管理功能，使开发者能够轻松处理复杂的配置需求。

主要特性
点操作语法 - 使用 config.key.subkey 形式访问和设置嵌套配置

自动保存 - 配置更改后自动保存到文件，可自定义延迟时间

类型提示支持 - 支持存储和自动转换路径等特殊类型

文件监视 - 可选的文件变化监视和自动重载功能

配置快照 - 创建和恢复配置快照

临时配置 - 使用上下文管理器创建临时配置

唯一ID生成 - 生成全局唯一配置ID

多进程安全 - 支持多进程环境下的安全配置访问

安装
bash
pip install config_manager
或者从源代码安装：

bash
git clone https://github.com/jaried/config_manager.git
cd config_manager
pip install  .
快速开始
python
from config_manager import get_config_manager
from pathlib import Path

# 初始化配置管理器

cfg = get_config_manager()

# 设置基本配置

cfg.app_name = "MyApp"
cfg.app_version = "1.0.0"

# 设置嵌套配置

cfg.database = {}
cfg.database.host = "localhost"
cfg.database.port = 5432

# 设置路径类型值

log_path = Path("/var/log/myapp")
cfg.set("logging.path", log_path, type_hint=Path)

# 获取路径值

log_dir = cfg.get_path("logging.path")
print(f"Log directory: {log_dir}")

# 批量更新

cfg.update({
    "app_version": "1.1.0",
    "database.port": 6432
})
使用示例
基本使用
python
from config_manager import get_config_manager

# 初始化配置

cfg = get_config_manager()

# 设置简单值

cfg.app_name = "MyApp"
cfg.debug_mode = False

# 设置嵌套值

cfg.database = {}
cfg.database.host = "db.example.com"
cfg.database.credentials = {}
cfg.database.credentials.username = "admin"

# 访问值

print(f"App name: {cfg.app_name}")
print(f"DB host: {cfg.database.host}")
print(f"DB user: {cfg.database.credentials.username}")

# 重新加载配置

cfg.reload()
路径类型支持
python
from pathlib import Path
from config_manager import get_config_manager

cfg = get_config_manager()

# 设置路径值

log_path = Path("/var/log/myapp")
cfg.set("logging.path", log_path, type_hint=Path)

# 获取路径值

log_dir = cfg.get_path("logging.path")
print(f"Log directory: {log_dir}")
print(f"Type: {type(log_dir)}")

# 获取类型提示

print(f"Type hint: {cfg.get_type_hint('logging.path')}")
高级功能
配置快照
python

# 创建配置快照

snapshot = cfg.snapshot()

# 修改配置

cfg.app_name = "ModifiedApp"

# 恢复快照

cfg.restore(snapshot)
print(f"App name restored: {cfg.app_name}")
临时配置上下文
python
with cfg.temporary({"debug_mode": True, "log_level": "DEBUG"}) as temp_cfg:
    print(f"Temp debug mode: {temp_cfg.debug_mode}")
    print(f"Temp log level: {temp_cfg.log_level}")

print(f"Original debug mode: {cfg.debug_mode}")
文件监视和自动重载
python

# 启用文件监视

cfg = get_config_manager(watch=True)

# 手动修改配置文件后自动重载

print("Modify the config file and see it reload automatically...")
生成唯一配置ID
python
config_id = cfg.generate_config_id()
print(f"Generated config ID: {config_id}")
测试
项目包含全面的测试套件，使用pytest运行：

bash
pytest tests/
测试文件命名规范：

tc0001_001_basic_operations.py - 基本操作测试

tc0001_002_type_hint_support.py - 类型提示支持测试

tc0002_001_autosave_feature.py - 自动保存功能测试

tc0003_001_concurrency_test.py - 并发测试

tc0004_001_error_handling.py - 错误处理测试

贡献指南
我们欢迎贡献！请遵循以下步骤：

Fork 仓库

创建特性分支 (git checkout -b feature/AmazingFeature)

提交更改 (git commit -m 'Add some AmazingFeature')

推送到分支 (git push origin feature/AmazingFeature)

打开 Pull Request

请确保遵循项目编码规范：

所有函数必须有显式的return或pass

文件头部包含四行标准注释

测试文件和函数使用tc前缀编号

许可证
本项目采用 MIT 许可证 - 详情请参阅 LICENSE 文件。

Configuration Manager
Table of Contents
Overview

Key Features

Installation

Quick Start

Usage Examples

Advanced Features

Testing

Contributing

License

Overview
Configuration Manager is a powerful Python library designed to simplify application configuration management. It provides intuitive dot-notation syntax, auto-save functionality, type hint support, and various advanced configuration management features, enabling developers to handle complex configuration requirements with ease.

Key Features
Dot-notation Syntax - Access and set nested configurations using config.key.subkey format

Auto-save - Automatically save changes to file with customizable delay

Type Hint Support - Store and auto-convert special types like Path

File Watching - Optional file change monitoring and auto-reload

Configuration Snapshots - Create and restore configuration snapshots

Temporary Configurations - Context manager for temporary configurations

Unique ID Generation - Generate globally unique configuration IDs

Multi-process Safety - Safe configuration access in multi-process environments

Installation
bash
pip install config_manager
Or install from source:

bash
git clone https://github.com/jaried/config_manager.git
cd config_manager
pip install -e .
Quick Start
python
from config_manager import get_config_manager
from pathlib import Path

# Initialize configuration manager

cfg = get_config_manager()

# Set basic configurations

cfg.app_name = "MyApp"
cfg.app_version = "1.0.0"

# Set nested configurations

cfg.database = {}
cfg.database.host = "localhost"
cfg.database.port = 5432

# Set path value

log_path = Path("/var/log/myapp")
cfg.set("logging.path", log_path, type_hint=Path)

# Get path value

log_dir = cfg.get_path("logging.path")
print(f"Log directory: {log_dir}")

# Batch update

cfg.update({
    "app_version": "1.1.0",
    "database.port": 6432
})
Usage Examples
Basic Usage
python
from config_manager import get_config_manager

# Initialize configuration

cfg = get_config_manager()

# Set simple values

cfg.app_name = "MyApp"
cfg.debug_mode = False

# Set nested values

cfg.database = {}
cfg.database.host = "db.example.com"
cfg.database.credentials = {}
cfg.database.credentials.username = "admin"

# Access values

print(f"App name: {cfg.app_name}")
print(f"DB host: {cfg.database.host}")
print(f"DB user: {cfg.database.credentials.username}")

# Reload configuration

cfg.reload()
Path Type Support
python
from pathlib import Path
from config_manager import get_config_manager

cfg = get_config_manager()

# Set path value

log_path = Path("/var/log/myapp")
cfg.set("logging.path", log_path, type_hint=Path)

# Get path value

log_dir = cfg.get_path("logging.path")
print(f"Log directory: {log_dir}")
print(f"Type: {type(log_dir)}")

# Get type hint

print(f"Type hint: {cfg.get_type_hint('logging.path')}")
Advanced Features
Configuration Snapshots
python

# Create configuration snapshot

snapshot = cfg.snapshot()

# Modify configuration

cfg.app_name = "ModifiedApp"

# Restore snapshot

cfg.restore(snapshot)
print(f"App name restored: {cfg.app_name}")
Temporary Configuration Context
python
with cfg.temporary({"debug_mode": True, "log_level": "DEBUG"}) as temp_cfg:
    print(f"Temp debug mode: {temp_cfg.debug_mode}")
    print(f"Temp log level: {temp_cfg.log_level}")

print(f"Original debug mode: {cfg.debug_mode}")
File Watching and Auto-reload
python

# Enable file watching

cfg = get_config_manager(watch=True)

# Auto-reload when config file is modified

print("Modify the config file and see it reload automatically...")
Generate Unique Configuration ID
python
config_id = cfg.generate_config_id()
print(f"Generated config ID: {config_id}")
Testing
The project includes a comprehensive test suite. Run tests with pytest:

bash
pytest tests/
Test file naming convention:

tc0001_001_basic_operations.py - Basic operations tests

tc0001_002_type_hint_support.py - Type hint support tests

tc0002_001_autosave_feature.py - Auto-save feature tests

tc0003_001_concurrency_test.py - Concurrency tests

tc0004_001_error_handling.py - Error handling tests

Contributing
Contributions are welcome! Please follow these steps:

Fork the repository

Create your feature branch (git checkout -b feature/AmazingFeature)

Commit your changes (git commit -m 'Add some AmazingFeature')

Push to the branch (git push origin feature/AmazingFeature)

Open a Pull Request

Please adhere to the project coding standards:

All functions must have explicit return or pass

File headers include four-line standard comments

Test files and functions use tc prefix numbering

License
This project is licensed under the MIT License - see the LICENSE file for details.