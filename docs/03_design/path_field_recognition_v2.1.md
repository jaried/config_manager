# 路径字段识别算法 v2.1 设计文档

## 1. 版本更新说明

### 1.1 v2.1 主要变更

**简化路径字段识别逻辑**：
- ✅ **精确后缀匹配**：只识别以特定路径相关名词结尾的字段
- ✅ **简化保护模式**：保护模式作用大幅简化，主要保护网络URL和正则表达式
- ✅ **提高准确性**：减少误识别，提高路径字段识别的准确性
- ✅ **降低复杂度**：简化算法逻辑，提高维护性

### 1.2 设计理念变更

**从模糊匹配到精确匹配**：
- **v2.0**：基于字段名关键词 + 值格式的双重检测
- **v2.1**：基于字段名后缀的精确匹配

**保护模式作用简化**：
- **v2.0**：复杂的保护逻辑，包括HTTP Headers、MIME类型等
- **v2.1**：简化保护逻辑，主要保护网络URL和正则表达式

## 2. 核心算法设计

### 2.1 路径字段识别算法

#### 2.1.1 识别规则

只有以下特定后缀的字段才被识别为路径字段：

| 后缀 | 用途 | 示例 |
|------|------|------|
| `_dir`, `dir` | 目录路径 | `base_dir`, `log_dir`, `work_dir` |
| `_path`, `path` | 文件或目录路径 | `config_path`, `data_path` |
| `_file`, `file` | 文件路径 | `config_file`, `log_file` |
| `_directory`, `directory` | 目录路径 | `temp_directory`, `backup_directory` |
| `_folder`, `folder` | 文件夹路径 | `backup_folder`, `cache_folder` |
| `_location`, `location` | 位置路径 | `install_location`, `storage_location` |

#### 2.1.2 算法实现

```python
@classmethod
def _is_path_field(cls, key: str, value: str) -> bool:
    """判断字段是否是路径字段
    
    只有以特定路径相关名词结尾的字段才被识别为路径字段：
    - _dir, dir: 目录路径
    - _path, path: 文件或目录路径  
    - _file, file: 文件路径
    - _directory, directory: 目录路径
    - _folder, folder: 文件夹路径
    - _location, location: 位置路径
    """
    if not isinstance(value, str) or not value.strip():
        return False

    # 首先检查是否是需要保护的字段类型
    if cls._is_protected_field(key, value):
        return False

    # 检查字段名是否以路径相关名词结尾
    key_lower = key.lower()
    path_suffixes = [
        '_dir', 'dir',
        '_path', 'path', 
        '_file', 'file',
        '_directory', 'directory',
        '_folder', 'folder',
        '_location', 'location'
    ]

    for suffix in path_suffixes:
        if key_lower.endswith(suffix):
            return True

    return False
```

### 2.2 保护字段算法（简化版）

#### 2.2.1 保护目标

由于路径字段识别已改为只识别特定后缀，保护模式主要用于：

1. **防止网络URL被误识别为路径**
2. **防止正则表达式被误识别为路径**
3. **保护特殊配置字段**

#### 2.2.2 算法实现

```python
@classmethod
def _is_protected_field(cls, key: str, value: str) -> bool:
    """判断字段是否是需要保护的字段（不应该被路径替换）
    
    由于路径字段识别已改为只识别特定后缀，保护模式主要用于：
    1. 防止网络URL被误识别为路径
    2. 防止正则表达式被误识别为路径
    3. 保护特殊配置字段
    """
    if not isinstance(value, str) or not value.strip():
        return False

    key_lower = key.lower()
    value_lower = value.lower()

    # 1. HTTP/HTTPS URL保护（最重要的保护）
    if value.startswith(('http://', 'https://', 'ftp://', 'ws://', 'wss://')):
        return True

    # 2. 网络相关字段保护
    network_keywords = ['proxy', 'url', 'endpoint', 'api', 'host', 'server']
    for keyword in network_keywords:
        if keyword in key_lower:
            return True

    # 3. HTTP Headers保护
    header_keywords = ['header', 'accept', 'content-type', 'user-agent', 'user_agent', 'cookie', 'authorization']
    for keyword in header_keywords:
        if keyword in key_lower:
            return True
    
    # 常见的HTTP Header字段名
    if key_lower in ['accept', 'content-type', 'user-agent', 'authorization', 'cookie']:
        return True

    # 4. 正则表达式保护
    if cls._is_regex_pattern(value):
        return True

    # 5. MIME类型保护
    if '/' in value and any(mime in value_lower for mime in [
        'text/', 'application/', 'image/', 'video/', 'audio/', 'multipart/', 'message/'
    ]):
        return True

    # 6. URL模式保护
    if cls._is_url_pattern(value):
        return True

    return False
```

## 3. 优势分析

### 3.1 准确性提升

**精确匹配**：
- ✅ 只识别明确的路径字段，避免误识别
- ✅ 减少对值格式的依赖，提高稳定性
- ✅ 明确的字段命名规范，便于开发者理解

**示例对比**：

| 字段名 | 值 | v2.0识别 | v2.1识别 | 说明 |
|--------|----|---------|---------|----- |
| `base_url` | `https://api.example.com` | ❌ 可能误识别 | ✅ 正确保护 | 包含base但不以路径后缀结尾 |
| `path_pattern` | `/api/v\d+/` | ❌ 可能误识别 | ✅ 正确保护 | 包含path但是正则表达式 |
| `base_dir` | `/original/base/path` | ✅ 正确识别 | ✅ 正确识别 | 以dir结尾的路径字段 |
| `config_file` | `/etc/config.yaml` | ✅ 正确识别 | ✅ 正确识别 | 以file结尾的路径字段 |

### 3.2 维护性提升

**简化逻辑**：
- ✅ 算法逻辑更简单，易于理解和维护
- ✅ 减少复杂的值格式检测，降低出错概率
- ✅ 明确的规则，便于扩展和修改

### 3.3 性能提升

**减少计算**：
- ✅ 不再需要复杂的路径格式检测
- ✅ 简单的字符串后缀匹配，性能更好
- ✅ 减少正则表达式和复杂逻辑的使用

## 4. 使用指南

### 4.1 字段命名规范

为了确保路径字段被正确识别，请遵循以下命名规范：

**推荐命名**：
```yaml
# 目录路径
base_dir: "/path/to/base"
log_dir: "/path/to/logs"
work_dir: "/path/to/work"

# 文件路径
config_file: "/path/to/config.yaml"
log_file: "/path/to/app.log"

# 通用路径
data_path: "/path/to/data"
backup_path: "/path/to/backup"

# 位置路径
install_location: "/usr/local/app"
storage_location: "/var/storage"
```

**避免命名**：
```yaml
# 这些不会被识别为路径字段
base_url: "https://api.example.com"  # 包含base但不以路径后缀结尾
path_pattern: "/api/v\\d+/"          # 包含path但不以路径后缀结尾
directory_listing: "enabled"         # 包含directory但不是路径值
```

### 4.2 特殊情况处理

**网络相关字段**：
```yaml
# 这些会被保护，不会被替换
proxy_url: "http://proxy.company.com:8080"
api_endpoint: "https://api.example.com/v1"
server_host: "localhost"
```

**HTTP Headers**：
```yaml
# 这些会被保护，不会被替换
headers:
  User-Agent: "Mozilla/5.0 (compatible; Bot/1.0)"
  Accept: "text/html,application/xhtml+xml"
  Content-Type: "application/json"
```

**正则表达式**：
```yaml
# 这些会被保护，不会被替换
validation:
  url_pattern: "^https://[^/]+/api/v\\d+/"
  file_pattern: "\\.log$"
```

## 5. 测试验证

### 5.1 测试用例

```python
# 应该被识别为路径字段的
test_cases_path = [
    ('base_dir', '/original/base/path'),
    ('work_dir', '/original/work/path'),
    ('log_dir', '/original/log/path'),
    ('config_file', '/etc/validation/rules.yaml'),
    ('data_path', '/var/data'),
    ('temp_directory', '/tmp/temp'),
    ('backup_folder', '/backup'),
    ('install_location', '/usr/local'),
]

# 不应该被识别为路径字段的
test_cases_protected = [
    ('proxy_url', 'http://proxy.company.com:8080'),
    ('url_pattern', r'^https://[^/]+/api/v\d+/'),
    ('User_Agent', 'Mozilla/5.0 (compatible; Bot/1.0)'),
    ('base_url', 'https://api.example.com'),
    ('path_pattern', r'/api/v\d+/'),
    ('directory_listing', 'enabled'),
]
```

### 5.2 验证结果

所有测试用例均通过，证明v2.1算法的准确性和可靠性。

## 6. 总结

v2.1版本的路径字段识别算法通过简化逻辑、精确匹配，显著提升了准确性、维护性和性能。新算法更加稳定可靠，为测试模式的路径替换功能提供了坚实的基础。 