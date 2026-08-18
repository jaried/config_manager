# 配置管理器演示指南

本目录包含配置管理器的完整功能演示，展示了所有主要特性和使用场景。

## 演示文件说明

### 1. `demo_config_manager_basic.py` - 基本功能演示
展示配置管理器的核心功能：
- **基本操作**：属性设置、获取、嵌套配置
- **类型支持**：路径类型、类型转换、类型提示
- **批量操作**：update方法、复杂嵌套结构
- **保存加载**：手动保存、重新加载

```bash
python src/demo/demo_config_manager_basic.py
```

### 2. `demo_config_manager_autosave.py` - 自动保存演示
展示智能自动保存功能：
- **基本自动保存**：延迟保存、文件验证
- **延迟控制**：可配置延迟、连续修改合并
- **性能特性**：大量数据处理、数据完整性

```bash
python src/demo/demo_config_manager_autosave.py
```

### 3. `demo_config_manager_advanced.py` - 高级功能演示
展示高级配置管理特性：
- **快照和恢复**：配置状态管理、版本回滚
- **临时上下文**：临时配置修改、自动恢复
- **ID生成**：唯一标识符、实验管理、会话管理

```bash
python src/demo/demo_config_manager_advanced.py
```

### 4. `demo_config_manager_file_operations.py` - 文件操作演示
展示文件系统相关功能：
- **文件监视**：实时文件变化检测、自动重新加载
- **多配置文件**：独立配置管理、配置隔离
- **备份恢复**：配置备份、损坏恢复

```bash
python src/demo/demo_config_manager_file_operations.py
```

### 5. `demo_config_manager_all.py` - 完整演示
运行所有演示的交互式程序：
- 按顺序运行所有演示
- 交互式控制演示进度
- 完整功能总览

```bash
python src/demo/demo_config_manager_all.py
```

## 快速开始

### 运行单个演示
```bash
# 基本功能
python src/demo/demo_config_manager_basic.py

# 自动保存
python src/demo/demo_config_manager_autosave.py

# 高级功能
python src/demo/demo_config_manager_advanced.py

# 文件操作
python src/demo/demo_config_manager_file_operations.py
```

### 运行完整演示
```bash
python src/demo/demo_config_manager_all.py
```

## 演示特点

### 🎯 实用性
- 所有演示都基于真实使用场景
- 展示最佳实践和常见模式
- 包含错误处理和边界情况

### 🔧 可定制性
- 使用临时文件，不影响系统
- 可独立运行每个演示
- 支持中断和恢复

### 📚 教育性
- 详细的输出说明
- 逐步演示过程
- 结果验证和解释

### 🧹 清理性
- 自动清理临时文件
- 资源管理和异常处理
- 不留下演示痕迹

## 演示内容概览

| 功能分类 | 主要特性 | 演示文件 |
|---------|---------|---------|
| **基础操作** | 属性访问、嵌套配置、类型支持 | `demo_config_manager_basic.py` |
| **自动保存** | 智能保存、延迟控制、性能优化 | `demo_config_manager_autosave.py` |
| **高级特性** | 快照恢复、临时上下文、ID生成 | `demo_config_manager_advanced.py` |
| **文件操作** | 文件监视、多配置、备份恢复 | `demo_config_manager_file_operations.py` |
| **完整体验** | 交互式全功能演示 | `demo_config_manager_all.py` |

## 使用建议

1. **新用户**：从 `demo_config_manager_basic.py` 开始
2. **评估性能**：运行 `demo_config_manager_autosave.py`
3. **了解高级功能**：查看 `demo_config_manager_advanced.py`
4. **生产环境评估**：运行 `demo_config_manager_file_operations.py`
5. **完整体验**：使用 `demo_config_manager_all.py`

## 技术要求

- Python 3.7+
- PyYAML
- 已安装配置管理器包：`pip install -e .`

## 故障排除

如果演示运行失败，请检查：

1. **安装检查**
   ```bash
   pip list | grep config-manager
   ```

2. **依赖检查**
   ```bash
   pip install -r requirements.txt  # 如果有的话
   ```

3. **权限检查**：确保有临时文件创建权限

4. **路径检查**：从项目根目录运行演示

## 代码示例

### 基本使用
```python
from config_manager import get_config_manager

# 获取配置管理器
cfg = get_config_manager()

# 设置配置
cfg.app_name = "MyApp"
cfg.database.host = "localhost"
cfg.database.port = 5_432

# 自动保存！配置已持久化
```

### 高级功能
```python
# 创建快照
snapshot = cfg.snapshot()

# 修改配置
cfg.debug_mode = True

# 恢复快照
cfg.restore(snapshot)

# 临时配置
with cfg.temporary({"debug_mode": True}) as temp_cfg:
    # 临时启用调试模式
    print(f"调试模式: {temp_cfg.debug_mode}")
# 自动恢复原始配置
```

### 类型安全
```python
from pathlib import Path

# 设置路径类型
cfg.set("log_path", Path("/var/log"), type_hint=Path)

# 类型转换
port = cfg.get("server.port", as_type=int)
timeout = cfg.get("timeout", as_type=float)
```

## 最佳实践

### 1. 配置组织
```python
# 推荐的配置结构
cfg.app.name = "MyApp"
cfg.app.version = "1.0.0"

cfg.database.host = "localhost"
cfg.database.port = 5_432

cfg.logging.level = "INFO"
cfg.logging.path = Path("/var/log/myapp")
```

### 2. 错误处理
```python
# 安全的配置访问
database_url = cfg.get("database.url", default="sqlite:///default.db")
max_connections = cfg.get("database.max_connections", default=10, as_type=int)
```

### 3. 性能优化
```python
# 批量更新以减少自动保存次数
cfg.update({
    "server.host": "0.0.0.0",
    "server.port": 8_080,
    "server.workers": 4
})
```

### 4. 开发环境配置
```python
# 使用临时配置进行测试
with cfg.temporary({
    "database.url": "sqlite:///test.db",
    "debug_mode": True,
    "log_level": "DEBUG"
}) as test_cfg:
    # 在测试配置下运行代码
    run_tests()
```

## 扩展功能

### 自定义配置路径
```python
# 指定配置文件位置
cfg = get_config_manager(
    config_path="/path/to/custom/config.yaml",
    watch=True,          # 启用文件监视
    autosave_delay=1.0   # 1秒自动保存延迟
)
```

### 多环境配置
```python
import os

env = os.getenv("ENVIRONMENT", "development")
config_file = f"config_{env}.yaml"

cfg = get_config_manager(config_path=config_file)
```

## 性能指标

| 操作类型 | 响应时间 | 内存占用 |
|---------|---------|---------|
| 属性设置 | < 1ms | 最小 |
| 嵌套访问 | < 1ms | 最小 |
| 自动保存 | < 10ms | 低 |
| 文件重载 | < 50ms | 中等 |
| 快照创建 | < 5ms | 低 |

## 支持和反馈

如果您在使用演示过程中遇到问题或有建议，请：

1. 检查演示输出中的错误信息
2. 查看项目文档
3. 提交 Issue 或建议

## 许可证

本演示代码遵循与主项目相同的许可证。