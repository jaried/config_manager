# TSB日志路径更新功能说明

## 概述

从版本X.X.X开始，config_manager更新了TSB（TensorBoard）日志路径的生成格式，提供了更规范的目录结构和路径一致性保证。

## 主要更新

### 1. 新的路径格式

**旧格式**：
```
{work_dir}/{yyyy}/{Www}/{mmdd}/{HHMMSS}
```

**新格式**：
```
{work_dir}/tsb_logs/{yyyy}/{ww}/{mmdd}/{HHMMSS}
```

主要变化：
- 增加了`/tsb_logs/`子目录，将TSB日志与其他文件分离
- 周数格式从`W02`改为`02`（两位数字，不带W前缀）
- 使用ISO 8601标准的周数计算

### 2. tensorboard_dir自动等于tsb_logs_dir

`config.paths.tensorboard_dir`现在是一个只读属性，其值始终等于`config.paths.tsb_logs_dir`。这确保了TensorBoard相关的所有路径保持一致。

```python
# 两个路径始终相等
assert config.paths.tensorboard_dir == config.paths.tsb_logs_dir

# 尝试设置tensorboard_dir会抛出异常
try:
    config.paths.tensorboard_dir = "/custom/path"
except AttributeError as e:
    print(f"错误: {e}")  # tensorboard_dir是只读属性
```

### 3. 动态路径生成

`tsb_logs_dir`是动态生成的，基于：
- `work_dir`：工作目录根路径
- `first_start_time`：首次启动时间（如果设置）
- 当前时间（如果没有设置first_start_time）

### 4. 1秒缓存优化

为了提高性能，路径生成结果会缓存1秒。在缓存期内的多次访问会返回相同的路径，避免重复计算。

## 使用示例

### 基本使用

```python
from config_manager import get_config_manager
from datetime import datetime

# 创建配置管理器
config = get_config_manager(
    auto_create=True,
    first_start_time=datetime(2025, 1, 15, 10, 30, 45)
)

# 访问TSB日志路径
tsb_dir = config.paths.tsb_logs_dir
print(f"TSB日志目录: {tsb_dir}")
# 输出: /path/to/work/tsb_logs/2025/03/0115/103045

# TensorBoard目录自动保持一致
tb_dir = config.paths.tensorboard_dir
assert tb_dir == tsb_dir
```

### 在训练脚本中使用

```python
from torch.utils.tensorboard import SummaryWriter

# 使用TSB日志目录创建SummaryWriter
writer = SummaryWriter(log_dir=config.paths.tsb_logs_dir)

# 记录训练指标
for epoch in range(num_epochs):
    # ... 训练代码 ...
    writer.add_scalar('Loss/train', train_loss, epoch)
    writer.add_scalar('Accuracy/train', train_acc, epoch)

writer.close()

# 启动TensorBoard查看日志
# tensorboard --logdir={config.paths.tensorboard_dir}
```

### ISO周数说明

路径中的周数遵循ISO 8601标准：
- 每年的第一个周四所在的周为第1周
- 一年可能有52或53周
- 年末的某些天可能属于下一年的第1周

```python
from datetime import datetime

# 示例日期的ISO周数
examples = [
    (datetime(2025, 1, 1), "2025年第1周"),
    (datetime(2025, 12, 25), "2025年第52周"),
    (datetime(2024, 12, 30), "2025年第1周"),  # 属于下一年
]

for date, desc in examples:
    iso_year, iso_week, _ = date.isocalendar()
    print(f"{date.strftime('%Y-%m-%d')}: {desc} (ISO: {iso_year}年第{iso_week}周)")
```

## 技术细节

### 实现机制

1. **PathsConfigNode**：特殊的配置节点类，支持动态路径生成
2. **DynamicPathProperty**：属性描述符，实现延迟计算和缓存
3. **TensorBoardDirDescriptor**：确保tensorboard_dir始终等于tsb_logs_dir

### 路径生成函数

```python
@staticmethod
def generate_tsb_logs_path(work_dir: str, timestamp: datetime = None) -> str:
    """生成TSB日志路径"""
    if timestamp is None:
        timestamp = datetime.now()
    
    # 使用ISO日历
    iso_year, iso_week, _ = timestamp.isocalendar()
    
    # 构建路径
    return os.path.join(
        work_dir,
        'tsb_logs',
        str(iso_year),
        f"{iso_week:02d}",
        timestamp.strftime('%m%d'),
        timestamp.strftime('%H%M%S')
    )
```

## 迁移指南

如果您的代码依赖旧的路径格式，请注意以下变化：

1. 路径中增加了`/tsb_logs/`子目录
2. 周数格式不再包含`W`前缀
3. `tensorboard_dir`不能再被独立设置

建议的迁移步骤：

```python
# 旧代码
config.paths.tensorboard_dir = custom_path  # 不再支持

# 新代码
# tensorboard_dir会自动等于tsb_logs_dir
# 如需自定义路径，应该通过设置work_dir或first_start_time来影响路径生成
```

## 常见问题

**Q: 为什么tensorboard_dir是只读的？**
A: 为了确保TensorBoard相关的所有路径保持一致，避免配置混乱。

**Q: 如何自定义TSB日志路径？**
A: 通过设置`work_dir`和`first_start_time`来影响路径生成，而不是直接设置路径。

**Q: 缓存会导致路径不更新吗？**
A: 缓存只有1秒，正常使用不会有问题。如果需要立即获取新路径，可以等待1秒后再访问。

**Q: ISO周数与普通周数有什么区别？**
A: ISO周数可能与日历年份不同，特别是在年初和年末。这确保了周数的国际标准一致性。