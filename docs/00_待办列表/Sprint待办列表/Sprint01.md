# Sprint01 待办列表

## Sprint信息

- **Sprint周期**：Sprint01
- **创建时间**：2026-01-09
- **Sprint目标**：增强ConfigNode的dict兼容性

## Sprint 状态：进行中

## Sprint 跟踪

| ID | 内容 | 状态 | 优先级 | 估算 | 依赖 | Phase |
|:---|:-----|:-----|:-------|:-----|:-----|:------|
| US-001 | [US] 为ConfigNode添加dict标准方法 | 进行中 | P1 | 2 |  |  |
| S1-02 | [US] 支持 `test_mode` 自动切换测试数据库并更新 `py-config-logger` | 设计完成 | P2 | 5 |  |  |
| S1-03 | [BUG] `ConfigManager.set()+save()` 将 YAML sequence 序列化为非法单横杠 | 待办 | P1 | 3 |  |  |

**Sprint 总点数**：10

**Issue 统计**：共 3 个 | 待办 1 | 方案已选择 0 | 方案已决策 0 | 方案设计中 0 | 实施中 0 | 进行中 1 | 设计完成 1 | 待验收 0 | 已完成 0 | 已取消 0 | 推迟 0 | 已关闭 0

## 用户故事详情

### US-001 为ConfigNode添加dict标准方法

> 作为配置管理库的用户，我希望ConfigNode支持keys()、values()、items()方法，以便可以像操作标准字典一样遍历和访问配置节点。

**状态**：进行中

**估算点数**：2

**验收标准**：
- [ ] ConfigNode实现keys()方法，返回所有配置键
- [ ] ConfigNode实现values()方法，返回所有配置值
- [ ] ConfigNode实现items()方法，返回所有键值对
- [ ] 所有方法行为与Python标准dict一致
- [ ] 添加完整的单元测试覆盖三个方法
- [ ] 通过ruff代码质量检查
- [ ] 所有现有测试继续通过

**优先级**：高
