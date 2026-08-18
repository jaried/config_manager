# ADR-001：ConfigManager 持久化职责边界

**状态**：已接受
**日期**：2026-08-18
**决策者**：Tony（`S1-03:solution-v3-review:approval:10` + 时序 11）
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

## 背景（Context）

ConfigManager 采用分层结构：`ConfigManagerCore` 管理配置状态、公开保存入口和模式编排，`FileOperations` 处理 YAML 加载、准备、序列化和文件提交。S1-03 证明，如果 round-trip 容器语义在 `FileOperations` 内被破坏，而生成结果又未经验证就替换目标文件，调用者会在 `save()` 返回成功时得到不可解析文件。

现有架构文档已经把文件操作和 YAML 处理归给 `FileOperations`，但仓库没有 ADR 冻结这条职责边界。缺少决策记录容易诱发三类错误方向：在 `ConfigManagerCore` 重复实现 YAML 细节、在消费项目按业务键绕过缺陷、或由调用者承担持久化正确性验证。

约束如下：

- `ConfigManagerCore.save()` 的公开调用方式和布尔成功语义保持兼容。
- YAML round-trip 格式、注释与原子文件提交仍由 `FileOperations` 统一拥有。
- 不把 S1-03 扩张为 raw YAML 格式重构、业务键特判或新序列化技术选型。
- 测试模式与非测试模式共享相同持久化正确性边界。

## 决策（Decision）

我们决定：

1. `ConfigManagerCore` 继续拥有配置状态、保存触发、测试/非测试模式编排以及对外 `save() -> bool` 契约；它只向文件层提交可序列化业务数据，不承担 ruamel 注释元数据修复。
2. `FileOperations` 独占 YAML 加载、round-trip 树快照、`PathsConfigNode` 转换、结构保真合并、主配置候选序列化/验证、目标替换和既有备份写入职责。
3. 公开 `save()` 的“返回成功”必须表示主配置持久化结果已经通过 YAML 重新解析门禁；主配置候选无效时，`FileOperations` 保留旧主配置并按现有布尔契约返回失败。
4. 任何消费项目、业务键名或调用模式不得承担 S1-03 的根因修复；标准/raw、test/non-test 使用同一文件层不变量。
5. 本决策不改变公开 API，不引入新的跨模块依赖；`ConfigManagerCore -> FileOperations -> ruamel.yaml/os` 仍是单向依赖。

## 备选方案（Alternatives Considered）

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

## 结果（Consequences）

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

## 高内聚与低耦合证据

- 高内聚：本 ADR 只回答“配置状态、持久化正确性和文件提交分别由谁拥有”，不规定内部算法步骤；背景、约束和结果都服务职责边界。
- 低耦合：仅依赖现有 `ConfigManagerCore -> FileOperations` 单向关系和公开布尔契约；具体保存顺序引用 `ADR-002`，不复制其流程正文。

## 参考资料

- `Docs/02_架构设计/架构设计.md`
- `Docs/04_详细设计/architecture_design.md`
- `Docs/04_详细设计/yaml_comments_preservation_design.md`
- `Docs/01_Sprint记录/Sprint01/S1-03/S1-03_系统诊断.md`
- `Docs/02_架构决策记录/ADR-002_YAML候选验证与原子提交顺序.md`
