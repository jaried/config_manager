# NEW-CM-LAYERED-CONFIG: 只读基础层与可写覆盖层的双文件配置

- 状态：草案（approval_draft），待用户最终批准
- 作用域：config_manager 项目
- 相关方案：base_env `docs/01_Sprint记录/Sprint06/00-联合方案决策/2026-11-04/联合方案决策.md` §5.2；切片 `cm-dual-config`

## 生命周期请求

- request_id：`CM-LAYERED-CONFIG-CREATE-DRAFT-01`
- source_issue：`cm-dual-config`（正式编号发布时登记）
- source_stage：`solution-decision`
- phase / action / scope：`approval_draft / create / project`
- target_adr：`NEW-CM-LAYERED-CONFIG`
- executor：`architecture-design`
- rationale：消费项目需要「多入口共用的通用配置 + 单入口专用配置」；现有 ConfigManager 只认一个文件并整份回写，消费方若自行合并会复制配置状态 owner。
- approval_locator：空（草案阶段）

## 背景

ConfigManager 是记忆型配置所有者：非 test_mode 会把 `first_start_time`、派生 `paths` 等回写到配置文件。base_env 有多个入口，需要共享 `project_name`、`base_dir`、logger、profiling 与通知设置，同时每个入口有自己的标的和周期。把共享项复制进每个入口的配置会产生多份真源；让一个入口整份回写共享文件会把它的运行记忆写进其他入口的输入。

现行 ADR-001 规定 `ConfigManagerCore` 拥有配置状态、保存触发与模式编排，`FileOperations` 拥有文件事务；ADR-002 规定候选验证后原子替换。

## 决策

1. `get_config_manager` 接受可选的 `base_config_path`。给出时配置由两层组成：基础层（只读）与覆盖层（`config_path`，可写）。
2. 读取视图是两层逐层合并的结果：mapping 对 mapping 递归，其余类型由覆盖层整体替换；类型提示按键合并，覆盖层优先。worker 快照使用合并视图。
3. 保存只把「基础层没有」或「值与基础层不同」的键写入覆盖层；基础层在任何模式下都不被写入或备份。
4. 合并与差集计算属于 `ConfigManagerCore` 的配置状态职责；两层文件的读取与覆盖层的保存事务继续由 `FileOperations` 按 ADR-001、ADR-002 执行。
5. `base_config_path` 只与 `watch=False` 组合；同时要求监视时抛 `ValueError`。
6. test_mode 只把覆盖层复制进测试环境；基础层原位只读，测试路径与数据库切换写入覆盖层副本。

## 备选与取舍

| 方案 | 影响 | 结论 |
|---|---|---|
| ConfigManager 原生两层，覆盖层只存差集 | 共享项单一真源；入口记忆只落在自己的文件；新增一个可选参数 | 采用 |
| 同一文件内按入口分段 | 所有入口共写一个文件，回写互相覆盖 | 不采用 |
| 消费方自行合并后交给 ConfigManager | 消费方复制配置状态职责，回写仍是整份 | 不采用 |

成本：保存时多一次差集计算（与配置树大小线性）；覆盖层文件内容随运行回写变化。

## 结果

- 无 `base_config_path` 的调用方行为不变。
- 基础层的修改对所有使用它的入口立即生效（下次启动）。
- 监视两层文件的需求出现时，重新评估第 5 条。

## 关联

- ADR-001 ConfigManager 持久化职责边界：职责划分不变，本 ADR 增加分层状态。
- ADR-002 YAML 候选验证与原子提交顺序：覆盖层保存沿用同一事务。
