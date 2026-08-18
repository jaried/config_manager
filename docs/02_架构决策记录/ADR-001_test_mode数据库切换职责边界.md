# ADR-001：test_mode 数据库切换职责边界

- 状态：已接受
- 日期：2026-08-18
- Issue：S1-02
- 视图：system_architecture
- 决策所有者：architecture-design
- 生命周期请求：`S1-02-ADR-SYSTEM-001`

## 背景

`ConfigManager.get_config_manager(..., test_mode=True)` 当前会把生产配置复制到临时目录，并仅把 `base_dir` 改为测试目录。数据库配置会原样进入测试实例，存在测试误用生产数据库地址的风险。S1-02 同时要求更新 `py-config-logger` 的使用规范，但不允许拆成多个 Issue。

## 决策

数据库地址切换由 `config_manager` 的测试配置转换阶段负责：生产配置复制完成后、测试 `ConfigManager` 实例加载前，在临时副本中把 `database.test_address` 选为活动的 `database.address`。

### 真源关系

S1-02 整体批准前，本 ADR 是 `S1-02-solution-v5` §6 的系统架构派生草案，候选真源仍为方案正文。整体批准且本 ADR 进入“已接受”后，本 ADR 成为该职责边界的架构真源，方案继续负责需求、取舍与验收。两者不一致时必须停止接力并由 `architecture-design` 修正。

职责边界如下：

- `config_manager` 负责读取、校验和选择配置值；不连接数据库，也不验证网络可达性。
- 生产配置文件只作为输入，禁止原地改写；所有切换只发生在临时测试副本。
- `py-config-logger` 只记录配置契约、启动生命周期、失败语义和示例；不得成为项目运行时依赖。
- 快照继续由现有配置快照能力生成，记录切换后的活动值；不得新增第二套快照实现。
- 不恢复历史上已移除的递归路径替换，也不新增通用测试覆盖引擎。

## 模块变更集

| 模块 | 责任 | 预期变更 |
|---|---|---|
| `src/config_manager/config_manager.py` | 测试副本转换 owner | 在现有 `_update_test_config_paths` 流程中调用窄范围数据库选择 helper，并让配置契约错误穿透既有 YAML 回退 |
| `tests/01_unit_tests/test_config_manager/` | 行为与回归证据 | 新增测试数据库切换、失败语义、源配置不变和格式兼容测试 |
| `README.md` | 项目公开说明 | 补充配置样例、模式行为和安全失败规则 |
| `skills/py-config-logger/` | 跨仓库规范 | 更新 Skill 入口与参考指南，不引入运行时依赖 |

## 备选方案

### A. 在 `ConfigManager` 测试副本转换阶段切换（采用）

复用现有 `test_mode` 生命周期，切换时机明确，生产源文件不可变，调用方无需重复实现。

### B. 由每个应用或测试夹具自行覆盖（否决）

无法保证所有入口一致执行，容易遗漏并继续连接生产数据库，也无法由 `py-config-logger` 给出统一可验证契约。

### C. 新增通用 `test_mode_overrides` 引擎（否决）

当前需求只有一个数据库地址，通用路径覆盖会扩大解析、类型、冲突和错误处理面，不符合最小改动原则。

## 影响

- 正向：测试入口统一获得安全的数据库选择行为，调用方零额外切换代码。
- 约束：任何使用此能力的配置必须把数据库地址视为不透明标量；连接参数拆分不在本 Issue 范围。
- 跨仓库：项目代码与全局 Skill 分别提交，但使用同一 Issue、同一方案版本和同一验收边界。

## 验证要求

- 证明切换发生在临时副本且生产源配置字节不变。
- 证明 `test_mode=False` 不改变活动地址。
- 证明标准 `__data__` 格式与原始 YAML 格式均受支持。
- 证明错误信息不输出生产或测试地址内容。
- 证明 `py-config-logger` 文档与实际行为一致。

## 生命周期记录

### 批准前草案

- `source_issue=S1-02`
- `source_stage=solution-decision`
- `design_doc=docs/01_Sprint记录/Sprint01/S1-02/S1-02_方案决策.md`
- `phase=approval_draft`
- `action=create`
- `target_adr=ADR-001`
- `target_scope=project`
- `rationale=冻结 test_mode 数据库切换的系统职责边界`
- `executor=architecture-design`
- `request_id=S1-02-ADR-SYSTEM-001`
- `approval_locator=""`
- `status=drafted`
- `resulting_adr=docs/02_架构决策记录/ADR-001_test_mode数据库切换职责边界.md`
- `owner=architecture-design`
- `completed_at=2026-08-18`

### 批准后最终动作

- `source_issue=S1-02`
- `source_stage=solution-decision`
- `design_doc=docs/01_Sprint记录/Sprint01/S1-02/S1-02_方案决策.md`
- `phase=approval_final`
- `action=create`
- `target_adr=ADR-001`
- `target_scope=project`
- `rationale=用户已批准 S1-02-solution-v5 完整方案及其中的 ADR-001 create 动作`
- `executor=architecture-design`
- `request_id=S1-02-ADR-SYSTEM-001`
- `approval_locator=S1-02:S1-02-solution-v5:approval:2 + conversation:current-thread:assistant-final@S1-02:S1-02-solution-v5:approval:2 + conversation:current-thread:user-reply-1@S1-02:S1-02-solution-v5:approval:2`
- `status=accepted`
- `resulting_adr=docs/02_架构决策记录/ADR-001_test_mode数据库切换职责边界.md`
- `owner=architecture-design`
- `completed_at=2026-08-18`
