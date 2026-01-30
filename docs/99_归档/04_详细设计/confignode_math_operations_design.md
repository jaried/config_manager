# ConfigNode数学运算支持概要设计

## 1. 设计概述

### 1.1 设计目标
为ConfigNode类添加数学运算支持，使配置数据能够直接参与数学计算，同时提供自动解包机制简化单值配置的使用。

### 1.2 核心特性
- **数学运算符**：支持加减乘除和比较运算
- **自动解包**：单值ConfigNode自动解包参与运算
- **类型转换**：支持int()、float()转换
- **错误处理**：多值ConfigNode提供清晰错误信息

## 2. 技术架构

### 2.1 运算符支持

#### 2.1.1 数学运算符
```python
__add__    # 加法 +
__sub__    # 减法 -
__mul__    # 乘法 *
__truediv__ # 除法 /
```

#### 2.1.2 比较运算符
```python
__eq__     # 等于 ==
__ne__     # 不等于 !=
__lt__     # 小于 <
__gt__     # 大于 >
```

#### 2.1.3 类型转换
```python
__int__    # int()转换
__float__  # float()转换
```

### 2.2 自动解包机制

#### 2.2.1 单值检测
```python
def _is_single_value(self):
    """检测是否为单值ConfigNode"""
    return (isinstance(self._data, dict) and 
            len(self._data) == 1 and 
            not isinstance(next(iter(self._data.values())), dict))
```

#### 2.2.2 自动解包逻辑
```python
def _auto_unpack(self):
    """自动解包单值ConfigNode"""
    if self._is_single_value():
        return next(iter(self._data.values()))
    return self
```

## 3. 实现方式

### 3.1 数学运算实现
```python
def __add__(self, other):
    """加法运算"""
    if self._is_single_value():
        return self._auto_unpack() + other
    else:
        raise TypeError("不支持多值ConfigNode的数学运算")
```

### 3.2 类型转换实现
```python
def __int__(self):
    """int()转换"""
    if self._is_single_value():
        return int(self._auto_unpack())
    else:
        raise TypeError("不支持多值ConfigNode的类型转换")
```

### 3.3 特殊类型处理
```python
def __getattr__(self, name):
    """特殊处理first_start_time等类型"""
    if name == 'first_start_time':
        # 自动转换为datetime对象
        return self._convert_to_datetime(value)
    return super().__getattr__(name)
```

## 4. 错误处理

### 4.1 多值ConfigNode错误
```python
# 错误示例
config_node = ConfigNode({'a': 1, 'b': 2})
result = config_node + 5  # 抛出TypeError

# 错误信息
TypeError: 不支持多值ConfigNode的数学运算，请使用 config_node.a + 5
```

### 4.2 类型转换错误
```python
# 错误示例
config_node = ConfigNode({'value': 'not_a_number'})
result = int(config_node)  # 抛出ValueError

# 错误信息
ValueError: 无法将 'not_a_number' 转换为整数
```

## 5. 使用示例

### 5.1 基本数学运算
```python
# 单值ConfigNode
config_node = ConfigNode({'value': 10})
result = config_node + 5  # 15
result = config_node * 2  # 20
```

### 5.2 比较运算
```python
config_node = ConfigNode({'threshold': 0.8})
if config_node > 0.5:
    print("超过阈值")
```

### 5.3 类型转换
```python
config_node = ConfigNode({'count': 10.5})
int_value = int(config_node)  # 10
float_value = float(config_node)  # 10.5
```

## 6. 兼容性考虑

### 6.1 向后兼容
- 现有ConfigNode功能完全保持
- 新增功能不影响现有API
- 错误处理提供清晰指导

### 6.2 类型安全
- 运算前进行类型检查
- 提供准确的错误信息
- 支持类型注释自动转换

## 7. 实施状态

### 7.1 完成状态
- ✅ **已完成**：基于commit 2b96b6f
- ✅ **运算符支持**：完整的数学运算符实现
- ✅ **自动解包**：单值ConfigNode自动解包
- ✅ **错误处理**：清晰的错误信息和类型检查

### 7.2 技术实现
- 在ConfigNode类中实现所有数学运算符
- 使用自动解包机制简化单值配置使用
- 提供完整的类型转换和错误处理支持