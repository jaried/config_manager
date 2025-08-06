# TSB日志路径功能测试套件总览

## 测试覆盖范围

本测试套件为TSB日志路径更新功能提供了全面的测试覆盖，包含以下测试类别：

### 1. 单元测试 (`tests/01_unit_tests/test_config_manager/`)

#### 1.1 周数格式测试 (`test_tsb_path_week_format.py`)
- **测试类**: `TestTsbPathWeekFormat`
- **测试内容**:
  - 周数格式为两位数字，不带W前缀
  - ISO周数计算的准确性
  - 年初年末的周数边界处理
  - 闰年的周数计算
  - 第53周的特殊情况
  - 周一作为一周第一天的验证
  - 路径中周数格式的一致性

#### 1.2 缓存机制测试 (`test_tsb_path_cache_mechanism.py`)
- **测试类**: `TestTsbPathCacheMechanism`
- **测试内容**:
  - 缓存持续时间为1秒
  - 缓存清理机制
  - 并发访问的线程安全性
  - 缓存性能指标（命中率、访问时间）
  - 不同实例间的缓存隔离
  - 动态时间戳时的缓存行为
  - 缓存内存效率

#### 1.3 只读属性测试 (`test_tensorboard_readonly_property.py`)
- **测试类**: `TestTensorBoardReadOnlyProperty`
- **测试内容**:
  - tensorboard_dir无法被设置
  - tensorboard_dir始终等于tsb_logs_dir
  - 描述符的__get__和__set__方法行为
  - 不同访问方式下的只读特性
  - 错误消息的清晰度
  - 属性值的持久性

#### 1.4 边界情况测试 (`test_tsb_path_edge_cases.py`)
- **测试类**: `TestTsbPathEdgeCases`
- **测试内容**:
  - 没有work_dir时的错误处理
  - 无效时间字符串的解析
  - 极端日期的处理（1970年、2100年等）
  - 特殊字符路径的处理
  - 并发缓存过期处理
  - 弱引用清理
  - 路径长度限制
  - work_dir改变时的缓存行为

### 2. 集成测试 (`tests/test_config_manager/`)

#### 2.1 路径功能集成测试 (`test_tsb_path_integration.py`)
- **测试类**: `TestTsbPathIntegration`
- **测试内容**:
  - 完整的路径生成工作流
  - 多进程环境下的路径一致性
  - 配置重新加载后的路径行为
  - 路径生成性能测试
  - 多线程并发访问
  - 大规模访问场景（10000次访问）

#### 2.2 跨平台兼容性测试 (`test_tsb_path_cross_platform.py`)
- **测试类**: `TestTsbPathCrossPlatform`
- **测试内容**:
  - Windows路径格式
  - Unix/Linux路径格式
  - os.path.join的跨平台一致性
  - Unicode路径支持
  - 网络路径（UNC）处理
  - 环境变量路径展开
  - 相对路径vs绝对路径
  - 路径分隔符一致性

### 3. 已有测试文件的覆盖

- `test_tsb_logs_path_generation.py`: 基本的TSB日志路径生成测试
- `test_unified_tensorboard_path.py`: 统一的TensorBoard路径测试
- `test_tensorboard_path_format.py`: TensorBoard路径格式测试

## 测试执行命令

### 运行完整测试套件
```bash
conda run -n base_python3.12 python -m pytest tests/ -k "tsb"
```

### 运行单元测试
```bash
# 周数格式测试
conda run -n base_python3.12 python -m pytest tests/01_unit_tests/test_config_manager/test_tsb_path_week_format.py -v

# 缓存机制测试
conda run -n base_python3.12 python -m pytest tests/01_unit_tests/test_config_manager/test_tsb_path_cache_mechanism.py -v

# 只读属性测试
conda run -n base_python3.12 python -m pytest tests/01_unit_tests/test_config_manager/test_tensorboard_readonly_property.py -v

# 边界情况测试
conda run -n base_python3.12 python -m pytest tests/01_unit_tests/test_config_manager/test_tsb_path_edge_cases.py -v
```

### 运行集成测试
```bash
# 功能集成测试
conda run -n base_python3.12 python -m pytest tests/test_config_manager/test_tsb_path_integration.py -v

# 跨平台测试
conda run -n base_python3.12 python -m pytest tests/test_config_manager/test_tsb_path_cross_platform.py -v
```

### 运行性能测试
```bash
conda run -n base_python3.12 python -m pytest tests/01_unit_tests/test_config_manager/test_tsb_path_cache_mechanism.py::TestTsbPathCacheMechanism::test_cache_performance_metrics -v -s

conda run -n base_python3.12 python -m pytest tests/test_config_manager/test_tsb_path_integration.py::TestTsbPathIntegration::test_path_generation_performance -v -s
```

## 测试覆盖的关键功能

1. **路径格式正确性**
   - 格式: `{work_dir}/tsb_logs/{yyyy}/{两位周数}/{mmdd}/{HHMMSS}`
   - 周数不带W前缀，使用ISO 8601标准

2. **tensorboard_dir只读特性**
   - 无法设置tensorboard_dir
   - tensorboard_dir始终等于tsb_logs_dir

3. **缓存机制**
   - 1秒缓存有效期
   - 线程安全
   - 内存效率

4. **跨平台兼容性**
   - Windows/Linux/macOS路径处理
   - Unicode支持
   - 路径规范化

5. **性能指标**
   - 缓存访问 < 0.01ms
   - 路径重新生成 < 1ms
   - 支持10000+并发访问

## 测试质量保证

- 所有测试遵循项目测试规范
- 使用`test_mode=True`确保测试隔离
- 包含正面和负面测试用例
- 覆盖正常流程和异常处理
- 性能基准测试
- 并发和多线程测试