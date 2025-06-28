# config_manager多进程支持概要设计

## 1. 设计概述

### 1.1 背景
config_manager原本不支持多进程环境，因为ConfigManager对象包含不可序列化的组件（线程锁、文件监视器、YAML解析器等），无法通过pickle传递给多进程worker。

### 1.2 设计目标
- 实现ConfigManager在多进程环境下的配置数据传递
- 保持API兼容性，不破坏现有功能
- 提供高性能的序列化解决方案
- 确保配置数据的完整性和一致性

### 1.3 解决方案架构

```
┌─────────────────────────────────────────────────────────────┐
│                    多进程配置传递架构                        │
├─────────────────────────────────────────────────────────────┤
│  主进程 (Main Process)                                      │
│  ┌─────────────────┐                                       │
│  │ ConfigManager   │  get_serializable_data()              │
│  │  ├─ 线程锁      │ ──────────────────────────────────────┐│
│  │  ├─ 文件监视器  │                                       ││
│  │  ├─ YAML解析器  │                                       ││
│  │  └─ 配置数据    │                                       ││
│  └─────────────────┘                                       ││
├─────────────────────────────────────────────────────────────┤│
│  序列化层 (Serialization Layer)                              ││
│  ┌─────────────────┐                                       ││
│  │SerializableConfigData│ ←──────────────────────────────────┘│
│  │  ├─ 配置数据    │                                        │
│  │  ├─ 类型提示    │  pickle.dumps()                       │
│  │  └─ 路径信息    │ ──────────────────────────────────────┐│
│  └─────────────────┘                                       ││
├─────────────────────────────────────────────────────────────┤│
│  进程间传输 (Inter-Process Transfer)                          ││
│  ┌─────────────────┐                                       ││
│  │ Pickle Stream   │ ←──────────────────────────────────────┘│
│  │ (Binary Data)   │                                        │
│  └─────────────────┘                                        │
├─────────────────────────────────────────────────────────────┤
│  Worker进程 (Worker Processes)                              │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐│
│  │ Worker 1        │  │ Worker 2        │  │ Worker N        ││
│  │ ┌─────────────┐ │  │ ┌─────────────┐ │  │ ┌─────────────┐ ││
│  │ │SerializableConfigData│ │SerializableConfigData│ │SerializableConfigData│ ││
│  │ │ pickle.loads()│ │  │ │ pickle.loads()│ │  │ │ pickle.loads()│ ││
│  │ │配置数据访问 │ │  │ │配置数据访问 │ │  │ │配置数据访问 │ ││
│  │ └─────────────┘ │  │ └─────────────┘ │  │ └─────────────┘ ││
│  └─────────────────┘  └─────────────────┘  └─────────────────┘│
└─────────────────────────────────────────────────────────────┘
```

## 2. 核心组件设计

### 2.1 SerializableConfigData类

#### 2.1.1 类结构
```python
class SerializableConfigData:
    def __init__(self, data: Dict[str, Any], type_hints: Dict[str, str], config_path: str)
    
    # 数据访问接口
    def __getattr__(self, name: str) -> Any
    def __getitem__(self, key: str) -> Any
    def get(self, key: str, default: Any = None, as_type: Type = None) -> Any
    
    # 数据修改接口（仅用于worker内部）
    def set(self, key: str, value: Any, type_hint: Type = None)
    def update(self, other: Dict[str, Any])
    
    # 工具方法
    def to_dict(self) -> Dict[str, Any]
    def is_serializable(self) -> bool
    def clone(self) -> SerializableConfigData
```

#### 2.1.2 设计特点
- **纯数据结构**：仅包含配置数据、类型提示和路径信息
- **完全可序列化**：无任何不可pickle的组件
- **API兼容**：与ConfigManager保持相同的访问接口
- **轻量级**：内存占用小，序列化快速

#### 2.1.3 数据存储结构
```python
{
    '_data': {           # 配置数据
        'app_name': 'MyApp',
        'database': {
            'host': 'localhost',
            'port': 5432
        },
        'paths': {
            'data_dir': '/tmp/data',
            'log_dir': '/tmp/logs'
        }
    },
    '_type_hints': {     # 类型提示
        'app_name': 'str',
        'database.port': 'int'
    },
    '_config_path': 'config.yaml'  # 原始配置文件路径
}
```

### 2.2 ConfigManagerCore扩展

#### 2.2.1 新增方法
```python
class ConfigManagerCore:
    def get_serializable_data(self) -> SerializableConfigData:
        """获取可序列化的配置数据"""
        
    def create_serializable_snapshot(self) -> SerializableConfigData:
        """创建配置快照"""
        
    def is_pickle_serializable(self) -> bool:
        """检查对象是否可序列化"""
```

#### 2.2.2 实现逻辑
```python
def get_serializable_data(self):
    from ..serializable_config import create_serializable_config
    return create_serializable_config(self)
```

### 2.3 工厂函数

#### 2.3.1 create_serializable_config函数
```python
def create_serializable_config(config_manager) -> SerializableConfigData:
    """从ConfigManager创建可序列化的配置数据"""
    data = config_manager.to_dict()
    type_hints = getattr(config_manager, '_type_hints', {})
    config_path = getattr(config_manager, '_config_path', None)
    
    return SerializableConfigData(
        data=data,
        type_hints=type_hints,
        config_path=config_path
    )
```

## 3. 接口设计

### 3.1 用户接口

#### 3.1.1 基本使用流程
```python
# 1. 创建配置管理器
config = get_config_manager("config.yaml", watch=False)

# 2. 设置配置
config.app_name = "MyApp"
config.database = {'host': 'localhost', 'port': 5432}

# 3. 获取可序列化配置
serializable_config = config.get_serializable_data()

# 4. 多进程使用
def worker_function(config_data):
    app_name = config_data.app_name
    db_host = config_data.database.host
    return process_data(app_name, db_host)

with mp.Pool(processes=4) as pool:
    results = pool.map(worker_function, [serializable_config] * 4)
```

#### 3.1.2 配置访问方式
```python
# 属性访问
app_name = config_data.app_name

# 字典访问
version = config_data['version']

# get方法（支持默认值）
batch_size = config_data.get('processing.batch_size', 100)

# 嵌套访问
log_dir = config_data.get('paths.log_dir', '/tmp/logs')

# 类型转换
timeout = config_data.get('timeout', 30, as_type=int)
```

### 3.2 内部接口

#### 3.2.1 序列化接口
```python
class SerializableConfigData:
    def __getstate__(self) -> Dict:
        """pickle序列化状态"""
        return {
            'data': self._data,
            'type_hints': self._type_hints,
            'config_path': self._config_path
        }
    
    def __setstate__(self, state: Dict):
        """pickle反序列化状态"""
        self._data = state['data']
        self._type_hints = state['type_hints']
        self._config_path = state['config_path']
```

## 4. 数据流设计

### 4.1 序列化流程

```
ConfigManager
    ↓ to_dict()
配置数据字典
    ↓ create_serializable_config()
SerializableConfigData对象
    ↓ pickle.dumps()
二进制数据流
    ↓ 多进程传输
Worker进程接收
    ↓ pickle.loads()
SerializableConfigData对象
    ↓ 配置访问
Worker业务逻辑
```

### 4.2 数据转换规则

#### 4.2.1 支持的数据类型
- 基本类型：str, int, float, bool, None
- 容器类型：list, tuple, dict
- 嵌套结构：ConfigNode → dict
- 特殊处理：Path → str

#### 4.2.2 不支持的数据类型
- 函数对象
- 线程锁
- 文件句柄
- 正则表达式对象
- 其他不可pickle的对象

### 4.3 错误处理

#### 4.3.1 序列化错误
```python
def get_serializable_data(self):
    try:
        serializable = create_serializable_config(self)
        # 验证可序列化性
        pickle.dumps(serializable)
        return serializable
    except Exception as e:
        raise SerializationError(f"配置数据序列化失败: {e}")
```

#### 4.3.2 访问错误
```python
def __getattr__(self, name: str) -> Any:
    if name in self._data:
        return self._data[name]
    raise AttributeError(f"配置项 '{name}' 不存在")
```

## 5. 性能设计

### 5.1 性能目标
- 序列化时间：< 100ms（100个配置项）
- 内存占用：< 50%（相对于原ConfigManager）
- 访问性能：与原ConfigManager相当

### 5.2 性能优化

#### 5.2.1 数据结构优化
- 使用简单的dict存储，避免复杂对象
- 延迟创建嵌套的SerializableConfigData对象
- 最小化序列化数据大小

#### 5.2.2 访问优化
```python
def __getattr__(self, name: str) -> Any:
    if name.startswith('_'):
        return super().__getattribute__(name)
    
    if name in self._data:
        value = self._data[name]
        # 延迟创建嵌套对象
        if isinstance(value, dict):
            return SerializableConfigData(value)
        return value
    
    raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")
```

## 6. 安全设计

### 6.1 数据隔离
- 序列化数据是配置的只读快照
- worker进程对配置的修改不影响主进程
- 每个worker获得独立的配置数据副本

### 6.2 类型安全
- 保留原始类型提示信息
- 支持类型转换和验证
- 提供类型检查方法

### 6.3 错误隔离
- 序列化错误不影响ConfigManager正常功能
- worker进程的配置访问错误不传播到主进程
- 提供详细的错误信息和堆栈跟踪

## 7. 兼容性设计

### 7.1 向后兼容
- 现有ConfigManager API完全保持不变
- 新增方法不影响现有功能
- 可选的多进程支持

### 7.2 平台兼容
- 支持Windows、Linux、macOS
- 兼容不同的多进程启动方法（fork、spawn）
- 处理平台特定的路径格式

### 7.3 版本兼容
- 支持Python 3.8+
- 兼容pickle协议的不同版本
- 处理序列化数据的版本差异

## 8. 监控和调试

### 8.1 性能监控
```python
def get_serializable_data(self):
    start_time = time.time()
    try:
        result = create_serializable_config(self)
        serialized = pickle.dumps(result)
        
        # 性能统计
        serialize_time = time.time() - start_time
        data_size = len(serialized)
        
        if serialize_time > 0.1:  # 超过100ms记录警告
            print(f"警告: 配置序列化耗时 {serialize_time:.3f}s")
        
        return result
    except Exception as e:
        print(f"配置序列化失败: {e}")
        raise
```

### 8.2 调试支持
```python
class SerializableConfigData:
    def debug_info(self) -> Dict:
        """获取调试信息"""
        return {
            'data_keys': list(self._data.keys()),
            'type_hints_count': len(self._type_hints),
            'config_path': self._config_path,
            'is_serializable': self.is_serializable(),
            'data_size': len(str(self._data))
        }
``` 