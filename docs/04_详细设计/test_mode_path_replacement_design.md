# 测试模式路径与数据库地址选择功能详细设计文档

## 1. 功能概述

### 1.1 设计目标
在 `get_config_manager(test_mode=True)` 创建的临时配置副本中，通用路径逻辑只设置
`base_dir` 为测试环境路径；数据库配置采用固定键的窄例外，将预配置的
`database.test_address` 选择为活动 `database.address`。生产源文件保持不变。

### 1.2 核心特性
- **简化路径设置**：通用路径逻辑只设置 `base_dir` 为测试环境路径，不递归替换任意路径字段
- **固定数据库键**：`database.address` 是活动值，`database.test_address` 是测试预配置值
- **API 触发**：只有公开 API 的 `test_mode=True` 才执行临时副本转换
- **保持隔离**：测试副本与生产源文件完全分离，生产源内容不改变
- **格式一致**：标准格式与原始 YAML 使用相同的数据库地址选择规则
- **透明地址边界**：地址按不透明字符串处理，不解析、不记录、不连接数据库

## 2. 技术架构

### 2.1 核心组件

```
┌─────────────────────────────────────────────────────────────┐
│                  测试模式架构                                │
├─────────────────────────────────────────────────────────────┤
│  入口函数                                                   │
│  _setup_test_environment(test_config_path, first_start_time) │
├─────────────────────────────────────────────────────────────┤
│  测试环境设置                                               │
│  ┌─────────────────┐  ┌─────────────────┐                   │
│  │ 配置复制        │  │ base_dir设置     │                   │
│  │ _copy_production│  │ 测试路径设置     │                   │
│  │ _config_to_test │  │                 │                   │
│  └─────────────────┘  └─────────────────┘                   │
│  ┌─────────────────────────────────────────────────────────┐│
│  │ 固定键数据库选择：database.test_address -> address       ││
│  └─────────────────────────────────────────────────────────┘│
├─────────────────────────────────────────────────────────────┤
│  配置处理                                                   │
│  ┌─────────────────┐  ┌─────────────────┐                   │
│  │ YAML加载/保存    │  │ 格式兼容性      │                   │
│  │ PyYAML安全codec │  │ 标准/原始格式   │                   │
│  └─────────────────┘  └─────────────────┘                   │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 处理流程

```
配置文件加载
    ↓
配置复制到测试环境
    ↓
设置base_dir为测试路径
    ↓
若存在database节点，按固定键选择测试活动address
    ↓
调用setup_project_paths()
    ↓
基于测试base_dir生成其他路径
    ↓
配置文件保存
```

## 3. 核心算法设计

### 3.1 测试环境设置算法

#### 3.1.1 配置复制

`get_config_manager(test_mode=True)` 先把生产配置复制到临时路径，再在该副本上执行
转换。复制和保存统一经过 PyYAML>=6.0 安全 codec，保持标准格式、原始 YAML 数据语义和
测试地址选择规则；raw 首次保存时规范化为标准包络。注释、排版、引号以及 anchor/alias
表达不属于保真契约，生产源文件只读，不在源文件上选择测试地址。

#### 3.1.2 base_dir 与固定数据库键

复制后的转换按以下顺序执行：

0. `test_mode=False` 时不进入测试副本转换，生产 `database.address` 保持原值。
1. 按既有格式规则取得配置数据根：标准格式使用可变映射 `__data__`，原始 YAML 使用文档根。
2. 通用路径逻辑只把数据根的 `base_dir` 设置为测试路径；不递归扫描或替换其他路径字段。
3. 仅检查固定的 `database` 节点：节点不存在时 no-op；节点存在但不是映射时快速失败。
4. `database.test_address` 必须是非空字符串；有效时原样执行
   `database.address = database.test_address`，不要求原先存在 `address`。
5. 其他既有时间、配置文件路径和路径生成逻辑继续按原规则执行，并把成功转换后的副本交给配置加载。

伪代码（只表达固定契约，不构成新增公开 API）：

```python
def select_test_database_address(data_root):
    if "database" not in data_root:
        return
    database = data_root["database"]
    if not isinstance(database, MutableMapping):
        raise TestDatabaseConfigurationError("database must be a mapping in test_mode")
    test_address = database.get("test_address")
    if not isinstance(test_address, str) or not test_address.strip():
        raise TestDatabaseConfigurationError(
            "database.test_address must be a non-empty string in test_mode"
        )
    database["address"] = test_address
```

该 helper 只处理这两个固定键，不读取配置数据中的普通 `test_mode` 字段，也不引入通用
覆盖机制。

### 3.2 路径生成逻辑

`setup_project_paths()` 继续消费测试 `base_dir` 生成既有项目路径。这里的“路径配置”规则
与数据库地址选择分离：通用路径只改变 `base_dir` 并按既有逻辑生成派生目录，不对配置中的
任意字符串做递归替换；数据库选择是上节定义的固定键窄例外。

#### 3.2.1 基于base_dir的路径生成
```python
def setup_project_paths(self) -> None:
    """设置项目路径并自动创建目录"""
    # 1. 获取base_dir（支持多平台格式）
    base_dir = self.get('base_dir')
    if isinstance(base_dir, dict):
        # 多平台格式，选择当前平台路径
        current_os = self._get_current_os()
        base_dir = base_dir.get(current_os, base_dir.get('windows', ''))
    
    # 2. 生成其他路径
    project_name = self.get('project_name', 'default_project')
    experiment_name = self.get('experiment_name', 'default_experiment')
    
    # 3. 生成工作目录
    debug_mode = self.debug_mode
    if debug_mode:
        work_dir = os.path.join(base_dir, 'debug', project_name, experiment_name)
    else:
        work_dir = os.path.join(base_dir, project_name, experiment_name)
    
    # 4. 设置路径配置
    self.set('paths.work_dir', work_dir)
    
    # 5. 生成其他子目录
    self._generate_sub_directories(work_dir)
    
    # 6. 自动创建目录（仅_dir结尾字段）
    self._create_dirs_for_fields(self)
```

#### 3.2.2 子目录生成
```python
def _generate_sub_directories(self, work_dir: str) -> None:
    """生成子目录配置"""
    # 1. 检查点目录
    checkpoint_dir = os.path.join(work_dir, 'checkpoint')
    best_checkpoint_dir = os.path.join(checkpoint_dir, 'best')
    
    # 2. 调试目录
    debug_dir = os.path.join(work_dir, 'debug')
    
    # 3. 日志目录（基于时间）
    first_start_time = self.get('first_start_time')
    if first_start_time:
        date_str, time_str = self._parse_time_components(first_start_time)
    else:
        date_str, time_str = self._get_current_time_components()
    
    tsb_logs_dir = os.path.join(work_dir, 'tsb_logs', date_str, time_str)
    log_dir = os.path.join(work_dir, 'logs', date_str, time_str)
    
    # 4. 设置路径配置
    self.set('paths.checkpoint_dir', checkpoint_dir)
    self.set('paths.best_checkpoint_dir', best_checkpoint_dir)
    self.set('paths.debug_dir', debug_dir)
    self.set('paths.tsb_logs_dir', tsb_logs_dir)
    self.set('paths.log_dir', log_dir)
```

## 4. 配置示例

### 4.1 生产环境配置
```yaml
# 生产环境配置文件
__data__:
  base_dir: 'd:\logs'
  project_name: 'my_project'
  experiment_name: 'exp_001'
  first_start_time: '2025-01-08T10:00:00'
  config_file_path: 'd:\logs\config.yaml'
  database:
    address: 'production-address'
    test_address: 'test-address'
```

### 4.2 测试环境配置
```yaml
# 测试环境配置文件
__data__:
  base_dir: '/tmp/tests/20250108/100000'
  project_name: 'my_project'
  experiment_name: 'exp_001'
  first_start_time: '2025-01-08T10:00:00'
  config_file_path: '/tmp/tests/20250108/100000/config.yaml'
  paths:
    work_dir: '/tmp/tests/20250108/100000/my_project/exp_001'
    checkpoint_dir: '/tmp/tests/20250108/100000/my_project/exp_001/checkpoint'
    best_checkpoint_dir: '/tmp/tests/20250108/100000/my_project/exp_001/checkpoint/best'
    debug_dir: '/tmp/tests/20250108/100000/my_project/exp_001/debug'
    tsb_logs_dir: '/tmp/tests/20250108/100000/my_project/exp_001/tsb_logs/2025-01-08/100000'
    log_dir: '/tmp/tests/20250108/100000/my_project/exp_001/logs/2025-01-08/100000'
  database:
    address: 'test-address'       # 测试副本中的活动值
    test_address: 'test-address'  # 预配置值保持不变
```

### 4.3 原始 YAML 格式

原始 YAML 不包含 `__data__` 根节点，但使用完全相同的固定键和状态规则：

```yaml
# 生产源文件（原始格式）
database:
  address: 'production-address'
  test_address: 'test-address'

# test_mode=True 后的临时副本中，只有活动值被选择为测试值
```

若原始格式存在 `database` 映射且 `test_address` 有效，临时副本的
`database.address` 为 `'test-address'`；生产源文件中的两个键均保持不变。没有
`database` 节点时仍为 no-op。

## 5. 使用示例

### 5.1 基本使用
```python
from config_manager import get_config_manager

# 创建测试模式配置管理器
config = get_config_manager(test_mode=True, first_start_time='2025-01-08T10:00:00')

# 检查base_dir是否已设置为测试路径
print(config.get('base_dir'))  # /tmp/tests/20250108/100000

# 检查其他路径是否基于测试base_dir生成
print(config.paths.work_dir)  # /tmp/tests/20250108/100000/my_project/exp_001
print(config.paths.log_dir)   # /tmp/tests/20250108/100000/my_project/exp_001/logs/2025-01-08/100000

# database.address 是测试副本中的活动值；不要把地址写入日志或连接数据库
assert config.get('database.address') == 'test-address'
snapshot = config.get_serializable_data()
assert snapshot.get('database.address') == 'test-address'
```

### 5.2 调试模式使用
```python
# 在调试模式下，路径会自动调整
# 假设is_debug()返回True
print(config.debug_mode)  # True
print(config.paths.work_dir)  # /tmp/tests/20250108/100000/debug/my_project/exp_001
```

## 6. 错误处理

### 6.1 配置复制错误

复制阶段的文件不存在、YAML 解析和既有路径处理继续沿用原有测试环境语义。数据库固定键
校验使用专用配置错误，并在宽泛异常回退之前原样穿透；因此无效数据库节点或测试地址
不会触发“创建基本配置文件”的生产地址降级路径。

### 6.2 路径设置错误

固定数据库键的失败矩阵如下：

| 数据状态 | 结果 |
|---|---|
| 没有 `database` 节点 | no-op，继续既有加载 |
| `database` 不是映射 | 快速失败，实例不创建 |
| `test_address` 缺失、`None`、空字符串、空白字符串或非字符串 | 快速失败，实例不创建 |
| `test_address` 为非空字符串 | 原样设置临时副本的 `database.address` |

失败消息只包含稳定键路径和原因，例如 `database.test_address`，不得包含生产地址、测试
地址、完整配置或凭据。地址不被解析、格式化、网络验证或记录；本项目不加载数据库驱动，
也不创建数据库连接。无效值绝不回退到生产 `database.address`。

## 7. 性能优化

### 7.1 缓存机制
- **配置缓存**：避免重复加载配置文件
- **路径缓存**：缓存生成的路径配置
- **时间解析缓存**：缓存时间解析结果

### 7.2 延迟计算
- **路径生成延迟**：只在需要时生成路径配置
- **目录创建延迟**：只在需要时创建目录

## 8. 测试策略

### 8.1 单元测试
- **配置复制测试**：测试配置复制功能
- **base_dir设置测试**：测试base_dir设置功能
- **固定键地址选择测试**：验证 `database.test_address` 只在 `test_mode=True` 时成为活动 `database.address`
- **失败测试**：验证无效 `database` 节点或 `test_address` 快速失败且不回退生产地址
- **路径生成测试**：测试路径生成逻辑
- **双格式测试**：标准格式和原始 YAML 使用相同的地址选择规则
- **源文件与快照测试**：验证生产源不变，运行时和可序列化快照使用同一测试活动值

### 8.2 集成测试
- **测试模式集成测试**：测试与配置管理器的集成
- **路径配置管理器集成测试**：测试与路径配置管理器的集成
- **无数据库兼容测试**：验证没有 `database` 节点时保持 no-op

### 8.3 端到端测试
- **完整测试流程**：测试从生产配置到测试配置的完整流程
- **路径验证测试**：验证生成的路径是否正确
- **数据库连接边界测试**：仅验证配置选择与实例/快照数据，不解析地址、不验证端点、不建立数据库连接

## 9. 部署和维护

### 9.1 依赖管理
- **PyYAML>=6.0**：配置文件安全 codec 与数据语义处理
- **pathlib/os.path**：路径操作支持

### 9.2 配置管理
- **配置文件格式**：支持YAML格式
- **配置验证**：自动验证配置格式和内容
- **配置迁移**：支持配置格式升级

### 9.3 监控和日志
- **配置复制日志**：记录配置复制操作
- **路径设置日志**：记录路径设置操作
- **错误日志**：记录错误和异常的稳定原因，不记录任何数据库地址或完整配置

## 10. 总结

测试模式路径与数据库地址选择通过以下设计实现隔离且可观察的测试环境：

1. **API 触发**：只有 `get_config_manager(test_mode=True)` 进入临时副本转换。
2. **通用路径规则**：只设置 `base_dir`，不恢复递归路径替换或通用覆盖机制。
3. **固定键选择**：有效的 `database.test_address` 原样成为临时副本的活动 `database.address`。
4. **失败不降级**：无效节点或值快速失败，不创建实例，不回退生产地址。
5. **源文件不变**：生产配置保持不变；标准格式与原始 YAML 共享同一选择规则。
6. **运行时一致**：运行时配置和可序列化快照都使用测试活动值。
7. **数据库范围外**：地址不解析、不记录、不验证真实端点，不加载驱动或创建数据库连接。
