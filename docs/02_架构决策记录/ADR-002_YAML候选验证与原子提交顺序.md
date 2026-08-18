# ADR-002：YAML 候选验证与原子提交顺序

**状态**：已接受
**日期**：2026-08-18
**决策者**：Tony（`S1-03:solution-v3-review:approval:10` + 时序 11）
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

## 背景（Context）

当前保存链先把业务数据合并进 ruamel round-trip 树，dump 到临时文件，必要时做文本后处理，然后直接 `os.replace`。S1-03 的失败链同时违反了两个数据不变量：准备阶段把 `CommentedSeq` 降级并污染持久保存的原始树；提交阶段没有解析生成候选，因而把非法 YAML 当作成功结果。

目标不是改变 YAML 格式，而是明确保存事务的顺序和所有权：只有结构保真的候选经过最终形态解析后，才允许替换目标文件。

约束如下：

- 合并必须在 `_original_yaml_data` 的独立快照上执行，不能把一次保存的中间状态写回长期原始树。
- 只转换真实 `PathsConfigNode`；普通 list/dict 与 ruamel round-trip 容器必须保持各自语义。
- sequence 更新必须保留父键和 sequence 的注释关系，不以普通 list 替换带注释的 `CommentedSeq`。
- 主配置候选验证发生在该入口所有既有后处理之后、任何主配置目标替换之前。
- 主配置候选失败保持旧主配置不变，清理本轮临时资源，并沿用现有 `False`/可观察错误信息语义。

## 决策（Decision）

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

## 备选方案（Alternatives Considered）

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

## 结果（Consequences）

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

## 高内聚与低耦合证据

- 高内聚：本 ADR 只决定“数据在保存事务中以什么顺序变换、验证和提交”，不分配跨模块职责；所有条款都服务数据流原子性。
- 低耦合：职责 owner 仅引用 `ADR-001`；流程依赖现有 ruamel.yaml、同目录临时文件和 `os.replace`，不引入消费项目或新基础设施依赖。

## 参考资料

- `Docs/01_Sprint记录/Sprint01/S1-03/S1-03_系统诊断.md`
- `Docs/01_Sprint记录/Sprint01/S1-03/技术验证/reproduce_S1-03_20260818/02_minimal_output.txt`
- `Docs/01_Sprint记录/Sprint01/S1-03/技术验证/reproduce_S1-03_20260818/04_manager_pipeline_output.txt`
- `Docs/04_详细设计/yaml_comments_preservation_design.md`
- `Docs/02_架构决策记录/ADR-001_ConfigManager持久化职责边界.md`
