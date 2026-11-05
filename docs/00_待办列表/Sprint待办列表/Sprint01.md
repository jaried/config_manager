# Sprint01 待办列表

## Sprint信息

- **Sprint周期**：Sprint01
- **创建时间**：2026-01-09
- **Sprint目标**：增强ConfigNode的dict兼容性

## Sprint 状态：进行中

## Sprint 跟踪

| ID | 内容 | 状态 | 优先级 | 估算 | 依赖 | Phase | 关键路径点数 | 登记日期 | 实施完成日期 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| S1-01 | [US] 为ConfigNode添加dict标准方法 | 待验收 | P1 | 2 |  |  | - | - | - |
| S1-02 | [US] 支持 `test_mode` 自动切换测试数据库并更新 `py-config-logger` | 待验收 | P2 | 5 |  |  | - | - | - |
| S1-03 | [BUG] `ConfigManager.set()+save()` 将 YAML sequence 序列化为非法单横杠 | 待验收 | P1 | 3 |  |  | - | - | - |
| S1-04 | [BUG] config.progress 变化触发配置自动备份 | 待验收 | P2 | 2 |  |  | - | - | - |
| S1-05 | [BUG] config.progress 变化时 config.yaml 正常保存且不触发备份 | 待验收 | P2 | 2 |  |  | - | - | - |
| S1-06 | [US] `get_config_manager` 支持只读通用层与可写专用层 | 方案设计中 | P1 | 5 | - | - | 5 | 2026-11-04 | - |

**Sprint 总点数**：19

**Issue 统计**：共 6 个 | 待办 0 | 方案已决策 0 | 方案未设计 0 | 方案设计中 1 | 方案已设计 0 | 实施中 0 | 待验收 5 | 已完成 0 | 已取消 0
设计完成 0 | 待验收 5 | 已完成 0 | 已取消 0 | 推迟 0 | 已关闭 0
