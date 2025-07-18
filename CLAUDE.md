# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

这是一个强大的Python配置管理库，支持自动保存、类型提示、文件监视、YAML注释保留、测试模式、多进程支持等高级功能。

## 核心架构

### 主要组件

- **ConfigManager** (`src/config_manager/config_manager.py`): 主要配置管理器类，处理单例模式和测试模式
- **ConfigManagerCore** (`src/config_manager/core/manager.py`): 核心实现，包含配置管理的基本功能
- **ConfigNode** (`src/config_manager/config_node.py`): 配置节点类，提供点操作语法访问
- **SerializableConfigData** (`src/config_manager/serializable_config.py`): 可序列化配置数据，支持多进程
- **TestEnvironmentManager** (`src/config_manager/test_environment.py`): 测试环境管理器

### 核心模块 (`src/config_manager/core/`)

- **manager.py**: 配置管理器核心实现
- **file_operations.py**: 文件操作（YAML加载/保存，注释保留）
- **autosave_manager.py**: 自动保存管理器
- **watcher.py**: 文件监视器
- **path_resolver.py**: 路径解析器
- **path_configuration.py**: 路径配置管理
- **cross_platform_paths.py**: 跨平台路径处理
- **call_chain.py**: 调用链追踪

### 测试架构

- **单元测试**: `tests/01_unit_tests/test_config_manager/` - 各个功能模块的单元测试
- **集成测试**: `tests/test_config_manager/` - 完整功能的集成测试
- **多进程测试**: `tests/test_config_multiprocessing_complete.py` - 多进程环境测试

## 开发命令

### 环境设置

```bash
# 激活conda环境
source /home/tony/programs/miniconda3/etc/profile.d/conda.sh && conda activate base_python3.12

# 安装开发依赖
pip install -e .
```

### 测试命令

```bash
# 运行所有测试
conda run -n base_python3.12 python -m pytest tests/

# 运行特定测试文件
conda run -n base_python3.12 python -m pytest tests/01_unit_tests/test_config_manager/test_tc0012_001_test_mode.py

# 运行特定测试函数
conda run -n base_python3.12 python -m pytest tests/01_unit_tests/test_config_manager/test_tc0012_001_test_mode.py::test_test_mode_basic

# 运行单元测试
conda run -n base_python3.12 python -m pytest tests/01_unit_tests/

# 运行集成测试
conda run -n base_python3.12 python -m pytest tests/test_config_manager/

# 运行多进程测试
conda run -n base_python3.12 python -m pytest tests/test_config_multiprocessing_complete.py
```

### 构建命令

```bash
# 构建包
conda run -n base_python3.12 python -m build

# 安装到本地环境
conda run -n base_python3.12 pip install -e .

# 清理构建文件
rm -rf build/ dist/ src/config_manager.egg-info/
```

### 代码质量检查

```bash
# 运行ruff检查
conda run -n base_python3.12 ruff check src/ tests/

# 运行ruff格式化
conda run -n base_python3.12 ruff format src/ tests/
```

## 重要开发指南

### 测试模式隔离

- 所有测试用例必须使用 `test_mode=True` 来创建配置管理器实例
- 测试模式会自动创建隔离的测试环境，避免影响生产配置
- 测试路径格式: `{临时目录}/tests/{YYYYMMDD}/{HHMMSS}/src/config/config.yaml`

### 多进程支持

- 使用 `get_serializable_data()` 获取可序列化的配置数据
- 在多进程环境中建议设置 `watch=False` 避免进程间冲突
- 可序列化配置数据支持与ConfigManager相同的访问API

### 跨平台路径处理

- 使用 `cross_platform_paths.py` 模块处理跨平台路径
- 路径配置会自动转换为适合当前平台的格式
- 支持Windows、Linux、macOS三个平台

### 文件操作

- 使用 `ruamel.yaml` 保留YAML注释和格式
- 支持标准格式（包含 `__data__` 节点）和原始格式的YAML文件
- 自动备份机制，防止配置文件丢失

### 调用链追踪

- 通过 `ENABLE_CALL_CHAIN_DISPLAY` 开关控制调用链显示
- 用于调试和问题排查

## 核心API

### 主要入口函数

```python
def get_config_manager(
    config_path: str = None,
    watch: bool = False,
    auto_create: bool = False,
    autosave_delay: float = None,
    first_start_time: datetime = None,
    test_mode: bool = False
) -> ConfigManager
```

### 配置访问模式

- **属性访问**: `config.app_name`
- **字典访问**: `config['app_name']`
- **嵌套访问**: `config.get('database.host', 'localhost')`
- **类型转换**: `config.get('port', 8080, as_type=int)`

### 测试最佳实践

1. 始终使用 `test_mode=True` 创建测试配置
2. 使用 `temporary()` 上下文管理器进行临时配置修改
3. 利用 `snapshot()` 和 `restore()` 进行状态保存和恢复
4. 测试文件命名遵循 `test_tc{编号}_{序号}_{功能描述}.py` 格式

## 依赖关系

### 核心依赖

- **Python 3.12+**: 项目基础运行环境
- **ruamel.yaml**: YAML文件处理，保留注释
- **is-debug**: 调试模式检测

### 开发依赖

- **pytest**: 测试框架
- **ruff**: 代码格式化和lint工具

## 项目结构说明

```
src/config_manager/
├── config_manager.py          # 主配置管理器
├── config_node.py             # 配置节点
├── serializable_config.py     # 可序列化配置
├── test_environment.py        # 测试环境管理
├── utils.py                   # 工具函数
├── core/                      # 核心模块
│   ├── manager.py             # 核心管理器
│   ├── file_operations.py     # 文件操作
│   ├── autosave_manager.py    # 自动保存
│   ├── watcher.py             # 文件监视
│   ├── path_resolver.py       # 路径解析
│   ├── path_configuration.py  # 路径配置
│   └── cross_platform_paths.py # 跨平台路径
# 注意：日志记录使用Python标准logging模块
```

## 关键特性

### 1. 自动保存机制
- 配置修改后自动保存到文件
- 支持延迟保存减少I/O频率
- 自动创建备份文件

### 2. 测试模式隔离
- 一键创建隔离的测试环境
- 自动路径替换和配置复制
- 测试结束后自动清理

### 3. 多进程支持
- 可序列化配置数据传递
- 支持多进程环境下的配置访问
- 与标准API完全兼容

### 4. 跨平台兼容
- 自动处理不同操作系统的路径格式
- 统一的配置访问接口
- 智能路径转换

### 5. 类型安全
- 完整的类型提示支持
- 自动类型转换
- 类型hint存储和恢复