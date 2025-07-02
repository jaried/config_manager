# CLAUDE.md

此文件为 Claude Code (claude.ai/code) 在此代码库中工作时提供指导。

## 开发命令

### 测试
```bash
# 运行所有测试
pytest

# 运行特定测试文件
pytest tests/test_config_manager/test_tc0001_001_basic_operations.py

# 运行详细输出的测试
pytest -v

# 运行简短回溯的测试
pytest --tb=short
```

### Python 环境
```bash
# 如果在 base conda 环境中，激活 python 3.12
conda deactivate && conda activate base_python3.12

# 运行简单测试
python simple_test.py

# 运行配置收集
python collect.py
```

## 项目架构

### 核心组件
- **ConfigManager**: 主要的单例配置管理器类（生产模式），支持测试模式下的多实例
- **ConfigManagerCore**: 继承自 ConfigNode 的核心实现，提供所有配置管理功能
- **ConfigNode**: 基础配置节点类，支持动态 debug_mode
- **PathResolver**: 处理路径解析和项目根目录检测
- **FileOperations**: 使用 ruamel.yaml 管理 YAML 文件操作
- **AutosaveManager**: 处理线程化的自动配置保存
- **CallChainTracker**: 跟踪方法调用链进行调试（保留功能）
- **TestEnvironmentManager**: 管理测试模式隔离和路径替换

### 关键设计模式
- **全局单例**: 生产模式下单实例，测试模式下多实例
- **线程安全**: 所有操作都是线程安全的，具有适当的锁定
- **自动持久化**: 配置更改自动保存
- **类型安全**: 整个代码库完整的类型提示
- **跨平台**: 支持 Windows 和 Ubuntu（从更广泛的操作系统支持中缩减）

### 目录结构
- `src/config_manager/`: 主包源代码
- `src/config_manager/core/`: 核心实现模块
- `src/config_manager/logger/`: 最小日志实现
- `src/config/`: 配置文件（config.yaml，备份）
- `tests/`: 测试套件，包含 01_unit_tests/ 和集成测试
- `Docs/`: 需求、架构和设计文档
- `temp/`: 临时文件（使用后必须清理）

## 配置管理

### 使用模式
```python
# 获取配置管理器（启用自动设置）
from config_manager import get_config_manager
config = get_config_manager()

# 测试模式使用
config = get_config_manager(test_mode=True)

# 通过属性访问配置（无默认值）
value = config.some_setting  # 如果未设置将抛出 AttributeError
```

### 路径处理
- 只有 `base_dir` 支持单路径到多平台配置的自动转换
- 以 `_dir` 结尾的字段自动创建目录
- 测试模式将 `base_dir` 替换为临时目录以实现隔离
- 使用 `setup_project_paths()` 进行路径配置初始化

## 开发指南

### 代码标准
- 使用 4 个空格缩进
- 函数使用 snake_case，类使用 PascalCase
- 优先使用 ruamel.yaml 而不是 pyyaml
- 测试文件必须以 `test_` 开头
- 在包内使用相对导入

### 测试要求
- 提交前所有测试必须通过
- 测试环境使用 `test_mode=True` 参数
- 测试文件应隔离在 temp/ 目录中
- 使用后清理临时文件
- 使用 `conftest.py` 进行共享测试配置

### 文档更新
代码更改后，更新相关文档：
- `Docs/01_requirements/` 中的需求文档
- `Docs/02_architecture/` 中的架构设计
- `Docs/03_design/` 中的设计文档
- 删除过时描述以匹配当前实现

### 错误处理
- 不对意外错误使用 try-except（错误透明性）
- 无备用或降级逻辑
- 属性访问无默认值（自然错误传播）

## 重要说明

### 多进程支持
- 对于多进程场景使用 `SerializableConfigData` 和 `create_serializable_config()`
- 配置数据可以被序列化并在进程间共享

### 测试模式功能
- 隔离实例防止测试干扰
- 自动路径替换到临时目录
- 为调试保留 CallChainTracker 功能
- 为 `_dir` 字段自动创建目录

### 平台支持
- 仅支持 Windows 10 和 Ubuntu Linux（缩减范围）
- 使用 `CrossPlatformPath` 处理跨平台路径
- 自动平台特定路径转换