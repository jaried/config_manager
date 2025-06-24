# Config Manager 最简 Logger 详细设计

## 1. 概述

本文档详细描述了config_manager最简logger的实现细节，包括类设计、方法实现、集成方案和替换策略。

## 2. 类设计详细说明

### 2.1 MinimalLogger类

#### 2.1.1 类定义
```python
class MinimalLogger:
    """最简日志记录器，与custom_logger格式兼容"""
    
    def __init__(self, name: str) -> None:
        """
        初始化日志记录器
        
        Args:
            name: 日志记录器名称，用于标识日志来源
        """
```

#### 2.1.2 属性设计
```python
class MinimalLogger:
    def __init__(self, name: str) -> None:
        self.name = name[:8] if len(name) > 8 else name  # 名称限制8位
        self._config_cache = None  # 配置缓存
        self._config_cache_time = 0  # 配置缓存时间
        self._log_file_handle = None  # 日志文件句柄
        self._log_file_path = None  # 日志文件路径
        self._start_time = datetime.now()  # 启动时间
```

#### 2.1.3 日志级别方法
```python
def debug(self, message: str, *args, **kwargs) -> None:
    """记录DEBUG级别日志"""
    if self._should_log('DEBUG'):
        formatted_message = self._format_message('DEBUG', message, *args, **kwargs)
        self._write_log(formatted_message)

def info(self, message: str, *args, **kwargs) -> None:
    """记录INFO级别日志"""
    if self._should_log('INFO'):
        formatted_message = self._format_message('INFO', message, *args, **kwargs)
        self._write_log(formatted_message)

def warning(self, message: str, *args, **kwargs) -> None:
    """记录WARNING级别日志"""
    if self._should_log('WARNING'):
        formatted_message = self._format_message('WARNING', message, *args, **kwargs)
        self._write_log(formatted_message)

def error(self, message: str, *args, **kwargs) -> None:
    """记录ERROR级别日志"""
    if self._should_log('ERROR'):
        formatted_message = self._format_message('ERROR', message, *args, **kwargs)
        self._write_log(formatted_message)

def critical(self, message: str, *args, **kwargs) -> None:
    """记录CRITICAL级别日志"""
    if self._should_log('CRITICAL'):
        formatted_message = self._format_message('CRITICAL', message, *args, **kwargs)
        self._write_log(formatted_message)
```

### 2.2 核心方法详细设计

#### 2.2.1 级别判断方法
```python
def _should_log(self, level: str) -> bool:
    """
    判断是否应该记录指定级别的日志
    
    Args:
        level: 日志级别
        
    Returns:
        bool: 是否应该记录
    """
    try:
        config = self._get_config()
        console_level = config.get('console_level', 'INFO')
        file_level = config.get('file_level', 'DEBUG')
        
        # 级别映射
        level_map = {
            'DEBUG': 10,
            'INFO': 20,
            'WARNING': 30,
            'ERROR': 40,
            'CRITICAL': 50
        }
        
        current_level = level_map.get(level.upper(), 0)
        console_threshold = level_map.get(console_level.upper(), 20)
        file_threshold = level_map.get(file_level.upper(), 10)
        
        # 如果控制台或文件任一满足条件，就记录
        return current_level >= console_threshold or current_level >= file_threshold
        
    except Exception:
        # 异常时默认记录INFO及以上级别
        return level.upper() in ['INFO', 'WARNING', 'ERROR', 'CRITICAL']
```

#### 2.2.2 消息格式化方法
```python
def _format_message(self, level: str, message: str, *args, **kwargs) -> str:
    """
    格式化日志消息
    
    Args:
        level: 日志级别
        message: 消息内容
        *args: 位置参数
        **kwargs: 关键字参数
        
    Returns:
        str: 格式化后的消息
    """
    try:
        # 格式化消息内容
        if args or kwargs:
            formatted_message = message.format(*args, **kwargs)
        else:
            formatted_message = message
            
        # 获取调用者信息
        caller_module, line_number = self._get_caller_info()
        
        # 获取当前时间
        current_time = datetime.now()
        timestamp = current_time.strftime('%Y-%m-%d %H:%M:%S')
        
        # 计算运行时长
        elapsed_str = self._format_elapsed_time(current_time)
        
        # 获取进程ID
        pid_str = f"{os.getpid():>6}"
        
        # 组装日志行：格式与custom_logger完全一致
        log_line = f"[{pid_str} | {caller_module:<8} : {line_number:>4}] {timestamp} - {elapsed_str} - {level:^10} - {formatted_message}"
        
        return log_line
        
    except Exception as e:
        # 格式化失败时返回简单消息
        return f"[ERROR] 日志格式化失败: {message} (错误: {e})"
```

#### 2.2.3 调用者信息获取方法
```python
def _get_caller_info(self) -> Tuple[str, int]:
    """
    获取调用者信息（文件名和行号）
    
    Returns:
        Tuple[str, int]: (模块名, 行号)
    """
    try:
        import inspect
        stack = inspect.stack()
        
        # 查找第一个非config_manager的调用者
        for frame_info in stack[2:]:  # 跳过当前方法和调用方法
            if frame_info is None:
                continue
                
            filename = frame_info.filename
            basename = os.path.basename(filename)
            line_number = frame_info.lineno
            
            # 验证行号合理性
            if line_number <= 0 or line_number > 10_000:
                continue
                
            # 获取模块名
            name_without_ext = os.path.splitext(basename)[0]
            
            # 跳过config_manager内部文件
            if 'config_manager' in filename and basename in [
                'minimal_logger.py', 'config_manager.py', 'manager.py'
            ]:
                continue
                
            # 跳过系统文件
            if basename in ['<string>', 'python']:
                continue
                
            # 返回找到的调用者
            module_name = name_without_ext[:8] if len(name_without_ext) > 8 else name_without_ext
            return module_name, line_number
            
        # 如果没找到合适的调用者，返回默认值
        return "unknown", 0
        
    except Exception:
        return "error", 0
```

#### 2.2.4 运行时长格式化方法
```python
def _format_elapsed_time(self, current_time: datetime) -> str:
    """
    格式化运行时长
    
    Args:
        current_time: 当前时间
        
    Returns:
        str: 格式化的运行时长
    """
    try:
        elapsed = current_time - self._start_time
        total_seconds = elapsed.total_seconds()
        
        hours, remainder = divmod(int(total_seconds), 3600)
        minutes, seconds_int = divmod(remainder, 60)
        
        # 计算带小数的秒数
        fractional_seconds = total_seconds - (hours * 3600 + minutes * 60)
        
        elapsed_str = f"{hours}:{minutes:02d}:{fractional_seconds:05.2f}"
        return elapsed_str
        
    except Exception:
        return "0:00:00.00"
```

#### 2.2.5 配置获取方法
```python
def _get_config(self) -> dict:
    """
    获取日志配置
    
    Returns:
        dict: 日志配置字典
    """
    try:
        # 检查配置缓存是否有效（5秒缓存）
        current_time = time.time()
        if (self._config_cache is not None and 
            current_time - self._config_cache_time < 5):
            return self._config_cache
            
        # 尝试从config_manager获取配置
        config = self._load_config_from_manager()
        if config:
            self._config_cache = config
            self._config_cache_time = current_time
            return config
            
        # 使用默认配置
        default_config = {
            'console_level': 'INFO',
            'file_level': 'DEBUG',
            'log_dir': 'logs'
        }
        
        self._config_cache = default_config
        self._config_cache_time = current_time
        return default_config
        
    except Exception:
        # 异常时返回默认配置
        return {
            'console_level': 'INFO',
            'file_level': 'DEBUG',
            'log_dir': 'logs'
        }
```

#### 2.2.6 配置加载方法
```python
def _load_config_from_manager(self) -> Optional[dict]:
    """
    从config_manager加载配置
    
    Returns:
        Optional[dict]: 配置字典，失败时返回None
    """
    try:
        # 尝试获取全局config对象
        import sys
        for module_name in sys.modules:
            if 'config_manager' in module_name:
                module = sys.modules[module_name]
                if hasattr(module, 'get_config_manager'):
                    config_manager = module.get_config_manager()
                    if config_manager and hasattr(config_manager, '_data'):
                        logger_config = config_manager._data.get('logger', {})
                        if logger_config:
                            return {
                                'console_level': logger_config.get('console_level', 'INFO'),
                                'file_level': logger_config.get('file_level', 'DEBUG'),
                                'log_dir': logger_config.get('log_dir', 'logs')
                            }
        return None
        
    except Exception:
        return None
```

#### 2.2.7 日志写入方法
```python
def _write_log(self, formatted_message: str) -> None:
    """
    写入日志到控制台和文件
    
    Args:
        formatted_message: 格式化后的日志消息
    """
    try:
        # 写入控制台
        self._write_console(formatted_message)
        
        # 写入文件
        self._write_file(formatted_message)
        
    except Exception:
        # 写入失败时使用print作为降级方案
        print(formatted_message)

def _write_console(self, formatted_message: str) -> None:
    """写入控制台"""
    try:
        config = self._get_config()
        console_level = config.get('console_level', 'INFO')
        
        # 检查控制台级别
        level_map = {'DEBUG': 10, 'INFO': 20, 'WARNING': 30, 'ERROR': 40, 'CRITICAL': 50}
        message_level = self._extract_level_from_message(formatted_message)
        if level_map.get(message_level, 0) >= level_map.get(console_level, 20):
            print(formatted_message)
            
    except Exception:
        # 异常时直接打印
        print(formatted_message)

def _write_file(self, formatted_message: str) -> None:
    """写入文件"""
    try:
        config = self._get_config()
        file_level = config.get('file_level', 'DEBUG')
        log_dir = config.get('log_dir', 'logs')
        
        # 检查文件级别
        level_map = {'DEBUG': 10, 'INFO': 20, 'WARNING': 30, 'ERROR': 40, 'CRITICAL': 50}
        message_level = self._extract_level_from_message(formatted_message)
        if level_map.get(message_level, 0) >= level_map.get(file_level, 10):
            # 确保日志目录存在
            if not os.path.exists(log_dir):
                os.makedirs(log_dir, exist_ok=True)
                
            # 生成日志文件路径
            current_date = datetime.now().strftime('%Y-%m-%d')
            log_file_path = os.path.join(log_dir, f'config_manager_{current_date}.log')
            
            # 写入文件
            with open(log_file_path, 'a', encoding='utf-8') as f:
                f.write(formatted_message + '\n')
                
    except Exception:
        # 文件写入失败时忽略，不影响控制台输出
        pass

def _extract_level_from_message(self, formatted_message: str) -> str:
    """从格式化消息中提取日志级别"""
    try:
        # 消息格式：[PID | 模块名 : 行号] 时间戳 - 运行时长 - 级别 - 消息
        parts = formatted_message.split(' - ')
        if len(parts) >= 3:
            level_part = parts[2].strip()
            return level_part
        return 'INFO'
    except Exception:
        return 'INFO'
```

## 3. 全局配置管理

### 3.1 全局logger实例管理
```python
# 全局logger实例缓存
_logger_instances = {}
_logger_lock = threading.Lock()

def get_minimal_logger(name: str) -> MinimalLogger:
    """
    获取最简logger实例
    
    Args:
        name: logger名称
        
    Returns:
        MinimalLogger: logger实例
    """
    # 名称长度限制
    if len(name) > 8:
        name = name[:8]
        
    with _logger_lock:
        if name not in _logger_instances:
            _logger_instances[name] = MinimalLogger(name)
        return _logger_instances[name]
```

## 4. 集成到ConfigManagerCore

### 4.1 在ConfigManagerCore中添加logger支持
```python
class ConfigManagerCore:
    def __init__(self):
        # 现有初始化代码...
        self._logger = get_minimal_logger("config_mgr")
        
    def _log_debug(self, message: str, *args, **kwargs) -> None:
        """记录DEBUG日志"""
        self._logger.debug(message, *args, **kwargs)
        
    def _log_info(self, message: str, *args, **kwargs) -> None:
        """记录INFO日志"""
        self._logger.info(message, *args, **kwargs)
        
    def _log_warning(self, message: str, *args, **kwargs) -> None:
        """记录WARNING日志"""
        self._logger.warning(message, *args, **kwargs)
        
    def _log_error(self, message: str, *args, **kwargs) -> None:
        """记录ERROR日志"""
        self._logger.error(message, *args, **kwargs)
```

### 4.2 替换print语句的策略

#### 4.2.1 替换原则
- 所有内部操作使用DEBUG级别
- 重要操作使用INFO级别
- 警告信息使用WARNING级别
- 错误信息使用ERROR级别
- 严重错误使用CRITICAL级别

#### 4.2.2 替换位置
1. **ConfigManagerCore**：配置加载、保存、重载等操作
2. **PathResolver**：路径解析相关操作
3. **FileOperations**：文件读写操作
4. **AutosaveManager**：自动保存操作
5. **FileWatcher**：文件监视操作
6. **TestEnvironment**：测试环境操作

#### 4.2.3 替换示例
```python
# 替换前
print(f"配置文件加载成功: {config_path}")

# 替换后
self._log_debug("配置文件加载成功: {}", config_path)

# 替换前
print(f"⚠️  配置保存失败: {e}")

# 替换后
self._log_error("配置保存失败: {}", e)
```

## 5. 文件组织

### 5.1 目录结构
```
src/config_manager/
├── logger/
│   ├── __init__.py          # 导出get_minimal_logger函数
│   └── minimal_logger.py    # MinimalLogger类实现
├── config_manager.py        # 主配置管理器
├── core/
│   ├── manager.py           # ConfigManagerCore
│   ├── path_resolver.py     # 路径解析器
│   ├── file_operations.py   # 文件操作
│   ├── autosave_manager.py  # 自动保存管理器
│   ├── file_watcher.py      # 文件监视器
│   └── test_environment.py  # 测试环境管理器
```

### 5.2 模块依赖关系
```
config_manager.py
    ↓
core/manager.py (ConfigManagerCore)
    ↓
logger/minimal_logger.py
    ↓
Python标准库 (os, datetime, inspect, threading, time)
```

## 6. 异常处理策略

### 6.1 配置读取异常
- 使用默认配置
- 记录警告信息
- 不影响主功能

### 6.2 文件写入异常
- 忽略文件写入错误
- 保持控制台输出
- 不影响主功能

### 6.3 格式化异常
- 使用简单消息格式
- 记录错误信息
- 保证基本功能

## 7. 性能优化

### 7.1 配置缓存
- 5秒配置缓存
- 避免重复读取
- 减少配置访问开销

### 7.2 级别检查优化
- 在格式化前检查级别
- 避免不必要的计算
- 减少字符串操作

### 7.3 文件句柄管理
- 按需打开文件
- 及时关闭文件
- 避免文件句柄泄漏

## 8. 测试策略

### 8.1 单元测试
- MinimalLogger类测试
- 配置读取测试
- 格式兼容性测试
- 异常处理测试

### 8.2 集成测试
- 与ConfigManagerCore集成测试
- 配置管理器功能测试
- 性能影响测试

### 8.3 兼容性测试
- 与custom_logger格式对比测试
- 跨平台兼容性测试
- 多线程安全性测试

## 9. 部署和配置

### 9.1 配置文件要求
```yaml
logger:
  console_level: INFO      # 控制台日志级别
  file_level: DEBUG        # 文件日志级别
  log_dir: logs           # 日志文件目录
```

### 9.2 默认配置
- console_level: INFO
- file_level: DEBUG
- log_dir: logs

### 9.3 环境变量支持
- 支持通过环境变量覆盖配置
- 优先级：环境变量 > 配置文件 > 默认值

## 10. 维护和扩展

### 10.1 版本兼容性
- 保持API向后兼容
- 支持配置格式升级
- 与custom_logger格式同步

### 10.2 扩展性设计
- 支持新的日志级别
- 支持新的输出方式
- 支持自定义格式

### 10.3 监控和维护
- 日志文件大小监控
- 性能指标监控
- 错误率监控 