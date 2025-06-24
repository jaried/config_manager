# Config Manager 最简 Logger 概要设计

## 1. 概述

### 1.1 设计目标
为config_manager提供独立的最简logger模块，避免与custom_logger的循环依赖，同时保持日志格式的完全兼容。

### 1.2 设计原则
- **最小化依赖**：只使用Python标准库
- **格式兼容**：与custom_logger格式完全一致
- **性能优先**：轻量级实现，不影响主功能
- **异常安全**：logger异常不影响config_manager功能

## 2. 系统架构

### 2.1 整体架构
```
┌─────────────────────────────────────────────────────────────┐
│                    Config Manager                           │
├─────────────────────────────────────────────────────────────┤
│  核心模块层 (Core Modules)                                   │
│  ┌─────────────────┐  ┌─────────────────┐                   │
│  │ ConfigManagerCore│  │ ConfigNode      │                   │
│  │ + MinimalLogger │  │                 │                   │
│  └─────────────────┘  └─────────────────┘                   │
├─────────────────────────────────────────────────────────────┤
│  功能组件层 (Components)                                     │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐        │
│  │ PathResolver │ │FileOperations│ │AutosaveManager│        │
│  │ + Logger     │ │ + Logger     │ │ + Logger     │        │
│  └──────────────┘ └──────────────┘ └──────────────┘        │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐        │
│  │ FileWatcher  │ │CallChainTracker│ │TestEnvironment│        │
│  │ + Logger     │ │ + Logger     │ │ + Logger     │        │
│  └──────────────┘ └──────────────┘ └──────────────┘        │
├─────────────────────────────────────────────────────────────┤
│  最简Logger层 (Minimal Logger)                              │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │              MinimalLogger                              │ │
│  │  + 配置读取    + 格式处理    + 输出管理                  │ │
│  └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 模块职责

#### 2.2.1 MinimalLogger
- **职责**：提供统一的日志记录接口
- **功能**：
  - 日志级别判断和过滤
  - 消息格式化和组装
  - 控制台和文件输出管理
  - 配置读取和缓存

#### 2.2.2 集成模块
- **ConfigManagerCore**：集成logger，替换print语句
- **PathResolver**：路径解析相关日志
- **FileOperations**：文件操作相关日志
- **AutosaveManager**：自动保存相关日志
- **FileWatcher**：文件监视相关日志
- **TestEnvironment**：测试环境相关日志

## 3. 模块设计

### 3.1 MinimalLogger类设计

```python
class MinimalLogger:
    def __init__(self, name: str)
    def debug(self, message: str, *args, **kwargs) -> None
    def info(self, message: str, *args, **kwargs) -> None
    def warning(self, message: str, *args, **kwargs) -> None
    def error(self, message: str, *args, **kwargs) -> None
    def critical(self, message: str, *args, **kwargs) -> None
    
    def _should_log(self, level: str) -> bool
    def _format_message(self, level: str, message: str, *args, **kwargs) -> str
    def _write_console(self, formatted_message: str) -> None
    def _write_file(self, formatted_message: str) -> None
    def _get_caller_info(self) -> Tuple[str, int]
    def _get_config(self) -> Any
```

### 3.2 配置管理设计

```python
class LoggerConfig:
    def __init__(self)
    def get_console_level(self) -> str
    def get_file_level(self) -> str
    def get_log_dir(self) -> str
    def _load_config(self) -> None
    def _get_default_config(self) -> dict
```

## 4. 数据流设计

### 4.1 日志记录流程
```
用户调用logger方法
    ↓
检查日志级别是否满足输出条件
    ↓
获取调用者信息（文件名、行号）
    ↓
格式化日志消息
    ↓
输出到控制台（如果级别满足）
    ↓
输出到文件（如果级别满足且配置了文件输出）
```

### 4.2 配置读取流程
```
Logger初始化
    ↓
尝试读取config.logger配置
    ↓
如果读取失败，使用默认配置
    ↓
缓存配置信息
    ↓
创建日志目录（如果需要文件输出）
```

## 5. 接口设计

### 5.1 公共接口
```python
def get_minimal_logger(name: str) -> MinimalLogger
```

### 5.2 日志级别
- DEBUG：调试信息，所有内部操作
- INFO：一般信息，重要操作
- WARNING：警告信息，潜在问题
- ERROR：错误信息，操作失败
- CRITICAL：严重错误，系统问题

## 6. 配置设计

### 6.1 配置结构
```yaml
logger:
  console_level: INFO      # 控制台日志级别
  file_level: DEBUG        # 文件日志级别
  log_dir: logs           # 日志文件目录
```

### 6.2 默认配置
```python
DEFAULT_CONFIG = {
    'console_level': 'INFO',
    'file_level': 'DEBUG',
    'log_dir': 'logs'
}
```

## 7. 日志格式设计

### 7.1 格式规范
```
[PID | 模块名 : 行号] 时间戳 - 运行时长 - 级别 - 消息
```

### 7.2 格式示例
```
[ 1234 | config_m :  156] 2025-01-07 10:30:45 - 0:05:23.45 -   DEBUG   - 配置文件加载成功
[ 1234 | path_res :   89] 2025-01-07 10:30:45 - 0:05:23.46 -    INFO    - 路径解析完成
```

## 8. 性能设计

### 8.1 优化策略
- **配置缓存**：避免重复读取配置
- **级别检查**：在格式化前检查级别，避免不必要的计算
- **同步写入**：使用同步文件写入，避免异步复杂性
- **最小化计算**：减少字符串操作和格式化计算

### 8.2 性能指标
- 日志记录延迟 < 1ms
- 内存占用增加 < 100KB
- 初始化时间 < 5ms

## 9. 异常处理设计

### 9.1 异常策略
- **降级机制**：配置读取失败时使用默认配置
- **容错处理**：文件写入失败不影响控制台输出
- **静默处理**：logger异常不影响主功能

### 9.2 异常类型
- ConfigReadError：配置读取失败
- FileWriteError：文件写入失败
- FormatError：消息格式化失败

## 10. 线程安全设计

### 10.1 线程安全策略
- **无状态设计**：logger实例无共享状态
- **文件锁**：文件写入使用文件锁保护
- **配置只读**：配置信息只读，无需锁保护

### 10.2 并发考虑
- 支持多线程环境
- 支持多进程环境（每个进程独立logger）
- 避免全局状态

## 11. 测试设计

### 11.1 测试策略
- **单元测试**：测试logger核心功能
- **集成测试**：测试与config_manager的集成
- **性能测试**：测试性能影响
- **兼容性测试**：测试格式兼容性

### 11.2 测试用例
- 日志级别过滤测试
- 格式兼容性测试
- 配置读取测试
- 异常处理测试
- 性能影响测试

## 12. 部署设计

### 12.1 集成方式
- 作为config_manager的内部模块
- 不对外暴露公共接口
- 通过get_minimal_logger函数获取实例

### 12.2 配置管理
- 从config.logger读取配置
- 支持运行时配置更新
- 提供默认配置兜底

## 13. 维护设计

### 13.1 维护策略
- **格式同步**：与custom_logger格式保持同步
- **配置兼容**：保持配置结构兼容
- **向后兼容**：保持API向后兼容

### 13.2 扩展性
- 支持新的日志级别
- 支持新的输出方式
- 支持新的格式选项

## 14. 风险评估

### 14.1 技术风险
- **格式不一致**：与custom_logger格式可能不一致
- **性能影响**：可能影响config_manager性能
- **配置冲突**：可能与custom_logger配置冲突

### 14.2 缓解措施
- 严格遵循custom_logger格式规范
- 性能测试和优化
- 配置隔离和默认值处理 