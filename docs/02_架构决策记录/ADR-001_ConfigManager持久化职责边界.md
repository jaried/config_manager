# ADR-001：ConfigManager 持久化职责边界

**状态**：已接受
**日期**：2026-08-18
**决策者**：Tony（现行修订：`S1-03:solution-v8-review:approval:24` + 时序 41；初始接受：`solution-v3-review:approval:10` + 时序 11）
**相关 Issue**：`S1-03`
**相关文档**：`Docs/01_Sprint记录/Sprint01/S1-03/S1-03_方案决策.md`

## 生命周期记录

- `request_id`：`S1-03-ADR-DRAFT-ARCH-001`
- `source_issue`：`S1-03`
- `source_stage`：`solution-decision`
- `design_doc`：`Docs/01_Sprint记录/Sprint01/S1-03/S1-03_方案决策.md`
- `phase`：`approval_draft`
- `action`：`create`
- `target_adr`：`NEW-S1-03-SYSTEM-ARCHITECTURE`
- `target_scope`：`project`
- `rationale`：仓库缺少系统架构视图 ADR；S1-03 需要冻结配置状态 owner、YAML 持久化 owner 与调用边界，防止在消费项目或业务键上修补序列化缺陷。
- `executor`：`architecture-design`
- `approval_locator`：空；草案阶段不接受最终授权。
- 草案结果：`status=drafted`、`resulting_adr=ADR-001`、`owner=architecture-design`、`completed_at=2026-08-18 Asia/Shanghai`。
- R2 草案修订：`request_id=S1-03-ADR-DRAFT-ARCH-001-R2`、`phase=approval_draft`、`action=revise`、`target_adr=ADR-001`、`target_scope=project`、`executor=architecture-design`；理由为 R1 finding F-01 要求把新增 parser 门禁收窄到已证实的主配置边界；结果为 `status=drafted`、`resulting_adr=ADR-001`、`owner=architecture-design`、`completed_at=2026-08-18 Asia/Shanghai`，批准定位仍为空。
- 最终接受：`request_id=S1-03-ADR-FINAL-ARCH-001`、`source_issue=S1-03`、`source_stage=solution-decision`、`design_doc=Docs/01_Sprint记录/Sprint01/S1-03/S1-03_方案决策.md`、`phase=approval_final`、`action=create`、`target_adr=ADR-001`、`target_scope=project`、`executor=architecture-design`；`approval_locator=approval_frame_id=S1-03:solution-v3-review:approval:10 + Docs/01_Sprint记录/Sprint01/S1-03/S1-03_处理记录.md#2026-08-18-时序-11`；结果为 `status=accepted`、`resulting_adr=ADR-001`、`owner=architecture-design`、`completed_at=2026-08-18 Asia/Shanghai`。
- solution-v8 最终修订：`request_id=S1-03-ADR-FINAL-ARCH-001-V8`、`source_issue=S1-03`、`source_stage=solution-decision`、`design_doc=Docs/01_Sprint记录/Sprint01/S1-03/S1-03_方案决策.md#14-solution-v8-当前候选`、`phase=approval_final`、`action=revise`、`target_adr=ADR-001`、`target_scope=project`、`rationale=时序38取消round-trip文本保真并批准整个包移除ruamel；职责owner与公开bool契约保留但技术约束改为统一PyYAML codec`、`executor=architecture-design`；`approval_locator=approval_frame_id=S1-03:solution-v8-review:approval:24 + Docs/01_Sprint记录/Sprint01/S1-03/S1-03_处理记录.md#2026-08-18-时序-41`；结果为 `status=accepted`、`resulting_adr=ADR-001`、`failure_reason=""`、`owner=architecture-design`、`completed_at=2026-08-18 Asia/Shanghai`。

## 历史 v3 决策正文（已由 solution-v8 修订，不再现行）

### 背景（Context）

ConfigManager 采用分层结构：`ConfigManagerCore` 管理配置状态、公开保存入口和模式编排，`FileOperations` 处理 YAML 加载、准备、序列化和文件提交。S1-03 证明，如果 round-trip 容器语义在 `FileOperations` 内被破坏，而生成结果又未经验证就替换目标文件，调用者会在 `save()` 返回成功时得到不可解析文件。

现有架构文档已经把文件操作和 YAML 处理归给 `FileOperations`，但仓库没有 ADR 冻结这条职责边界。缺少决策记录容易诱发三类错误方向：在 `ConfigManagerCore` 重复实现 YAML 细节、在消费项目按业务键绕过缺陷、或由调用者承担持久化正确性验证。

约束如下：

- `ConfigManagerCore.save()` 的公开调用方式和布尔成功语义保持兼容。
- YAML round-trip 格式、注释与原子文件提交仍由 `FileOperations` 统一拥有。
- 不把 S1-03 扩张为 raw YAML 格式重构、业务键特判或新序列化技术选型。
- 测试模式与非测试模式共享相同持久化正确性边界。

### 决策（Decision）

我们决定：

1. `ConfigManagerCore` 继续拥有配置状态、保存触发、测试/非测试模式编排以及对外 `save() -> bool` 契约；它只向文件层提交可序列化业务数据，不承担 ruamel 注释元数据修复。
2. `FileOperations` 独占 YAML 加载、round-trip 树快照、`PathsConfigNode` 转换、结构保真合并、主配置候选序列化/验证、目标替换和既有备份写入职责。
3. 公开 `save()` 的“返回成功”必须表示主配置持久化结果已经通过 YAML 重新解析门禁；主配置候选无效时，`FileOperations` 保留旧主配置并按现有布尔契约返回失败。
4. 任何消费项目、业务键名或调用模式不得承担 S1-03 的根因修复；标准/raw、test/non-test 使用同一文件层不变量。
5. 本决策不改变公开 API，不引入新的跨模块依赖；`ConfigManagerCore -> FileOperations -> ruamel.yaml/os` 仍是单向依赖。

### 备选方案（Alternatives Considered）

### 方案 1：在 FileOperations 内修复并建立保存门禁（已选择）

- 优点：根因与责任 owner 一致；所有调用模式一次修复；公开 API 不变；可以把“成功”与“可重新加载”绑定。
- 缺点：每次保存增加一次结构复制和一次候选解析，时间与峰值内存仍为配置树大小的线性量级。
- 选择原因：它是唯一同时满足根因修复、职责隔离、文件安全和兼容性的候选。

### 方案 2：在 ConfigManagerCore 或消费项目规避 commented sequence（未选择）

- 优点：局部补丁表面改动小。
- 缺点：复制 YAML 细节、遗漏其他调用路径、依赖业务键、无法保证保存结果可解析。
- 不选择原因：违反现有模块职责且没有消除根因。

### 方案 3：放弃 round-trip 注释结构，统一转普通 dict/list（未选择）

- 优点：序列化模型简单。
- 缺点：破坏已经承诺的注释保留与格式兼容行为。
- 不选择原因：以功能回退换取合法 YAML，不满足需求边界。

### 结果（Consequences）

正面影响：

- YAML 持久化不变量有唯一 owner，调用者不需要理解 ruamel 内部元数据。
- 标准/raw 和 test/non-test 不再形成不同修复分支。
- 无效主配置候选不能覆盖已存在的合法主配置文件。
- 下游设计和评审可以只围绕 `FileOperations` 与其契约测试展开。

负面影响与成本：

- 保存路径增加一次深复制和一次解析验证，CPU 与峰值内存为 `O(n)`；这是用可验证文件安全换取的明确成本。
- `FileOperations` 的职责描述需要从“加载/保存”细化为“准备/验证/原子提交”，但模块边界不变。

技术债务：

- 现存基于文本行的重复键后处理器不在 S1-03 中重构；主配置候选解析门禁负责阻止它产生的任何非法结果进入主配置目标。
- raw-to-standard 的 anchor/投影重复现象继续作为排除项，除非未来独立 Issue 证明其业务影响。

风险与缓解：

- 深复制若未覆盖 ruamel 容器会再次破坏注释元数据；以容器类型、注释保留和重复保存回归测试约束。
- 主配置失败路径若遗留临时文件会污染目录；以异常注入测试验证旧主文件不变和本轮临时资源清理。

### 高内聚与低耦合证据

- 高内聚：本 ADR 只回答“配置状态、持久化正确性和文件提交分别由谁拥有”，不规定内部算法步骤；背景、约束和结果都服务职责边界。
- 低耦合：仅依赖现有 `ConfigManagerCore -> FileOperations` 单向关系和公开布尔契约；具体保存顺序引用 `ADR-002`，不复制其流程正文。

### 参考资料

- `Docs/02_架构设计/架构设计.md`
- `Docs/04_详细设计/architecture_design.md`
- `Docs/04_详细设计/yaml_comments_preservation_design.md`
- `Docs/01_Sprint记录/Sprint01/S1-03/S1-03_系统诊断.md`
- `Docs/02_架构决策记录/ADR-002_YAML候选验证与原子提交顺序.md`

## 现行 solution-v8 修订（已接受）

### 生命周期请求与结果

- `request_id`：`S1-03-ADR-DRAFT-ARCH-001-V8`
- `source_issue`：`S1-03`
- `source_stage`：`solution-decision`
- `design_doc`：`Docs/01_Sprint记录/Sprint01/S1-03/S1-03_方案决策.md#14-solution-v8-当前候选`
- `phase`：`approval_draft`
- `action`：`revise`
- `target_adr`：`ADR-001`
- `target_scope`：`project`
- `rationale`：用户时序 38 取消 round-trip 文本保真并允许整个包移除 ruamel；职责 owner 与公开 bool 契约继续成立，但现行 ruamel/注释约束需要更新。
- `executor`：`architecture-design`
- `approval_locator`：空；草案不改变现行已接受状态。
- 结果：`status=drafted`、`resulting_adr=ADR-001`、`failure_reason=""`、`owner=architecture-design`、`completed_at=2026-08-18 Asia/Shanghai`。

### 背景与约束

ConfigManager 仍由 `ConfigManagerCore` 管理状态、模式和公开保存入口，由 `FileOperations` 管理文件事务。变化是 YAML 表达不再以 ruamel round-trip 树为长期状态：一个独立 `yaml_codec` 统一拥有 PyYAML YAML 1.2 安全 schema，FileOperations 只消费普通数据并负责候选验证和文件提交。

候选约束：

- `save() -> bool` 的公开调用和成功语义不变；`True` 表示主目标可由同一 codec 安全重载且数据语义相等。
- 只保证业务键、值、mapping、sequence 和支持的 YAML 标量类型；不保证注释、样式、anchor/alias 表达或 raw 根布局原样。
- raw 输入仍可加载，首次成功保存允许规范化为标准 `__data__/__type_hints__` 包络。
- test/non-test、standard/raw 共享同一 codec 和 FileOperations 事务；消费项目和业务键不承担修复。
- 单向依赖为 `ConfigManagerCore -> FileOperations -> yaml_codec -> PyYAML`，同时 `FileOperations -> os`；facade 辅助可直接依赖 codec，codec 不反向依赖 manager/file layer。

### Decision

1. `ConfigManagerCore` 继续拥有配置状态、保存触发、模式编排和公开 `save() -> bool` 契约；不拥有 YAML resolver、dump 或文件替换。
2. `yaml_codec` 独占 YAML 1.2 safe loader/dumper resolver、重复 mapping key 拒绝、支持类型验证和数据语义等价判断；所有产品 YAML 入口及 manager 序列化预检必须复用它，不得裸调分散的 `safe_load/safe_dump`。
3. `FileOperations` 独占普通数据准备、临时候选生命周期、候选重载验证、`os.replace` 和既有备份写入；不再保存或合并 round-trip 树，不再做 anchor/重复键文本修复。
4. 主配置候选无效或语义不等时，FileOperations 保留旧目标、清理本轮候选并沿用布尔失败与可观察错误语义。
5. `ConfigManagerCore` 不访问 `_file_ops._yaml` 等私有 serializer；消费项目、业务键和调用模式不得包含 S1-03 补丁。

### Alternatives and Consequences

- 选定职责拆分：`yaml_codec` 只负责 schema/data，`FileOperations` 只负责 file transaction，`ConfigManagerCore` 只负责 state/API；每个变化原因只有一个 owner。
- 不选把 codec 全塞进 FileOperations：测试配置和 raw 内容辅助也需要同一 schema，会迫使 facade 访问文件层私有实现或重复 resolver。
- 不选在 ConfigManagerCore/消费项目规避 sequence：会复制 YAML 细节并遗漏调用路径。
- 正面：删除长期 round-trip 共享状态和跨层私有 serializer 访问；所有 YAML 入口 schema 一致；公开 API 不变。
- 成本：新增一个小型内部 codec 模块；文本保真与 unsafe Python tag 不兼容；依赖从 ruamel 迁移为 PyYAML。
- 风险控制：resolver/安全标签/raw 规范化/失败不覆盖由 S1-03 AC8-01..10 验证；当前说明文档同步数据语义口径；无关大文件重构、消费侧修改和多进程保存协议排除。

### 高内聚与低耦合

- 高内聚：本 ADR 仍只决定“状态、YAML schema 和文件事务分别由谁拥有”；具体事务顺序继续由 ADR-002 决定。
- 低耦合：codec 只依赖 PyYAML，FileOperations 只通过 codec 接口处理 YAML；本 ADR 不复制 resolver 正则或测试矩阵，直接引用 solution-v8 与 ADR-002。

本修订已由 frame24 与时序 41 的完整方案批准授权，并由 `architecture-design` 以 `phase=approval_final/action=revise` 接受；本节是 ADR-001 当前现行决策，历史 v3 正文只保留审计身份。
