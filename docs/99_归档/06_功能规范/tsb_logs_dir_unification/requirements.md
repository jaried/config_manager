# TensorBoard目录统一需求规范

## 1. 需求概述

### 1.1 背景
当前系统中存在两个TensorBoard相关的目录配置：
- `config.paths.tsb_logs_dir`: TensorBoard日志目录
- `config.paths.tensorboard_dir`: TensorBoard目录

这两个目录的功能相似但路径格式不同，容易造成混淆和维护困难。

### 1.2 目标
1. 将`config.paths.tsb_logs_dir`的路径格式改为: `{work_dir}/{yyyy}/{第几周}/{mmdd}/{HHMMSS}`
2. 确保`config.paths.tensorboard_dir`与`config.paths.tsb_logs_dir`完全一致
3. 保持向后兼容性，确保现有功能不受影响

## 2. 功能需求

### 2.1 路径格式规范
- **路径模板**: `{work_dir}/{yyyy}/{第几周}/{mmdd}/{HHMMSS}`
- **路径组件说明**:
  - `{work_dir}`: 工作目录根路径
  - `{yyyy}`: 4位年份（如：2025）
  - `{第几周}`: 一年中的第几周，使用ISO周数，格式为`W{周数}`（如：W01, W52）
  - `{mmdd}`: 月份和日期的4位数字（如：0108）
  - `{HHMMSS}`: 时分秒的6位数字（如：143025）

### 2.2 路径生成要求
1. 两个配置项必须指向同一个物理路径
2. 路径生成时使用相同的时间戳和计算逻辑
3. 周数计算采用ISO 8601标准（周一为一周的第一天）

### 2.3 兼容性要求
1. 保留原有的API接口，不改变外部调用方式
2. 确保测试模式下的路径生成逻辑一致
3. 支持跨平台路径处理（Windows/Linux/macOS）

## 3. 约束条件

### 3.1 技术约束
- 必须使用Python标准库的datetime模块进行时间处理
- 路径生成必须使用pathlib或os.path确保跨平台兼容
- 不得引入新的第三方依赖

### 3.2 性能约束
- 路径生成操作的时间复杂度应为O(1)
- 不得因路径统一而增加额外的文件I/O操作

### 3.3 安全约束
- 生成的路径必须在work_dir范围内，防止路径遍历攻击
- 确保路径中不包含特殊字符或非法字符

## 4. 预期行为

### 4.1 正常场景
1. 系统启动时，两个配置项生成相同的路径
2. 配置更新时，两个配置项同步更新
3. 获取任一配置项时，返回相同的路径值

### 4.2 异常场景
1. 如果时间解析失败，应抛出明确的异常信息
2. 如果work_dir不存在或无权限，应在首次使用时报错
3. 如果路径创建失败，应保留原有行为（由调用方处理）

## 5. 验收标准

### 5.1 功能验收
1. `config.paths.tsb_logs_dir`生成的路径符合新格式
2. `config.paths.tensorboard_dir === config.paths.tsb_logs_dir`始终为真
3. 所有现有测试用例通过

### 5.2 质量验收
1. 代码覆盖率不低于现有水平
2. 无新增的代码质量问题（ruff检查通过）
3. 文档更新完整，包括API文档和使用示例

## 6. 示例

### 6.1 路径示例
假设：
- work_dir = `/home/user/project`
- 时间 = 2025年1月8日 14时30分25秒（周三，第2周）

生成路径：
```
/home/user/project/2025/W02/0108/143025
```

### 6.2 配置示例
```yaml
paths:
  work_dir: /home/user/project
  tsb_logs_dir: /home/user/project/2025/W02/0108/143025
  tensorboard_dir: /home/user/project/2025/W02/0108/143025
```

## 7. 依赖关系
- 依赖于PathConfiguration类的路径生成逻辑
- 依赖于TimeProcessor类的时间解析功能
- 影响所有使用这两个配置项的下游模块