# TSB日志和TensorBoard路径统一化详细设计

## 1. 设计背景

为了确保TensorBoard相关的所有路径保持一致，避免配置混乱，需要实现tsb_logs_dir和tensorboard_dir的统一化管理。

## 2. 设计目标

1. **路径一致性**：tensorboard_dir始终等于tsb_logs_dir
2. **格式标准化**：tsb_logs_dir使用统一的时间戳格式
3. **性能优化**：路径生成结果缓存，避免重复计算
4. **向后兼容**：不影响现有功能

## 3. 技术方案

### 3.1 路径格式定义

**统一格式**：
```
{work_dir}/tsb_logs/{yyyy}/{ww}/{mmdd}/{HHMMSS}
```

**格式说明**：
- `{work_dir}`: 工作目录根路径
- `/tsb_logs/`: 固定的TSB日志子目录
- `{yyyy}`: 4位年份
- `{ww}`: 2位周数（ISO 8601标准，不带W前缀）
- `{mmdd}`: 月日（4位）
- `{HHMMSS}`: 时分秒（6位）

### 3.2 核心实现

#### 3.2.1 DynamicPathProperty描述符

```python
class DynamicPathProperty:
    """动态路径属性描述符，支持缓存"""
    
    def __init__(self, path_func, cache_duration=1.0):
        self.path_func = path_func
        self.cache_duration = cache_duration
        self._cache = {}
        self._cache_time = {}
    
    def __get__(self, obj, objtype=None):
        if obj is None:
            return self
        
        cache_key = id(obj)
        current_time = time.time()
        
        # 检查缓存
        if cache_key in self._cache:
            if current_time - self._cache_time[cache_key] < self.cache_duration:
                return self._cache[cache_key]
        
        # 生成新路径
        result = self.path_func(obj)
        self._cache[cache_key] = result
        self._cache_time[cache_key] = current_time
        
        return result
```

#### 3.2.2 TensorBoardDirDescriptor描述符

```python
class TensorBoardDirDescriptor:
    """tensorboard_dir描述符，确保始终等于tsb_logs_dir"""
    
    def __get__(self, obj, objtype=None):
        if obj is None:
            return self
        
        # 直接返回tsb_logs_dir的值
        return obj.tsb_logs_dir
    
    def __set__(self, obj, value):
        # 禁止设置，抛出异常
        raise AttributeError(
            "tensorboard_dir是只读属性，其值自动等于tsb_logs_dir。"
            "请通过设置work_dir或first_start_time来影响路径生成。"
        )
```

#### 3.2.3 路径生成函数

```python
def _generate_tsb_logs_dir(self) -> str:
    """生成TSB日志目录路径"""
    work_dir = self.get('work_dir', '')
    if not work_dir:
        return ''
    
    # 获取时间戳
    config_manager = self._get_root_manager()
    if config_manager and hasattr(config_manager, 'first_start_time'):
        timestamp = config_manager.first_start_time
    else:
        timestamp = datetime.now()
    
    # 使用ISO日历获取年和周数
    iso_year, iso_week, _ = timestamp.isocalendar()
    
    # 构建路径
    path_components = [
        work_dir,
        'tsb_logs',
        str(iso_year),
        f"{iso_week:02d}",
        timestamp.strftime('%m%d'),
        timestamp.strftime('%H%M%S')
    ]
    
    return os.path.join(*path_components)
```

### 3.3 PathsConfigNode实现

```python
class PathsConfigNode(ConfigNode):
    """特殊的paths配置节点，支持动态路径生成"""
    
    # 动态属性定义
    tsb_logs_dir = DynamicPathProperty(_generate_tsb_logs_dir)
    tensorboard_dir = TensorBoardDirDescriptor()
    
    def __init__(self, data=None, parent=None, key=None):
        super().__init__(data, parent, key)
        
        # 如果paths数据中有旧的tensorboard_dir配置，移除它
        if 'tensorboard_dir' in self._data:
            del self._data['tensorboard_dir']
```

### 3.4 集成到ConfigManagerCore

```python
class ConfigManagerCore(ConfigNode):
    
    def _ensure_paths_node(self):
        """确保paths节点是PathsConfigNode实例"""
        if 'paths' not in self._data:
            self._data['paths'] = {}
        
        # 如果paths不是PathsConfigNode实例，转换它
        if not isinstance(self._data.get('paths'), PathsConfigNode):
            paths_data = self._data.get('paths', {})
            self._data['paths'] = PathsConfigNode(
                data=paths_data,
                parent=self,
                key='paths'
            )
```

## 4. 缓存机制设计

### 4.1 缓存策略

- **缓存时长**：1秒
- **缓存键**：对象ID
- **缓存清理**：自动过期，无需手动清理

### 4.2 缓存优势

1. **性能提升**：避免频繁的路径计算
2. **一致性保证**：短时间内多次访问返回相同路径
3. **资源节省**：减少CPU使用

## 5. ISO周数说明

### 5.1 ISO 8601标准

- 每年的第一个周四所在的周为第1周
- 一年可能有52或53周
- 年初的某些天可能属于上一年的最后一周
- 年末的某些天可能属于下一年的第1周

### 5.2 实现示例

```python
from datetime import datetime

# 2025年1月1日（周三）属于2025年第1周
date1 = datetime(2025, 1, 1)
iso_year, iso_week, _ = date1.isocalendar()
print(f"{date1}: ISO {iso_year}年第{iso_week}周")  # 2025年第1周

# 2024年12月30日（周一）属于2025年第1周
date2 = datetime(2024, 12, 30)
iso_year, iso_week, _ = date2.isocalendar()
print(f"{date2}: ISO {iso_year}年第{iso_week}周")  # 2025年第1周
```

## 6. 错误处理

### 6.1 路径生成错误

- **work_dir未设置**：返回空字符串
- **时间戳无效**：使用当前时间
- **路径拼接失败**：记录错误，返回默认路径

### 6.2 属性访问错误

- **尝试设置tensorboard_dir**：抛出AttributeError
- **缓存失效**：重新生成路径

## 7. 测试要点

### 7.1 功能测试

1. 验证tsb_logs_dir生成正确的路径格式
2. 验证tensorboard_dir始终等于tsb_logs_dir
3. 验证tensorboard_dir不能被设置
4. 验证缓存机制正常工作

### 7.2 边界测试

1. 测试年初和年末的ISO周数
2. 测试不同时区的影响
3. 测试极端日期值

### 7.3 性能测试

1. 测试缓存命中率
2. 测试路径生成性能
3. 测试大量并发访问

## 8. 迁移指南

### 8.1 配置文件迁移

旧配置文件中的`tensorboard_dir`设置将被忽略：

```yaml
# 旧配置
paths:
  tensorboard_dir: /custom/path  # 将被忽略
  
# 新配置
paths:
  # tensorboard_dir自动生成，无需配置
```

### 8.2 代码迁移

```python
# 旧代码
config.paths.tensorboard_dir = "/custom/path"  # 不再支持

# 新代码
# tensorboard_dir自动等于tsb_logs_dir
print(config.paths.tensorboard_dir)  # 只读访问
```

## 9. 实现清单

1. **DynamicPathProperty**: 动态路径属性描述符（已实现）
2. **TensorBoardDirDescriptor**: tensorboard_dir描述符（已实现）
3. **PathsConfigNode**: 特殊的paths节点类（已实现）
4. **路径生成函数**: tsb_logs_dir生成逻辑（已实现）
5. **集成代码**: ConfigManagerCore集成（已实现）
6. **测试用例**: 完整的测试覆盖（已实现）

## 10. 总结

通过描述符模式和动态属性实现，成功实现了tsb_logs_dir和tensorboard_dir的统一化管理，确保了路径的一致性，同时通过缓存机制优化了性能。这种设计既满足了功能需求，又保持了代码的简洁性和可维护性。