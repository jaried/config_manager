# Config Manager

一个功能强大的Python配置管理器，支持跨平台路径、自动备份、测试模式隔离等特性。

## 安装

```bash
pip install -e .
```

## 基本使用

### 获取配置管理器

```python
from config_manager import get_config_manager

# 获取配置管理器实例
config = get_config_manager()

# 测试模式（用于单元测试）
config = get_config_manager(test_mode=True)
```

### 配置基本操作

```python
# 设置配置值
config.set('database.host', 'localhost')
config.set('database.port', 5432)

# 获取配置值
host = config.get('database.host')
port = config.get('database.port', default=3306)

# 使用属性访问（推荐）
host = config.database.host
port = config.database.port
```

### 多平台路径配置

配置管理器自动支持Windows和Linux平台的路径配置：

```python
# 设置基础路径（自动转换为多平台格式）
config.set('base_dir', '/tmp/my_project')

# 在Windows系统上会自动创建：
# base_dir:
#   windows: d:\logs  # 默认值
#   ubuntu: /tmp/my_project

# 在Linux系统上会自动创建：
# base_dir:
#   windows: d:\logs
#   ubuntu: /tmp/my_project

# 获取当前平台的路径
current_base_dir = config.get('base_dir')  # 返回当前平台对应的路径
```

### 项目路径设置

```python
# 初始化项目路径结构
config.setup_project_paths()

# 访问生成的路径
work_dir = config.get('paths.work_dir')
backup_dir = config.get('paths.backup_dir')  # 新增：备份目录
log_dir = config.get('paths.log_dir')
checkpoint_dir = config.get('paths.checkpoint_dir')
```

### 备份功能

配置文件会自动备份到 `config.paths.backup_dir` 目录下：

```python
# 备份路径格式：
# {work_dir}/backup/{first_start_time日期YYYYMMDD}/{first_start_time时间HHMMSS}/

# 示例：
# /tmp/my_project/project_name/experiment_name/backup/20250703/143025/config_20250703_143025.yaml
```

### 测试模式

测试模式提供完全隔离的环境，避免测试干扰生产配置：

```python
# 启用测试模式
config = get_config_manager(test_mode=True)

# 测试模式特性：
# 1. 使用系统临时目录
# 2. 路径格式：{系统临时目录}/tests/{YYYYMMDD}/{HHMMSS}_{唯一标识符}
# 3. 支持并发测试隔离
# 4. 自动路径替换
```

### 类型提示和验证

```python
from pathlib import Path

# 设置带类型提示的配置
config.set('data_dir', '/tmp/data', type_hint=Path)

# 获取指定类型的配置值
data_path = config.get('data_dir', as_type=Path)
```

### 配置文件监视

```python
# 启用文件监视（配置文件变化时自动重新加载）
config = get_config_manager(watch=True)
```

## 配置文件格式

配置文件使用YAML格式，支持多平台路径：

```yaml
__data__:
  project_name: "my_project"
  base_dir:
    windows: "d:\\projects\\my_project"
    ubuntu: "/home/user/projects/my_project"
  
  paths:
    work_dir: "/home/user/projects/my_project/my_project/experiment"
    backup_dir: "/home/user/projects/my_project/my_project/experiment/backup/20250703/143025"
    log_dir: "/home/user/projects/my_project/my_project/experiment/logs/2025-07-03/143025"
    checkpoint_dir: "/home/user/projects/my_project/my_project/experiment/checkpoint"

__type_hints__:
  data_dir: "Path"
```

## 平台支持

- **Windows**: 支持Windows路径格式，默认使用 `d:\logs`
- **Linux/Ubuntu**: 支持Unix路径格式，默认使用 `~/logs`
- **跨平台**: 自动检测当前平台并使用对应配置

## 注意事项

1. 配置会自动保存，无需手动调用save()
2. 测试模式下所有路径都会被替换为临时路径
3. 只有 `base_dir` 支持多平台配置自动转换
4. 以 `_dir` 结尾的配置字段会自动创建对应目录
5. 配置文件备份到新的 `config.paths.backup_dir` 路径而不是传统的 `config/backup` 目录