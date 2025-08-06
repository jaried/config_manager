# 设计文档：TSB日志路径格式更新

## 1. 设计概述

本设计文档描述了如何实现TSB日志路径格式更新功能，包括路径生成逻辑、路径一致性保证机制以及相关的技术实现方案。

## 2. 系统架构

### 2.1 组件关系图

```
ConfigManager
    │
    ├── PathConfiguration (路径配置管理)
    │   ├── work_dir (基础工作目录)
    │   ├── tsb_logs_dir (TSB日志目录) [动态生成]
    │   └── tensorboard_dir (TensorBoard目录) [等于tsb_logs_dir]
    │
    └── PathResolver (路径解析器)
        └── generate_tsb_logs_path() (路径生成方法)
```

### 2.2 数据流

1. 用户访问`config.paths.tsb_logs_dir`
2. PathConfiguration检测到访问请求
3. 调用PathResolver生成动态路径
4. 返回格式化的路径字符串
5. `tensorboard_dir`自动返回相同的值

## 3. 详细设计

### 3.1 路径生成算法

```python
def generate_tsb_logs_path(work_dir: str, timestamp: datetime = None) -> str:
    """
    生成TSB日志路径
    
    Args:
        work_dir: 工作目录根路径
        timestamp: 时间戳，默认为当前时间
        
    Returns:
        格式化的TSB日志路径
    """
    if timestamp is None:
        timestamp = datetime.now()
    
    # 提取时间组件
    year = timestamp.strftime('%Y')
    week_number = timestamp.isocalendar()[1]  # ISO周数
    week_str = f"{week_number:02d}"  # 格式化为两位数
    date_str = timestamp.strftime('%m%d')
    time_str = timestamp.strftime('%H%M%S')
    
    # 构建路径
    path_components = [
        work_dir,
        'tsb_logs',
        year,
        week_str,
        date_str,
        time_str
    ]
    
    return os.path.join(*path_components)
```

### 3.2 路径一致性保证

#### 3.2.1 属性描述符实现

```python
class TensorBoardDirDescriptor:
    """确保tensorboard_dir始终等于tsb_logs_dir的描述符"""
    
    def __get__(self, obj, objtype=None):
        if obj is None:
            return self
        return obj.tsb_logs_dir
    
    def __set__(self, obj, value):
        raise AttributeError("tensorboard_dir是只读属性，其值自动等于tsb_logs_dir")
```

#### 3.2.2 PathConfiguration类修改

```python
class PathConfiguration:
    """路径配置类"""
    
    tensorboard_dir = TensorBoardDirDescriptor()
    
    def __init__(self, work_dir: str):
        self._work_dir = work_dir
        self._tsb_logs_dir_cache = None
        self._cache_timestamp = None
    
    @property
    def tsb_logs_dir(self) -> str:
        """获取TSB日志目录路径"""
        current_time = datetime.now()
        
        # 缓存策略：每秒更新一次
        if (self._cache_timestamp is None or 
            (current_time - self._cache_timestamp).total_seconds() >= 1):
            self._tsb_logs_dir_cache = generate_tsb_logs_path(self._work_dir)
            self._cache_timestamp = current_time
            
        return self._tsb_logs_dir_cache
```

### 3.3 跨平台路径处理

```python
def normalize_path(path: str) -> str:
    """
    标准化路径以确保跨平台兼容性
    
    Args:
        path: 原始路径字符串
        
    Returns:
        标准化后的路径
    """
    # 使用pathlib处理路径
    path_obj = Path(path)
    return str(path_obj.resolve())
```

### 3.4 周数计算细节

遵循ISO 8601标准：
- 每年的第一个周四所在的周为第1周
- 一年可能有52或53周
- 使用Python的`datetime.isocalendar()`方法

```python
def get_iso_week_number(date: datetime) -> int:
    """获取ISO标准周数"""
    return date.isocalendar()[1]
```

## 4. 接口设计

### 4.1 公共API

```python
# 获取TSB日志目录
tsb_dir = config.paths.tsb_logs_dir
# 返回: /path/to/work/tsb_logs/2025/02/0107/181520

# 获取TensorBoard目录（始终等于tsb_logs_dir）
tb_dir = config.paths.tensorboard_dir
# 返回: /path/to/work/tsb_logs/2025/02/0107/181520

# 尝试设置tensorboard_dir（将抛出异常）
config.paths.tensorboard_dir = "/custom/path"  # AttributeError
```

### 4.2 内部API

```python
class PathResolver:
    @staticmethod
    def generate_tsb_logs_path(work_dir: str, timestamp: datetime = None) -> str:
        """生成TSB日志路径"""
        pass
    
    @staticmethod
    def parse_tsb_logs_path(path: str) -> dict:
        """解析TSB日志路径，提取时间信息"""
        pass
```

## 5. 错误处理

### 5.1 异常类型

```python
class PathGenerationError(Exception):
    """路径生成错误"""
    pass

class InvalidWorkDirError(PathGenerationError):
    """无效的工作目录错误"""
    pass
```

### 5.2 错误处理策略

1. **工作目录不存在**: 抛出`InvalidWorkDirError`
2. **路径创建失败**: 记录错误日志，抛出`PathGenerationError`
3. **权限不足**: 提供明确的错误信息

## 6. 性能优化

### 6.1 缓存机制

- 路径生成结果缓存1秒
- 使用`functools.lru_cache`缓存周数计算
- 避免重复的文件系统操作

### 6.2 延迟计算

- 路径仅在访问时生成
- 使用属性描述符实现延迟加载

## 7. 测试策略

### 7.1 单元测试

```python
def test_tsb_logs_dir_format():
    """测试TSB日志目录格式"""
    # 固定时间戳测试
    test_time = datetime(2025, 1, 7, 18, 15, 20)
    expected = "/work/tsb_logs/2025/02/0107/181520"
    assert generate_tsb_logs_path("/work", test_time) == expected

def test_tensorboard_dir_equals_tsb_logs_dir():
    """测试tensorboard_dir等于tsb_logs_dir"""
    config = get_config_manager(test_mode=True)
    assert config.paths.tensorboard_dir == config.paths.tsb_logs_dir
```

### 7.2 集成测试

- 测试路径创建和访问
- 测试跨平台兼容性
- 测试边界情况（年初、年末）

## 8. 迁移方案

### 8.1 检测旧路径

```python
def detect_old_format(path: str) -> bool:
    """检测是否为旧格式路径"""
    # 旧格式特征检测逻辑
    pass
```

### 8.2 路径迁移

```python
def migrate_old_paths(old_root: str, new_root: str):
    """迁移旧格式路径到新格式"""
    # 扫描和迁移逻辑
    pass
```

## 9. 配置示例

### 9.1 生成的配置文件示例

```yaml
paths:
  work_dir: /home/user/project/work
  # tsb_logs_dir 和 tensorboard_dir 是动态生成的
  # 实际值类似: /home/user/project/work/tsb_logs/2025/02/0107/181520
```

### 9.2 代码使用示例

```python
from config_manager import get_config_manager

# 获取配置
config = get_config_manager()

# 使用TSB日志目录
tsb_dir = config.paths.tsb_logs_dir
print(f"TSB logs will be saved to: {tsb_dir}")

# TensorBoard目录自动保持一致
tb_dir = config.paths.tensorboard_dir
assert tb_dir == tsb_dir
```

## 10. 安全考虑

- 路径生成不包含敏感信息
- 避免路径遍历攻击
- 确保适当的文件权限

## 11. 未来优化

- 支持自定义时间戳格式
- 支持路径模板配置
- 添加路径压缩归档功能