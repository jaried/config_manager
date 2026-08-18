# ADR-002：test_mode 数据库地址数据流

- 状态：已接受
- 日期：2026-08-18
- Issue：S1-02
- 视图：data_flow
- 决策所有者：architecture-design
- 生命周期请求：`S1-02-ADR-DATA-001`

## 背景

S1-02 需要在配置中预先声明测试数据库地址，并在 `test_mode=true` 时自动切换。原始需求未指定键名、缺失值行为或配置文件格式差异，必须冻结一个不会静默使用生产地址的数据契约。

## 决策

采用以下最小配置契约：

整体批准前，本 ADR 是 `S1-02-solution-v5` §7 的数据流派生草案，候选真源仍为方案正文。整体批准且本 ADR 进入“已接受”后，本 ADR 成为数据库选择数据流的架构真源，方案继续负责需求、取舍与验收。两者不一致时必须停止接力并由 `architecture-design` 修正。

```yaml
database:
  address: "production-database-address"
  test_address: "test-database-address"
```

两个值均作为不透明标量处理，`config_manager` 不解析协议、主机、端口、库名或凭据。

`test_mode` 的权威触发源是 `get_config_manager(..., test_mode=True)` 的公开 API 参数；配置数据内的同名普通键不反向决定实例模式。

### 模式规则

| 条件 | 结果 |
|---|---|
| `test_mode=False` | 不改变 `database.address`；`database.test_address` 为被动配置 |
| `test_mode=True` 且不存在 `database` | 保持无操作，兼容不使用数据库的通用配置 |
| `test_mode=True` 且存在 `database`，同时 `test_address` 为非空字符串 | 在临时副本中设置 `database.address = database.test_address` |
| `test_mode=True` 且存在 `database`，但 `test_address` 缺失、为 `null`、空串或纯空白 | 抛出专用配置错误，禁止继续加载，禁止保留生产地址 |
| `test_mode=True` 且有有效 `test_address`、没有原 `address` | 在临时副本中创建活动 `address` |

### 配置根定位

- 标准格式：数据库节点位于顶层 `__data__.database`。
- 原始 YAML 格式：数据库节点位于文档根 `database`。
- 节点存在但不是映射时，按无效配置快速失败。

## 数据流

```text
生产配置文件（只读）
  -> 复制到临时测试目录
  -> 定位数据根（__data__ 或原始根）
  -> 校验 database/test_address
  -> 临时副本 database.address := database.test_address
  -> 现有 ConfigManager 加载与验证
  -> 现有快照记录活动测试地址
  -> 调用方读取 database.address
```

任何校验失败都在测试实例创建前终止；数据不得回写生产文件。

## 数据流变更集

| 数据 | 来源 | 转换 | 消费方 | 持久化边界 |
|---|---|---|---|---|
| `database.address` | 生产配置 | 测试模式下由有效 `test_address` 替换 | 业务调用方、现有快照 | 仅临时测试副本 |
| `database.test_address` | 生产配置 | 只校验，不解析 | 测试副本转换 helper | 生产配置原样保留；临时副本保留 |
| 配置错误 | 测试副本转换 | 仅包含键路径与原因 | 调用方/测试框架 | 不记录地址值 |

## 备选契约

曾考虑 `test_mode_overrides.database.address` 的通用映射。该结构会引入点路径解析、任意类型覆盖和冲突优先级，超出当前单一数据库地址需求，因此否决。

## 兼容与迁移

- 没有 `database` 节点的既有配置保持原行为。
- 存在 `database` 节点且启用测试模式的使用者，需要先补充 `test_address`；这是为了消除静默使用生产地址的安全风险。
- `test_mode=False` 的生产读取路径保持不变。
- 配置项名称与失败规则同步写入 `README.md` 和 `py-config-logger`。

## 验证要求

- 覆盖标准格式、原始 YAML、地址缺失/空白、布尔/整数/列表/映射等非字符串地址、节点类型错误、无数据库节点和仅有测试地址的情况。
- 验证临时副本、运行时读取结果与配置快照一致。
- 验证异常文本和日志不包含任一地址值。

## 生命周期记录

### 批准前草案

- `source_issue=S1-02`
- `source_stage=solution-decision`
- `design_doc=docs/01_Sprint记录/Sprint01/S1-02/S1-02_方案决策.md`
- `phase=approval_draft`
- `action=create`
- `target_adr=ADR-002`
- `target_scope=project`
- `rationale=冻结 test_mode 数据库地址选择的数据流契约`
- `executor=architecture-design`
- `request_id=S1-02-ADR-DATA-001`
- `approval_locator=""`
- `status=drafted`
- `resulting_adr=docs/02_架构决策记录/ADR-002_test_mode数据库地址数据流.md`
- `owner=architecture-design`
- `completed_at=2026-08-18`

### 批准后最终动作

- `source_issue=S1-02`
- `source_stage=solution-decision`
- `design_doc=docs/01_Sprint记录/Sprint01/S1-02/S1-02_方案决策.md`
- `phase=approval_final`
- `action=create`
- `target_adr=ADR-002`
- `target_scope=project`
- `rationale=用户已批准 S1-02-solution-v5 完整方案及其中的 ADR-002 create 动作`
- `executor=architecture-design`
- `request_id=S1-02-ADR-DATA-001`
- `approval_locator=S1-02:S1-02-solution-v5:approval:2 + conversation:current-thread:assistant-final@S1-02:S1-02-solution-v5:approval:2 + conversation:current-thread:user-reply-1@S1-02:S1-02-solution-v5:approval:2`
- `status=accepted`
- `resulting_adr=docs/02_架构决策记录/ADR-002_test_mode数据库地址数据流.md`
- `owner=architecture-design`
- `completed_at=2026-08-18`
