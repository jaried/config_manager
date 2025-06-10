# 路径配置模块详细设计文档

## 1. 设计概述

### 1.1 设计目标
为配置管理器增加标准化的路径配置功能，支持机器学习项目的路径管理需求，提供调试模式和生产模式的路径隔离。

### 1.2 核心特性
- **debug_mode动态属性**：`config.debug_mode`动态返回`is_debug()`结果，不存储在配置文件中
- **调试模式集成**：自动检测和配置调试模式
- **标准化路径结构**：提供统一的项目路径组织方案
- **时间基础目录**：基于启动时间生成日志目录
- **跨平台兼容**：支持Windows、Linux、macOS路径格式
- **自动目录创建**：路径配置时自动创建对应目录结构
- **智能路径检测**：自动识别路径相关配置并创建目录

## 2. 技术架构

### 2.1 模块结构

```
┌─────────────────────────────────────────────────────────────┐
│                  路径配置模块架构                            │
├─────────────────────────────────────────────────────────────┤
│  接口层 (Interface Layer)                                   │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │ PathConfigurationManager                                │ │
│  │ + initialize_path_configuration()                       │ │
│  │ + update_debug_mode()                                   │ │
│  │ + generate_all_paths()                                  │ │
│  └─────────────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────────┤
│  核心逻辑层 (Core Logic Layer)                              │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐        │
│  │DebugDetector │ │PathGenerator │ │TimeProcessor │        │
│  │  调试检测    │ │  路径生成    │ │  时间处理    │        │
│  └──────────────┘ └──────────────┘ └──────────────┘        │
├─────────────────────────────────────────────────────────────┤
│  工具层 (Utility Layer)                                    │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐        │
│  │PathValidator │ │DirectoryCreator│ │ConfigUpdater │        │
│  │  路径验证    │ │  目录创建    │ │  配置更新    │        │
│  └──────────────┘ └──────────────┘ └──────────────┘        │
├─────────────────────────────────────────────────────────────┤
│  外部依赖层 (External Dependencies)                         │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐        │
│  │   is_debug   │ │   pathlib    │ │   datetime   │        │
│  │   模块       │ │   路径处理   │ │   时间处理   │        │
│  └──────────────┘ └──────────────┘ └──────────────┘        │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 处理流程

```
配置管理器初始化
    ↓
调用initialize_path_configuration()
    ↓
检测调试模式（is_debug()）
    ↓
设置debug_mode配置项
    ↓
解析基础配置（base_dir, project_name, experiment_name）
    ↓
生成工作目录路径
    ├── 调试模式：base_dir/debug/project_name/experiment_name
    └── 生产模式：base_dir/project_name/experiment_name
    ↓
解析时间组件（first_start_time）
    ├── 提取日期（YYYY-MM-DD）
    └── 提取时间（HHMMSS）
    ↓
生成子目录路径
    ├── paths.checkpoint_dir: paths.work_dir/checkpoint/
    ├── paths.best_checkpoint_dir: paths.work_dir/checkpoint/best
    ├── paths.debug_dir: paths.work_dir/debug/
    ├── paths.tsb_logs_dir: paths.work_dir/tsb_logs/date/time
    └── paths.log_dir: paths.work_dir/logs/date/time
    ↓
验证路径配置
    ↓
自动创建所有路径目录
    ↓
更新配置数据
    ↓
保存配置
```

## 3. 核心组件设计

### 3.1 ConfigNode debug_mode动态属性设计

在ConfigNode的`__getattr__`方法中特殊处理`debug_mode`属性：

```python
def __getattr__(self, name: str) -> Any:
    """通过属性访问值（属性不存在时抛出AttributeError）"""
    if '_data' not in super().__getattribute__('__dict__'):
        raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")

    # 特殊处理debug_mode：动态从is_debug()获取
    if name == 'debug_mode':
        try:
            from is_debug import is_debug
            return is_debug()
        except ImportError:
            # 如果is_debug模块不可用，默认为生产模式
            return False

    data = super().__getattribute__('_data')
    if name in data:
        return data[name]
    raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")
```

**设计优势**：
- 始终反映当前运行环境的调试状态
- 避免配置文件与实际环境不一致
- 简化配置管理逻辑
- 外部调用`config.debug_mode`时不会出现AttributeError

### 3.2 PathConfigurationManager 类

主要的路径配置管理器，负责协调所有路径配置操作。

```python
class PathConfigurationManager:
    """路径配置管理器"""
    
    def __init__(self, config_manager):
        """初始化路径配置管理器
        
        Args:
            config_manager: 配置管理器实例
        """
        self._config_manager = config_manager
        self._debug_detector = DebugDetector()
        self._path_generator = PathGenerator()
        self._time_processor = TimeProcessor()
        self._path_validator = PathValidator()
        self._directory_creator = DirectoryCreator()
        self._config_updater = ConfigUpdater(config_manager)
    
    def initialize_path_configuration(self) -> None:
        """初始化路径配置"""
        
    def update_debug_mode(self) -> None:
        """更新调试模式状态"""
        
    def generate_all_paths(self) -> dict[str, str]:
        """生成所有路径配置"""
        
    def validate_path_configuration(self) -> bool:
        """验证路径配置"""
        
    def create_directories(self, create_all: bool = False) -> None:
        """创建目录结构"""
```

### 3.2 DebugDetector 类

调试模式检测器，负责集成is_debug模块。

```python
class DebugDetector:
    """调试模式检测器"""
    
    @staticmethod
    def detect_debug_mode() -> bool:
        """检测当前是否为调试模式
        
        Returns:
            bool: True表示调试模式，False表示生产模式
        """
        try:
            from is_debug import is_debug
            return is_debug()
        except ImportError as e:
            # 如果is_debug模块不可用，默认为生产模式
            return False
    
    @staticmethod
    def get_debug_status_info() -> dict[str, any]:
        """获取调试状态信息
        
        Returns:
            dict: 包含调试状态和相关信息的字典
        """
```

### 3.3 PathGenerator 类

路径生成器，负责生成各种路径配置。

```python
class PathGenerator:
    """路径生成器"""
    
    def generate_work_directory(
        self, 
        base_dir: str, 
        project_name: str, 
        experiment_name: str, 
        debug_mode: bool
    ) -> str:
        """生成工作目录路径
        
        Args:
            base_dir: 基础目录
            project_name: 项目名称
            experiment_name: 实验名称
            debug_mode: 是否为调试模式
            
        Returns:
            str: 工作目录路径
        """
    
    def generate_checkpoint_directories(self, work_dir: str) -> dict[str, str]:
        """生成检查点目录路径
        
        Args:
            work_dir: 工作目录
            
        Returns:
            dict: 检查点目录路径字典
        """
    
    def generate_debug_directory(self, work_dir: str) -> dict[str, str]:
        """生成调试目录路径
        
        Args:
            work_dir: 工作目录
            
        Returns:
            dict: 调试目录路径字典
        """
    
    def generate_log_directories(
        self, 
        work_dir: str, 
        date_str: str, 
        time_str: str
    ) -> dict[str, str]:
        """生成日志目录路径
        
        Args:
            work_dir: 工作目录
            date_str: 日期字符串（YYYY-MM-DD）
            time_str: 时间字符串（HHMMSS）
            
        Returns:
            dict: 日志目录路径字典
        """
```

### 3.4 TimeProcessor 类

时间处理器，负责解析和格式化时间信息。

```python
class TimeProcessor:
    """时间处理器"""
    
    @staticmethod
    def parse_first_start_time(first_start_time: str) -> tuple[str, str]:
        """解析首次启动时间
        
        Args:
            first_start_time: ISO格式的时间字符串
            
        Returns:
            tuple: (日期字符串, 时间字符串)
        """
    
    @staticmethod
    def format_date(dt: datetime) -> str:
        """格式化日期
        
        Args:
            dt: datetime对象
            
        Returns:
            str: YYYY-MM-DD格式的日期字符串
        """
    
    @staticmethod
    def format_time(dt: datetime) -> str:
        """格式化时间
        
        Args:
            dt: datetime对象
            
        Returns:
            str: HHMMSS格式的时间字符串
        """
    
    @staticmethod
    def get_current_time_components() -> tuple[str, str]:
        """获取当前时间组件
        
        Returns:
            tuple: (日期字符串, 时间字符串)
        """
```

### 3.5 PathValidator 类

路径验证器，负责验证路径配置的有效性。

```python
class PathValidator:
    """路径验证器"""
    
    @staticmethod
    def validate_base_dir(base_dir: str) -> bool:
        """验证基础目录
        
        Args:
            base_dir: 基础目录路径
            
        Returns:
            bool: 验证结果
        """
    
    @staticmethod
    def validate_path_format(path: str) -> bool:
        """验证路径格式
        
        Args:
            path: 路径字符串
            
        Returns:
            bool: 验证结果
        """
    
    @staticmethod
    def validate_directory_permissions(path: str) -> bool:
        """验证目录权限
        
        Args:
            path: 目录路径
            
        Returns:
            bool: 权限验证结果
        """
```

### 3.6 DirectoryCreator 类

目录创建器，负责创建必要的目录结构。

```python
class DirectoryCreator:
    """目录创建器"""
    
    @staticmethod
    def create_directory(path: str, exist_ok: bool = True) -> bool:
        """创建目录
        
        Args:
            path: 目录路径
            exist_ok: 目录已存在时是否报错
            
        Returns:
            bool: 创建结果
        """
    
    def create_path_structure(self, paths: dict[str, str]) -> dict[str, bool]:
        """创建路径结构
        
        Args:
            paths: 路径配置字典
            
        Returns:
            dict: 创建结果字典
        """
```

### 3.7 ConfigUpdater 类

配置更新器，负责更新配置管理器中的路径配置。

```python
class ConfigUpdater:
    """配置更新器"""
    
    def __init__(self, config_manager):
        """初始化配置更新器
        
        Args:
            config_manager: 配置管理器实例
        """
        self._config_manager = config_manager
    
    def update_path_configurations(self, path_configs: dict[str, str]) -> None:
        """更新路径配置
        
        Args:
            path_configs: 路径配置字典
        """
    
    def update_debug_mode(self, debug_mode: bool) -> None:
        """更新调试模式配置
        
        Args:
            debug_mode: 调试模式标志
        """
```

## 4. 配置字段设计

### 4.1 核心配置字段

```yaml
# 调试模式配置
debug_mode: false  # 由is_debug()自动设置

# 基础路径配置
base_dir: 'd:\logs'  # 基础存储路径

# 项目配置
project_name: 'my_project'  # 项目名称
experiment_name: 'exp_001'  # 实验名称

# 时间配置
first_start_time: '2025-01-08T10:00:00'  # 首次启动时间

# 自动生成的路径配置
work_dir: ''  # 工作目录
checkpoint_dir: ''  # 检查点目录
best_checkpoint_dir: ''  # 最佳检查点目录
tsb_logs_dir: ''  # TensorBoard日志目录
logs_dir: ''  # 普通日志目录
```

### 4.2 字段类型定义

```python
# 类型提示配置
__type_hints__:
  debug_mode: bool
  base_dir: Path
  project_name: str
  experiment_name: str
  first_start_time: str
  paths:
    work_dir: Path
    checkpoint_dir: Path
    best_checkpoint_dir: Path
    debug_dir: Path
    tsb_logs_dir: Path
    log_dir: Path
```

### 4.3 默认值配置

```python
DEFAULT_PATH_CONFIG = {
    'debug_mode': False,
    'base_dir': 'd:\\logs',  # Windows默认
    'project_name': 'default_project',
    'experiment_name': 'default_experiment',
    'first_start_time': None,  # 自动生成
    'paths': {
        'work_dir': '',  # 自动生成，通过config.paths.work_dir访问
        'checkpoint_dir': '',  # 自动生成，通过config.paths.checkpoint_dir访问
        'best_checkpoint_dir': '',  # 自动生成，通过config.paths.best_checkpoint_dir访问
        'debug_dir': '',  # 自动生成，通过config.paths.debug_dir访问
        'tsb_logs_dir': '',  # 自动生成，通过config.paths.tsb_logs_dir访问
        'log_dir': '',  # 自动生成，通过config.paths.log_dir访问
    }
}
```

## 5. 路径生成算法

### 5.1 工作目录生成算法

```python
def generate_work_directory(base_dir, project_name, experiment_name, debug_mode):
    """工作目录生成算法"""
    # 标准化路径分隔符
    base_dir = Path(base_dir)
    
    # 构建路径组件
    path_components = [base_dir]
    
    # 调试模式添加debug标识
    if debug_mode:
        path_components.append('debug')
    
    # 添加项目名称和实验名称
    path_components.extend([project_name, experiment_name])
    
    # 生成最终路径
    work_dir = Path(*path_components)
    
    return str(work_dir)
```

### 5.2 时间目录生成算法

```python
def generate_time_based_directory(work_dir, base_name, date_str, time_str):
    """基于时间的目录生成算法"""
    work_path = Path(work_dir)
    time_dir = work_path / base_name / date_str / time_str
    return str(time_dir)
```

### 5.3 检查点目录生成算法

```python
def generate_checkpoint_directories(work_dir):
    """检查点目录生成算法"""
    work_path = Path(work_dir)
    
    checkpoint_dirs = {
        'checkpoint_dir': str(work_path / 'checkpoint'),
        'best_checkpoint_dir': str(work_path / 'checkpoint' / 'best')
    }
    
    return checkpoint_dirs
```

### 5.4 调试目录生成算法

```python
def generate_debug_directory(work_dir):
    """调试目录生成算法"""
    work_path = Path(work_dir)
    
    debug_dirs = {
        'debug_dir': str(work_path / 'debug')
    }
    
    return debug_dirs
```

## 6. 集成设计

### 6.1 与ConfigManager集成

```python
# 在ConfigManagerCore中集成路径配置
class ConfigManagerCore:
    def __init__(self, config_path: str = None):
        # ... 现有初始化代码 ...
        self._path_config_manager = None
    
    def initialize(self):
        """初始化配置管理器"""
        # ... 现有初始化代码 ...
        
        # 初始化路径配置
        self._initialize_path_configuration()
    
    def _initialize_path_configuration(self):
        """初始化路径配置"""
        self._path_config_manager = PathConfigurationManager(self)
        self._path_config_manager.initialize_path_configuration()
```

### 6.2 配置更新触发

```python
def set(self, key: str, value: any) -> None:
    """设置配置值"""
    # ... 现有设置逻辑 ...
    
    # 检查是否需要更新路径配置
    if self._should_update_path_config(key):
        self._path_config_manager.generate_all_paths()
    
def _should_update_path_config(self, key: str) -> bool:
    """判断是否需要更新路径配置"""
    path_related_keys = [
        'base_dir', 'project_name', 'experiment_name', 
        'first_start_time', 'debug_mode'
    ]
    return key in path_related_keys
```

## 7. 错误处理设计

### 7.1 异常类型定义

```python
class PathConfigurationError(Exception):
    """路径配置错误基类"""
    pass

class InvalidPathError(PathConfigurationError):
    """无效路径错误"""
    pass

class DirectoryCreationError(PathConfigurationError):
    """目录创建错误"""
    pass

class PermissionError(PathConfigurationError):
    """权限错误"""
    pass

class TimeParsingError(PathConfigurationError):
    """时间解析错误"""
    pass
```

### 7.2 错误处理策略

```python
def initialize_path_configuration(self):
    """初始化路径配置（带错误处理）"""
    try:
        # 检测调试模式
        debug_mode = self._debug_detector.detect_debug_mode()
        self._config_updater.update_debug_mode(debug_mode)
        
        # 生成路径配置
        path_configs = self.generate_all_paths()
        
        # 验证路径配置
        if not self.validate_path_configuration():
            raise PathConfigurationError("路径配置验证失败")
        
        # 更新配置
        self._config_updater.update_path_configurations(path_configs)
        
    except ImportError:
        # is_debug模块不可用，使用默认值
        self._handle_is_debug_import_error()
    except (OSError, PermissionError) as e:
        # 路径相关错误
        raise DirectoryCreationError(f"目录操作失败: {e}")
    except ValueError as e:
        # 时间解析错误
        raise TimeParsingError(f"时间解析失败: {e}")
```

## 8. 测试设计

### 8.1 单元测试覆盖

```python
class TestPathConfigurationManager:
    """路径配置管理器测试"""
    
    def test_debug_mode_detection(self):
        """测试调试模式检测"""
        
    def test_work_directory_generation(self):
        """测试工作目录生成"""
        
    def test_checkpoint_directories_generation(self):
        """测试检查点目录生成"""
        
    def test_log_directories_generation(self):
        """测试日志目录生成"""
        
    def test_time_parsing(self):
        """测试时间解析"""
        
    def test_path_validation(self):
        """测试路径验证"""
        
    def test_directory_creation(self):
        """测试目录创建"""
        
    def test_error_handling(self):
        """测试错误处理"""
```

### 8.2 集成测试设计

```python
class TestPathConfigurationIntegration:
    """路径配置集成测试"""
    
    def test_full_path_configuration_flow(self):
        """测试完整路径配置流程"""
        
    def test_debug_production_mode_switching(self):
        """测试调试/生产模式切换"""
        
    def test_configuration_persistence(self):
        """测试配置持久化"""
        
    def test_cross_platform_compatibility(self):
        """测试跨平台兼容性"""
```

## 9. 性能优化

### 9.1 缓存策略

```python
class PathConfigurationManager:
    def __init__(self, config_manager):
        # ... 现有代码 ...
        self._path_cache = {}
        self._cache_valid = False
    
    def generate_all_paths(self) -> dict[str, str]:
        """生成所有路径配置（带缓存）"""
        if self._cache_valid and self._path_cache:
            return self._path_cache.copy()
        
        # 生成路径配置
        path_configs = self._generate_paths_internal()
        
        # 更新缓存
        self._path_cache = path_configs.copy()
        self._cache_valid = True
        
        return path_configs
    
    def invalidate_cache(self):
        """使缓存失效"""
        self._cache_valid = False
```

### 9.2 延迟初始化

```python
def _initialize_path_configuration(self):
    """延迟初始化路径配置"""
    if self._path_config_manager is None:
        self._path_config_manager = PathConfigurationManager(self)
    
    # 只在需要时初始化路径配置
    if self._should_initialize_paths():
        self._path_config_manager.initialize_path_configuration()
```

## 10. 扩展性设计

### 10.1 插件接口

```python
class PathConfigurationPlugin:
    """路径配置插件基类"""
    
    def generate_custom_paths(self, base_config: dict) -> dict[str, str]:
        """生成自定义路径配置"""
        raise NotImplementedError
    
    def validate_custom_paths(self, paths: dict[str, str]) -> bool:
        """验证自定义路径配置"""
        raise NotImplementedError
```

### 10.2 配置模板

```python
class PathConfigurationTemplate:
    """路径配置模板"""
    
    ML_PROJECT_TEMPLATE = {
        'work_dir': '{base_dir}/{debug_prefix}{project_name}/{experiment_name}',
        'data_dir': '{work_dir}/data',
        'model_dir': '{work_dir}/models',
        'checkpoint_dir': '{work_dir}/checkpoint',
        'logs_dir': '{work_dir}/logs/{date}/{time}',
        'results_dir': '{work_dir}/results',
    }
    
    WEB_PROJECT_TEMPLATE = {
        'work_dir': '{base_dir}/{debug_prefix}{project_name}',
        'static_dir': '{work_dir}/static',
        'uploads_dir': '{work_dir}/uploads',
        'logs_dir': '{work_dir}/logs/{date}',
        'cache_dir': '{work_dir}/cache',
    }
```

## 11. 自动目录创建设计

### 11.1 设计目标

自动目录创建功能旨在确保配置的路径在使用时目录已存在，避免外部模块因目录不存在而出错。

### 11.2 触发机制

```python
# 1. 直接设置路径配置时触发
config.set('paths.log_dir', '/path/to/logs')  # 自动创建目录，通过config.paths.log_dir访问

# 2. 路径配置管理器批量更新时触发
path_configs = manager.generate_all_paths()  # 自动创建所有路径

# 3. 路径关键词检测触发
config.set('data_dir', '/path/to/data')  # 检测到路径关键词，自动创建，通过config.data_dir访问
```

### 11.3 路径识别策略

```python
def _is_path_configuration(self, key: str, value: Any) -> bool:
    """判断是否为路径配置"""
    # 1. 检查是否为字符串类型
    if not isinstance(value, str):
        return False
    
    # 2. 检查是否为paths命名空间
    if key.startswith('paths.'):
        return True
    
    # 3. 检查字段名是否包含路径关键词
    path_keywords = ['dir', 'path', 'directory', 'folder', 'location', 'root', 'base']
    key_lower = key.lower()
    if any(keyword in key_lower for keyword in path_keywords):
        return self._looks_like_path(value)
    
    return False

def _looks_like_path(self, value: str) -> bool:
    """判断字符串是否像路径"""
    if not value:
        return False
    
    # 检查是否包含路径分隔符
    if '/' in value or '\\' in value:
        return True
    
    # 检查是否为Windows盘符格式
    if len(value) >= 2 and value[1] == ':':
        return True
    
    return False
```

### 11.4 目录创建实现

```python
class DirectoryCreator:
    """目录创建器"""
    
    @staticmethod
    def create_directory(path: str, exist_ok: bool = True) -> bool:
        """创建目录"""
        try:
            Path(path).mkdir(parents=True, exist_ok=exist_ok)
            return True
        except (OSError, PermissionError):
            return False
    
    def create_path_structure(self, paths: Dict[str, str]) -> Dict[str, bool]:
        """创建路径结构"""
        results = {}
        for key, path in paths.items():
            if path and isinstance(path, str):
                results[key] = self.create_directory(path)
            else:
                results[key] = False
        return results
```

### 11.5 集成点设计

#### 11.5.1 ConfigManagerCore.set() 方法集成

```python
def set(self, key: str, value: Any, autosave: bool = True, type_hint: Type = None):
    """设置配置值并自动创建目录"""
    # ... 现有逻辑 ...
    
    # 检查是否为路径配置，如果是则自动创建目录
    if self._is_path_configuration(key, value):
        self._create_directory_for_path(key, value)
    
    # ... 继续现有逻辑 ...
```

#### 11.5.2 ConfigUpdater.update_path_configurations() 方法集成

```python
def update_path_configurations(self, path_configs: Dict[str, str]) -> None:
    """更新路径配置并自动创建目录"""
    # 首先创建所有目录
    creation_results = self._directory_creator.create_path_structure(path_configs)
    
    # 记录目录创建结果
    for key, success in creation_results.items():
        if not success:
            print(f"警告: 目录创建失败 {key}: {path_configs.get(key)}")
    
    # 然后设置配置值
    for key, value in path_configs.items():
        self._config_manager.set(key, value)
```

#### 11.5.3 PathConfigurationManager._update_path_configuration() 方法集成

```python
def _update_path_configuration(self) -> None:
    """更新路径配置并自动创建目录"""
    if self._path_config_manager:
        try:
            # 生成路径配置
            path_configs = self._path_config_manager.generate_all_paths()
            
            # 首先创建所有目录
            from .path_configuration import DirectoryCreator
            directory_creator = DirectoryCreator()
            creation_results = directory_creator.create_path_structure(path_configs)
            
            # 然后设置配置值
            for path_key, path_value in path_configs.items():
                self._data[path_key] = path_value
                # ... 设置到paths命名空间 ...
        except Exception as e:
            print(f"路径配置更新失败: {e}")
```

### 11.6 错误处理策略

```python
def _create_directory_for_path(self, key: str, path: str) -> None:
    """为路径配置创建目录"""
    try:
        from pathlib import Path
        Path(path).mkdir(parents=True, exist_ok=True)
    except (OSError, PermissionError, ValueError) as e:
        # 目录创建失败，记录警告但不中断程序
        print(f"警告: 无法创建目录 {key}: {path}, 错误: {e}")
    except Exception as e:
        # 其他未预期的错误
        print(f"警告: 创建目录时发生未知错误 {key}: {path}, 错误: {e}")
```

### 11.7 测试模式支持

自动目录创建功能在测试模式下同样工作，确保测试环境的路径也能正常创建：

```python
# 测试模式下的自动目录创建
config = get_config_manager(test_mode=True, first_start_time=test_time)
config.set('paths.test_log_dir', '/tmp/test/logs')  # 自动创建测试目录，通过config.paths.test_log_dir访问
```

### 11.8 性能考虑

- **幂等性**：使用`exist_ok=True`确保重复创建不会出错
- **批量创建**：路径配置管理器批量创建所有路径，减少系统调用
- **错误容忍**：创建失败不影响配置设置，只记录警告
- **权限检查**：自动处理权限错误，不中断程序执行

---

**文档版本**: v1.1  
**最后更新**: 2025-06-09  
**更新内容**: 添加自动目录创建功能的详细设计 