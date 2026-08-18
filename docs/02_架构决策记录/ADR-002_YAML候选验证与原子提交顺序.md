# ADR-002：YAML 候选验证与原子提交顺序

**状态**：已接受
**日期**：2026-08-18
**决策者**：Tony（现行修订：`S1-03:solution-v8-review:approval:24` + 时序 41；初始接受：`solution-v3-review:approval:10` + 时序 11）
**相关 Issue**：`S1-03`
**相关文档**：`Docs/01_Sprint记录/Sprint01/S1-03/S1-03_方案决策.md`

## 生命周期记录

- `request_id`：`S1-03-ADR-DRAFT-DATA-002`
- `source_issue`：`S1-03`
- `source_stage`：`solution-decision`
- `design_doc`：`Docs/01_Sprint记录/Sprint01/S1-03/S1-03_方案决策.md`
- `phase`：`approval_draft`
- `action`：`create`
- `target_adr`：`NEW-S1-03-DATA-FLOW`
- `target_scope`：`project`
- `rationale`：仓库缺少数据流视图 ADR；S1-03 需要冻结 round-trip 数据准备、候选验证与 `os.replace` 的先后关系，使成功返回与可重新加载文件一致。
- `executor`：`architecture-design`
- `approval_locator`：空；草案阶段不接受最终授权。
- 草案结果：`status=drafted`、`resulting_adr=ADR-002`、`owner=architecture-design`、`completed_at=2026-08-18 Asia/Shanghai`。
- R2 草案修订：`request_id=S1-03-ADR-DRAFT-DATA-002-R2`、`phase=approval_draft`、`action=revise`、`target_adr=ADR-002`、`target_scope=project`、`executor=architecture-design`；理由为 R1 finding F-01 要求只在 `save_config` 主目标与 `save_config_only` 建立新门禁，备份保持既有语义；结果为 `status=drafted`、`resulting_adr=ADR-002`、`owner=architecture-design`、`completed_at=2026-08-18 Asia/Shanghai`，批准定位仍为空。
- 最终接受：`request_id=S1-03-ADR-FINAL-DATA-002`、`source_issue=S1-03`、`source_stage=solution-decision`、`design_doc=Docs/01_Sprint记录/Sprint01/S1-03/S1-03_方案决策.md`、`phase=approval_final`、`action=create`、`target_adr=ADR-002`、`target_scope=project`、`executor=architecture-design`；`approval_locator=approval_frame_id=S1-03:solution-v3-review:approval:10 + Docs/01_Sprint记录/Sprint01/S1-03/S1-03_处理记录.md#2026-08-18-时序-11`；结果为 `status=accepted`、`resulting_adr=ADR-002`、`owner=architecture-design`、`completed_at=2026-08-18 Asia/Shanghai`。
- solution-v8 最终修订：`request_id=S1-03-ADR-FINAL-DATA-002-V8`、`source_issue=S1-03`、`source_stage=solution-decision`、`design_doc=Docs/01_Sprint记录/Sprint01/S1-03/S1-03_方案决策.md#14-solution-v8-当前候选`、`phase=approval_final`、`action=revise`、`target_adr=ADR-002`、`target_scope=project`、`rationale=保存事务继续要求验证后替换，但数据准备和parser从ruamel round-trip改为统一PyYAML YAML 1.2 codec`、`executor=architecture-design`；`approval_locator=approval_frame_id=S1-03:solution-v8-review:approval:24 + Docs/01_Sprint记录/Sprint01/S1-03/S1-03_处理记录.md#2026-08-18-时序-41`；结果为 `status=accepted`、`resulting_adr=ADR-002`、`failure_reason=""`、`owner=architecture-design`、`completed_at=2026-08-18 Asia/Shanghai`。

## 历史 v3 决策正文（已由 solution-v8 修订，不再现行）

### 背景（Context）

当前保存链先把业务数据合并进 ruamel round-trip 树，dump 到临时文件，必要时做文本后处理，然后直接 `os.replace`。S1-03 的失败链同时违反了两个数据不变量：准备阶段把 `CommentedSeq` 降级并污染持久保存的原始树；提交阶段没有解析生成候选，因而把非法 YAML 当作成功结果。

目标不是改变 YAML 格式，而是明确保存事务的顺序和所有权：只有结构保真的候选经过最终形态解析后，才允许替换目标文件。

约束如下：

- 合并必须在 `_original_yaml_data` 的独立快照上执行，不能把一次保存的中间状态写回长期原始树。
- 只转换真实 `PathsConfigNode`；普通 list/dict 与 ruamel round-trip 容器必须保持各自语义。
- sequence 更新必须保留父键和 sequence 的注释关系，不以普通 list 替换带注释的 `CommentedSeq`。
- 主配置候选验证发生在该入口所有既有后处理之后、任何主配置目标替换之前。
- 主配置候选失败保持旧主配置不变，清理本轮临时资源，并沿用现有 `False`/可观察错误信息语义。

### 决策（Decision）

我们决定保存数据流固定为：

```text
ConfigManagerCore 的可序列化业务数据
  -> 复制原始 ruamel round-trip 树
  -> 仅转换 PathsConfigNode，保留 CommentedMap/CommentedSeq 及注释元数据
  -> 在复制树上递归合并；兼容 sequence 原地更新，不污染 _original_yaml_data
  -> dump 到同目录临时候选
  -> 执行该入口既有的重复键/anchor 后处理
  -> 用 YAML parser 重新解析最终候选
     -> 失败：拒绝提交、删除临时候选、旧主配置不变、返回 False
     -> 成功：os.replace 原子替换目标、返回 True
```

补充规则：

1. `save_config` 的主配置目标和初始化使用的 `save_config_only` 都必须满足“验证后替换”；这是已确认失败链中两个到期写入边界。
2. 可选备份及 `create_backup_only` 不在本次新增 parser 门禁范围；沿用并回归保护现有语义：主配置已经成功提交后，可选备份失败不改变主保存成功，备份错误单独可观察。
3. parser 验证的是后处理后的最终候选，而不是内存对象或后处理前文本。
4. 验证门禁不替代根因修复；仅有门禁会把成功写坏降级为失败，仍不满足“合法保存”的业务目标。

### 备选方案（Alternatives Considered）

### 方案 1：结构保真准备 + 最终候选验证 + 原子替换（已选择）

- 优点：同时恢复正常保存和失败安全；门禁位置覆盖序列化器与文本后处理器；旧目标可恢复。
- 缺点：每次保存增加一次解析；需要明确清理临时候选。
- 选择原因：唯一闭合全部已确认失败签名与文件安全验收的顺序。

### 方案 2：只修复 sequence 合并，不验证候选（未选择）

- 优点：正常路径改动较少。
- 缺点：未来任一序列化或文本后处理缺陷仍可被 `os.replace` 提交并返回成功。
- 不选择原因：不能建立“成功即重新可加载”的验收不变量。

### 方案 3：只增加解析门禁，不修复 round-trip 树（未选择）

- 优点：可以阻止当前非法文件覆盖旧目标。
- 缺点：commented sequence 的正常保存仍失败；只是止损，不是需求解决方案。
- 不选择原因：不满足用户要求的保存功能。

### 结果（Consequences）

正面影响：

- `save() == True` 与目标 YAML 可重新加载形成可测试的一致关系。
- `_original_yaml_data` 不再携带一次保存造成的中间不一致状态，重复保存行为稳定。
- 标准/raw、test/non-test、更新/未更新 sequence 共享一条数据流。

负面影响与成本：

- 深复制和解析验证使每次保存新增两次 `O(n)` 工作；配置树峰值内存增加一个独立快照和 parser 所需对象。
- 修改 `save_config` 时必须回归保护主文件与可选备份的既有失败语义，避免把备份失败误改为主文件失败；本 ADR 不新增备份行为。

技术债务：

- 文本重复键后处理仍存在；本 ADR 通过最终解析隔离其安全风险，不决定其未来替换方案。
- 不在本次决定 YAML schema、anchor 规范化或注释格式重排。

风险与缓解：

- parser 选择与 dump 配置不一致可能误拒绝合法扩展；使用项目现有 ruamel.yaml 语义，并以 anchor、注释、标准/raw 样本回归。
- Windows 临时文件替换与清理可能受占用影响；保留同目录临时文件与现有 `os.replace`，异常路径只删除本轮可确认创建的候选。

### 高内聚与低耦合证据

- 高内聚：本 ADR 只决定“数据在保存事务中以什么顺序变换、验证和提交”，不分配跨模块职责；所有条款都服务数据流原子性。
- 低耦合：职责 owner 仅引用 `ADR-001`；流程依赖现有 ruamel.yaml、同目录临时文件和 `os.replace`，不引入消费项目或新基础设施依赖。

### 参考资料

- `Docs/01_Sprint记录/Sprint01/S1-03/S1-03_系统诊断.md`
- `Docs/01_Sprint记录/Sprint01/S1-03/技术验证/reproduce_S1-03_20260818/02_minimal_output.txt`
- `Docs/01_Sprint记录/Sprint01/S1-03/技术验证/reproduce_S1-03_20260818/04_manager_pipeline_output.txt`
- `Docs/04_详细设计/yaml_comments_preservation_design.md`
- `Docs/02_架构决策记录/ADR-001_ConfigManager持久化职责边界.md`

## 现行 solution-v8 修订（已接受）

### 生命周期请求与结果

- `request_id`：`S1-03-ADR-DRAFT-DATA-002-V8`
- `source_issue`：`S1-03`
- `source_stage`：`solution-decision`
- `design_doc`：`Docs/01_Sprint记录/Sprint01/S1-03/S1-03_方案决策.md#14-solution-v8-当前候选`
- `phase`：`approval_draft`
- `action`：`revise`
- `target_adr`：`ADR-002`
- `target_scope`：`project`
- `rationale`：验证后替换的事务原则不变，但用户时序 38 允许移除 round-trip 保真；数据准备和 parser 应改为统一 PyYAML YAML 1.2 codec。
- `executor`：`architecture-design`
- `approval_locator`：空；草案不改变现行已接受状态。
- 结果：`status=drafted`、`resulting_adr=ADR-002`、`failure_reason=""`、`owner=architecture-design`、`completed_at=2026-08-18 Asia/Shanghai`。

### 背景与约束

S1-03 的不变量仍是“只有经最终形态重载验证的主配置候选才能替换目标”。时序 38 取消注释、样式和 anchor/alias round-trip 承诺后，不再需要原始树深复制、容器保真合并或重复键/anchor 文本后处理；事务输入改为标准包络的普通安全 YAML 数据。

候选约束：

- loader 与 dumper 必须共享 `yaml_codec` 的 YAML 1.2 resolver，避免 `yes/no/on/off/0123/0o17/1e3/1:20` 等标量 schema 漂移；loader 拒绝重复 mapping key。
- dump 前递归验证字符串 mapping key 和声明的 YAML 数据类型；tuple、set、自定义对象及其他未声明类型失败，不允许隐式转换后提交。
- 主配置的语义比较覆盖递归 mapping/sequence、标量类型和值；NaN 由双方均为 NaN 判等；mapping 顺序和对象引用身份不作为语义。
- 无法安全表示、解析失败、语义不等或替换失败都不得覆盖旧目标。
- 只清理本轮唯一创建的同目录候选；不删除来源不明的 `.tmp`。
- 可选备份继续是主配置提交后的 best-effort；备份失败不回滚已成功主配置。`create_backup_only` 仍按自身 bool 语义报告。

### Decision

```text
ConfigManagerCore 的标准数据文档
  -> FileOperations 转换 PathsConfigNode 为普通 YAML 数据
  -> yaml_codec safe dump 到本轮唯一同目录临时候选
  -> 关闭并重新打开候选
  -> 同一 yaml_codec safe load
  -> 与待保存普通数据做递归语义比较
     -> dump/load/compare 失败或不等：拒绝提交、清理本轮候选、旧目标不变、返回 False
     -> 相等：os.replace 原子替换主目标、返回 True
```

补充规则：

1. `save_config` 和 `save_config_only` 的主目标都执行完整门禁；auto-create 进入同一保存边界。
2. raw 输入的首次保存直接生成标准 `__data__/__type_hints__` 文档，不把原 raw mapping 合并进候选。
3. 不执行重复键或 anchor 文本后处理；候选只来自一个 Python mapping，任何 serializer 缺陷由最终 safe load/比较门禁截断。
4. parser 验证临时文件的最终字节，不验证内存字符串或前处理版本。
5. `save()==True` 不扩张为断电持久性、多进程互斥或备份成功保证。

### Alternatives and Consequences

- 选定“直接普通数据 dump + 同 codec 重载比较 + replace”：同时满足合法 sequence、成功一致性和失败安全，状态最少。
- 不选裸 PyYAML：验证证实 YAML 1.1/1.2 标量差异会改值或类型。
- 不选 round-trip 合并：用户已取消文本保真，保留它只增加共享状态、分支和错误面。
- 不选只增加 parser 门禁：虽能止损，但若 serializer 不能正确输出合法 sequence 会把正常功能降为失败。
- 正面：每次保存只剩一次 dump、一次 load/比较和一次 replace；删除深复制/合并/文本后处理。
- 成本：每次主保存仍有 `O(n)` 的重载和比较；raw 文件布局首次保存会规范化；不支持 unsafe Python tag。
- 风险控制：S1-03 AC8-01..10 覆盖 schema、sequence、raw/standard、模式、异常、备份与消费侧等价复现。

### 高内聚与低耦合

- 高内聚：本 ADR 仍只决定候选从普通数据到验证、提交或拒绝的顺序，不分配跨模块 owner。
- 低耦合：owner 只引用 ADR-001；schema 规则只引用 `yaml_codec` 唯一真源，不在 ADR 中复制实现正则。

本修订已由 frame24 与时序 41 的完整方案批准授权，并由 `architecture-design` 以 `phase=approval_final/action=revise` 接受；本节是 ADR-002 当前现行决策，历史 v3 正文只保留审计身份。
