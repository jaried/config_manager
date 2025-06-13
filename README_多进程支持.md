# config_manager多进程支持说明

## 问题描述

**原始问题**：config_manager生成的config对象不能传递给多进程worker，因为包含不可pickle序列化的组件（如正则表达式对象、线程锁、文件监视器等）。

**错误信息**：`cannot pickle 're.Pattern' object`

## 解决方案

### 1. 实现了可序列化的配置数据类

创建了 `SerializableConfigData` 类，这是一个轻量级的、完全可序列化的配置数据容器。

**特点**：
- ✅ 完全支持pickle序列化
- ✅ 保持与原ConfigManager相同的API
- ✅ 支持属性访问、字典访问、get方法等
- ✅ 支持嵌套配置访问

### 2. 为ConfigManager添加序列化方法

在ConfigManager中新增了以下方法：
- `get_serializable_data()` - 获取可序列化的配置数据
- `create_serializable_snapshot()` - 创建配置快照
- `is_pickle_serializable()` - 检查对象是否可序列化

## 使用方法

### 基本使用流程

```python
from config_manager import get_config_manager
import multiprocessing as mp

# 1. 创建配置管理器
config = get_config_manager(
    config_path="config.yaml",
    auto_create=True,
    watch=False  # 多进程环境建议关闭文件监视
)

# 2. 设置配置
config.app_name = "MyApp"
config.database = {
    'host': 'localhost',
    'port': 5432
}

# 3. 获取可序列化的配置数据
serializable_config = config.get_serializable_data()

# 4. 在多进程中使用
def worker_function(config_data):
    app_name = config_data.app_name
    db_host = config_data.database.host
    # ... 处理逻辑
    return result

# 5. 启动多进程
with mp.Pool(processes=4) as pool:
    results = pool.map(worker_function, [serializable_config] * 4)
```

### 配置访问方式

```python
# 1. 直接属性访问
app_name = config_data.app_name

# 2. 字典风格访问
version = config_data['version']

# 3. get方法（支持默认值）
batch_size = config_data.get('processing.batch_size', 100)

# 4. 嵌套访问
log_dir = config_data.get('paths.log_dir', '/tmp/logs')

# 5. 复杂对象访问
db_config = config_data.database
host = db_config.host
```

## 测试用例

### 完整测试（包含在项目中）

- `tests/test_multiprocessing_pickle.py` - 基础pickle问题验证
- `tests/test_config_multiprocessing_complete.py` - 完整场景测试
- `tests/example_multiprocessing_usage.py` - 使用示例

### 简化测试（可独立使用）

项目根目录下的 `test_config_multiprocess_minimal.py` 是一个最小化的测试脚本，可以直接复制到任何项目中使用。

## 测试结果

✅ **所有测试通过**：
- pickle序列化测试通过
- 多进程配置传递成功
- 所有worker使用相同配置数据
- 支持各种配置访问方式
- 无错误信息输出

## 性能特点

- **序列化数据大小**：约1000-2000 bytes（取决于配置复杂度）
- **序列化速度**：快速，适合频繁的多进程调用
- **内存占用**：轻量级，仅包含配置数据
- **功能完整性**：保持原有API的所有功能

## 注意事项

1. **文件监视器**：多进程环境建议设置 `watch=False`
2. **Windows兼容性**：需要设置 `mp.set_start_method('spawn', force=True)`
3. **配置更新**：序列化后的配置是快照，不会自动同步主进程的配置更新
4. **路径配置**：某些路径配置错误不会影响核心功能，会自动降级处理

## 在其他项目中使用

1. **安装或导入config_manager模块**
2. **复制 `test_config_multiprocess_minimal.py` 到您的项目**
3. **根据需要调整导入路径**
4. **运行测试验证功能**
5. **按照使用示例集成到您的代码中**

## 核心改进

- ✅ 解决了pickle序列化问题
- ✅ 保持API兼容性
- ✅ 增强了错误容错性
- ✅ 提供了完整的测试用例
- ✅ 支持各种使用场景

现在config_manager完全支持多进程环境，可以安全地将配置数据传递给任何数量的worker进程。 