# Config Manager

一个强大、易用的 Python 配置管理库，支持自动保存、类型提示、文件监视、YAML注释保留、测试模式、多进程支持等高级功能。

## 特性

- 🚀 **简单易用**：直观的点操作语法访问配置项
- 💾 **自动保存**：配置变更时自动保存到文件
- 🔒 **线程安全**：支持多线程环境安全使用
- 🎯 **类型安全**：完整的类型提示支持
- 📁 **文件监视**：实时监控配置文件变化并自动重载
- 🔄 **快照恢复**：便捷的配置状态保存和恢复
- 💬 **注释保留**：完美保留YAML配置文件中的注释和格式
- 📄 **多格式支持**：支持标准格式和原始YAML格式，自动识别
- 🧪 **测试模式**：一键创建隔离的测试环境，智能路径替换
- 🏗️ **自动路径管理**：智能生成项目目录结构，支持调试模式和时间戳
- 🔄 **多进程支持**：通过可序列化配置数据支持多进程环境
- 🌐 **跨平台**：支持 Windows、Linux、macOS

## 安装

从源代码仓库安装：

```bash
git clone https://github.com/jaried/config_manager.git
cd config_manager
pip install -e .
```

### 依赖要求

- Python 3.12+
- ruamel.yaml (用于YAML注释保留)
- is-debug (用于调试模式检测)

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

| 参数 | 类型 | 默认值 | 是否必需 | 说明 |
|------|------|--------|----------|------|
| `config_path` | `str` | `None` | 否 | 配置文件路径。如果为 `None`，会自动查找项目根目录并使用 `src/config/config.yaml` |
| `watch` | `bool` | `False` | 否 | 是否启用文件监视。为 `True` 时会监控配置文件变化并自动重载 |
| `auto_create` | `bool` | `False` | 否 | 配置文件不存在时是否自动创建。为 `True` 时会在指定路径创建新的配置文件 |
| `autosave_delay` | `float` | `None` | 否 | 自动保存延迟时间（秒）。配置修改后延迟指定时间再保存，避免频繁 I/O |
| `first_start_time` | `datetime` | `None` | 主程序需要 | 应用首次启动时间。**主程序调用时必须提供**，用于记录启动时间和生成备份文件时间戳 |
| `test_mode` | `bool` | `False` | 否 | 是否启用测试模式。为 `True` 时创建隔离的测试环境，自动生成临时路径 |

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

### 2. 安全的配置访问

```python
# 可以在任何地方使用（主程序或子模块）
cfg = get_config_manager()

# 使用 get 方法安全访问，提供默认值
timeout = cfg.get("database.timeout", default=30)
max_connections = cfg.get("database.max_connections", default=100)

# 指定类型转换
port = cfg.get("server.port", default="8080", as_type=int)
```

### 3. 类型提示和转换

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

### 3. 自动路径配置管理

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

## 测试模式功能

### 一键测试环境

**测试模式**通过一个参数即可创建完全隔离的测试环境：

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

### 测试路径格式

测试模式会在系统临时目录下创建唯一的测试环境：

```
{系统临时目录}/tests/{YYYYMMDD}/{HHMMSS}/src/config/config.yaml
```

例如：`d:\temp\tests\20250607\143052\src\config\config.yaml`

## 多进程配置支持

config_manager 完美支持多进程环境，通过可序列化的配置数据传递，解决了传统配置管理器在多进程中的pickle序列化问题。

### 核心特性

- ✅ **完全可序列化**：配置数据可以安全地传递给多进程worker
- ✅ **API兼容性**：与原ConfigManager保持相同的访问方式
- ✅ **高性能传输**：轻量级数据结构，序列化数据通常 < 2KB
- ✅ **配置一致性**：所有worker进程获得相同的配置数据
- ✅ **跨平台支持**：兼容Windows、Linux、macOS的多进程方式

### 基本使用

#### 1. 获取可序列化配置数据

```python
import multiprocessing as mp
from config_manager import get_config_manager
from datetime import datetime

# 1. 创建配置管理器（禁用文件监视以避免进程间冲突）
config = get_config_manager(
    config_path="config.yaml",
    watch=False,  # 多进程环境建议禁用文件监视
    first_start_time=datetime.now()
)

# 2. 设置配置
config.app_name = "多进程应用"
config.batch_size = 100
config.database = {
    'host': 'localhost',
    'port': 5432,
    'timeout': 30
}

# 3. 获取可序列化的配置数据
serializable_config = config.get_serializable_data()
print(f"配置数据可序列化: {serializable_config.is_serializable()}")
```

#### 2. 在多进程worker中使用配置

```python
def worker_function(config_data):
    """worker函数，接收序列化的配置数据"""
    worker_name = mp.current_process().name
    
    # 使用配置数据（API与ConfigManager完全相同）
    app_name = config_data.app_name
    batch_size = config_data.batch_size
    db_host = config_data.database.host
    timeout = config_data.get('database.timeout', 30)
    
    # 模拟处理任务
    results = []
    for i in range(batch_size):
        results.append(f"{app_name}-{worker_name}-item-{i}")
    
    return {
        'worker': worker_name,
        'processed': len(results),
        'app_name': app_name,
        'db_host': db_host
    }

# 启动多进程处理
def main():
    # Windows兼容性设置
    if sys.platform.startswith('win'):
        mp.set_start_method('spawn', force=True)
    
    # 创建进程池并执行任务
    with mp.Pool(processes=4) as pool:
        # 将相同的配置数据传递给所有worker
        results = pool.map(worker_function, [serializable_config] * 4)
    
    # 验证结果
    for result in results:
        print(f"Worker {result['worker']} 处理了 {result['processed']} 项")

if __name__ == '__main__':
    main()
```

### 配置访问方式

可序列化配置数据支持与ConfigManager完全相同的访问方式：

```python
# 获取可序列化配置
config_data = config.get_serializable_data()

# 属性访问
app_name = config_data.app_name
version = config_data.version

# 字典访问
database_host = config_data['database']['host']
batch_size = config_data['batch_size']

# get方法（支持默认值）
timeout = config_data.get('timeout', 30)
log_level = config_data.get('logging.level', 'INFO')

# 嵌套访问
cache_size = config_data.get('cache.size', 1000)
redis_host = config_data.get('redis.connection.host', 'localhost')

# 检查键是否存在
if 'debug_mode' in config_data:
    debug = config_data.debug_mode

# 类型转换
max_workers = config_data.get('max_workers', 4, as_type=int)
enable_cache = config_data.get('enable_cache', True, as_type=bool)
```

## 配置文件格式

配置管理器支持两种 YAML 配置文件格式，可以自动识别并正确处理。

### 标准格式（ConfigManager原生格式）

包含元数据和类型提示的完整格式：

```yaml
# 应用配置文件
__data__:
  app_name: "我的应用"
  version: "1.0.0"
  first_start_time: "2025-06-04T10:30:00.123456"
  config_file_path: "/absolute/path/to/config.yaml"
  
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
```

### 原始格式（标准YAML格式）

直接的YAML配置格式，兼容第三方工具和手动编辑：

```yaml
# 应用配置文件
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

### YAML注释保留功能

配置管理器使用 `ruamel.yaml` 库，**完美保留配置文件中的所有注释和格式**：

- ✅ **顶部注释**：文件开头的说明注释
- ✅ **行内注释**：配置项后的说明注释  
- ✅ **节点注释**：配置节点上方的分组注释
- ✅ **末尾注释**：文件结尾的备注信息

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

A: 配置管理器会自动创建带时间戳的备份文件，也可以使用 `snapshot()` 方法手动创建快照。

### Q: 配置文件损坏怎么办？

A: 可以从自动备份恢复，或使用 `restore()` 方法从之前的快照恢复。

### Q: 什么时候需要传递 first_start_time？

A: 只有主程序（应用入口点）需要传递此参数。库代码、工具函数、子模块调用时不需要传递。

### Q: autosave_delay 设置多少合适？

A: 建议值：
- 开发环境：0.1-0.5 秒（快速响应）
- 生产环境：1-5 秒（减少 I/O 频率）
- 高频修改场景：2-10 秒（避免过度保存）

### Q: 配置文件中的注释会丢失吗？

A: **不会！** 配置管理器使用 `ruamel.yaml` 库，完美保留所有类型的YAML注释和格式。

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

ConfigManager会自动识别格式并正确处理。

### Q: 测试中如何临时修改配置？

A: 推荐使用 `temporary()` 上下文管理器：

```python
with cfg.temporary({"test_mode": True}) as temp_cfg:
    # 使用临时配置进行测试
    pass
# 配置自动恢复
```

## 许可证

本项目采用 MIT 许可证。