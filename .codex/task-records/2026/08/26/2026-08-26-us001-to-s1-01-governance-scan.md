# 项目文档治理一次性报告

- 扫描根目录：`D:\Tony\Documents\invest2025\project\config_manager\docs`
- 文档数量：103
- ADR 编号空洞：`[]`
- ADR-034 空洞保留：`True`

## 运行上下文与本次专项范围

- 实际目标目录：`D:\Tony\Documents\invest2025\project\config_manager`
- `is_global`：`false`
- `skills_mode`：`global_only`
- `git_root_real`：`D:/Tony/Documents/invest2025/project/config_manager`
- `recommended_path_base`：`D:/Tony/Documents/invest2025/project/config_manager`
- 扫描器返回的 `active_docs_root`：`C:/Users/Tony/.codex/docs`；该路径属于全局 Codex 文档资产，与普通项目作用域不一致，本次未读取或修改。
- 本次固定 `docs_root`：`D:\Tony\Documents\invest2025\project\config_manager\docs`，依据 `is_global=false` 的项目路径规则使用 `recommended_path_base/docs`。
- Python 运行上下文：独立治理扫描脚本；`D:\anaconda3\envs\base_python3.12\python.exe` 已通过无副作用 probe，Windows `nt`，Python `3.12.9`；未初始化或同步项目环境。
- 用户专项要求：把历史标识 `US-001` 重编号为 `S1-01`；从 `Sprint01.md` 提取内嵌原始需求到 `docs/01_Sprint记录/Sprint01/S1-01/S1-01_原始需求.md`；同步处理相关文档和代码标识。
- 专项清点结果：`S1-01` Issue 目录尚不存在，当前仓库内也没有其他 `S1-01` 占用；`src/` 和 `tests/` 中没有 `US-001` 或 `S1-01` 标识；`ConfigNode` 当前也没有 `keys()`、`values()`、`items()` 实现，本次重编号不据此扩大为功能实施。
- 当前工作树基线：除本次报告与请求记录外，存在用户的未跟踪文件 `.codex/task-records/2026/08/26/20260826-s1-04-solution-decision.md`，本流程不读取、不修改、不暂存。

## 全量分类结果

| 源文件 | 分类 | 作用域 | 目标载体 | 动作 | 判定依据 | 提升候选 |
|:-------|:-----|:-------|:---------|:-----|:---------|:---------|
| 00_待办列表/Sprint待办列表/Sprint01.md | 设计 | project | 05_项目设计/Sprint01.md | migrate_non_adr | 路径、文件名、标题或正文命中设计关键词；相对路径未包含 Issue 标识 | 否 |
| 00_待办列表/产品待办列表.md | 待人工分类 | manual | 00_待办列表/产品待办列表.md | manual_classification | 没有足够的类型关键词证据 | 否 |
| 01_Sprint记录/Sprint01/S1-02/S1-02_原始需求.md | 设计 | issue | 01_Sprint记录/Sprint01/S1-02/S1-02_原始需求.md | retain | 路径、文件名、标题或正文命中设计关键词；相对路径包含 Issue 标识 | 否 |
| 01_Sprint记录/Sprint01/S1-02/S1-02_处理记录.md | 设计 | issue | 01_Sprint记录/Sprint01/S1-02/S1-02_处理记录.md | retain | 路径、文件名、标题或正文命中设计关键词；相对路径包含 Issue 标识 | 否 |
| 01_Sprint记录/Sprint01/S1-02/S1-02_实施计划.md | 设计 | issue | 01_Sprint记录/Sprint01/S1-02/S1-02_实施计划.md | retain | 路径、文件名、标题或正文命中设计关键词；相对路径包含 Issue 标识 | 否 |
| 01_Sprint记录/Sprint01/S1-02/S1-02_实施记录.md | 约束 | issue | 01_Sprint记录/Sprint01/S1-02/S1-02_实施记录.md | retain | 路径、文件名、标题或正文命中约束关键词；相对路径包含 Issue 标识 | 否 |
| 01_Sprint记录/Sprint01/S1-02/S1-02_整体评审报告.md | 设计 | issue | 01_Sprint记录/Sprint01/S1-02/S1-02_整体评审报告.md | retain | 路径、文件名、标题或正文命中设计关键词；相对路径包含 Issue 标识 | 否 |
| 01_Sprint记录/Sprint01/S1-02/S1-02_方案决策.md | 概念 | project | 03_项目概念/S1-02_方案决策.md | migrate_non_adr | 路径、文件名、标题或正文命中概念关键词 | 否 |
| 01_Sprint记录/Sprint01/S1-02/S1-02_方案决策总结.md | 设计 | issue | 01_Sprint记录/Sprint01/S1-02/S1-02_方案决策总结.md | retain | 路径、文件名、标题或正文命中设计关键词；相对路径包含 Issue 标识 | 否 |
| 01_Sprint记录/Sprint01/S1-02/S1-02_方案实施总结.md | 设计 | issue | 01_Sprint记录/Sprint01/S1-02/S1-02_方案实施总结.md | retain | 路径、文件名、标题或正文命中设计关键词；相对路径包含 Issue 标识 | 否 |
| 01_Sprint记录/Sprint01/S1-02/S1-02_方案设计总结.md | 设计 | issue | 01_Sprint记录/Sprint01/S1-02/S1-02_方案设计总结.md | retain | 路径、文件名、标题或正文命中设计关键词；相对路径包含 Issue 标识 | 否 |
| 01_Sprint记录/Sprint01/S1-02/S1-02_测试报告.md | 待人工分类 | manual | 01_Sprint记录/Sprint01/S1-02/S1-02_测试报告.md | manual_classification | 没有足够的类型关键词证据 | 否 |
| 01_Sprint记录/Sprint01/S1-02/S1-02_设计.md | 设计 | issue | 01_Sprint记录/Sprint01/S1-02/S1-02_设计.md | retain | 路径、文件名、标题或正文命中设计关键词；相对路径包含 Issue 标识 | 否 |
| 01_Sprint记录/Sprint01/S1-02/S1-02_遗留事项报告.md | 设计 | issue | 01_Sprint记录/Sprint01/S1-02/S1-02_遗留事项报告.md | retain | 路径、文件名、标题或正文命中设计关键词；相对路径包含 Issue 标识 | 否 |
| 01_Sprint记录/Sprint01/S1-02/S1-02_遗留问题.md | 约束 | issue | 04_项目约束/S1-02_遗留问题.md | review_promotion | 路径、文件名、标题或正文命中约束关键词；相对路径包含 Issue 标识 | 是 |
| 01_Sprint记录/Sprint01/S1-03/S1-03_原始需求.md | 设计 | issue | 01_Sprint记录/Sprint01/S1-03/S1-03_原始需求.md | retain | 路径、文件名、标题或正文命中设计关键词；相对路径包含 Issue 标识 | 否 |
| 01_Sprint记录/Sprint01/S1-03/S1-03_处理记录.md | 概念 | project | 03_项目概念/S1-03_处理记录.md | migrate_non_adr | 路径、文件名、标题或正文命中概念关键词 | 否 |
| 01_Sprint记录/Sprint01/S1-03/S1-03_实施计划.md | 概念 | project | 03_项目概念/S1-03_实施计划.md | migrate_non_adr | 路径、文件名、标题或正文命中概念关键词 | 否 |
| 01_Sprint记录/Sprint01/S1-03/S1-03_实施记录.md | 设计 | issue | 01_Sprint记录/Sprint01/S1-03/S1-03_实施记录.md | retain | 路径、文件名、标题或正文命中设计关键词；相对路径包含 Issue 标识 | 否 |
| 01_Sprint记录/Sprint01/S1-03/S1-03_整体评审报告.md | 约束 | issue | 01_Sprint记录/Sprint01/S1-03/S1-03_整体评审报告.md | retain | 路径、文件名、标题或正文命中约束关键词；相对路径包含 Issue 标识 | 否 |
| 01_Sprint记录/Sprint01/S1-03/S1-03_方案决策.md | 概念 | project | 03_项目概念/S1-03_方案决策.md | migrate_non_adr | 路径、文件名、标题或正文命中概念关键词 | 否 |
| 01_Sprint记录/Sprint01/S1-03/S1-03_方案决策总结.md | 约束 | issue | 01_Sprint记录/Sprint01/S1-03/S1-03_方案决策总结.md | retain | 路径、文件名、标题或正文命中约束关键词；相对路径包含 Issue 标识 | 否 |
| 01_Sprint记录/Sprint01/S1-03/S1-03_方案实施总结.md | 设计 | issue | 01_Sprint记录/Sprint01/S1-03/S1-03_方案实施总结.md | retain | 路径、文件名、标题或正文命中设计关键词；相对路径包含 Issue 标识 | 否 |
| 01_Sprint记录/Sprint01/S1-03/S1-03_方案设计总结.md | 设计 | issue | 01_Sprint记录/Sprint01/S1-03/S1-03_方案设计总结.md | retain | 路径、文件名、标题或正文命中设计关键词；相对路径包含 Issue 标识 | 否 |
| 01_Sprint记录/Sprint01/S1-03/S1-03_测试报告.md | 设计 | issue | 01_Sprint记录/Sprint01/S1-03/S1-03_测试报告.md | retain | 路径、文件名、标题或正文命中设计关键词；相对路径包含 Issue 标识 | 否 |
| 01_Sprint记录/Sprint01/S1-03/S1-03_系统诊断.md | 约束 | issue | 01_Sprint记录/Sprint01/S1-03/S1-03_系统诊断.md | retain | 路径、文件名、标题或正文命中约束关键词；相对路径包含 Issue 标识 | 否 |
| 01_Sprint记录/Sprint01/S1-03/S1-03_设计.md | 概念 | project | 03_项目概念/S1-03_设计.md | migrate_non_adr | 路径、文件名、标题或正文命中概念关键词 | 否 |
| 01_Sprint记录/Sprint01/S1-03/S1-03_遗留事项报告.md | 约束 | issue | 01_Sprint记录/Sprint01/S1-03/S1-03_遗留事项报告.md | retain | 路径、文件名、标题或正文命中约束关键词；相对路径包含 Issue 标识 | 否 |
| 01_Sprint记录/Sprint01/S1-03/S1-03_遗留问题.md | 设计 | issue | 01_Sprint记录/Sprint01/S1-03/S1-03_遗留问题.md | retain | 路径、文件名、标题或正文命中设计关键词；相对路径包含 Issue 标识 | 否 |
| 01_Sprint记录/Sprint01/S1-03/S1-03_需求澄清.md | 约束 | issue | 01_Sprint记录/Sprint01/S1-03/S1-03_需求澄清.md | retain | 路径、文件名、标题或正文命中约束关键词；相对路径包含 Issue 标识 | 否 |
| 01_Sprint记录/Sprint01/S1-03/技术验证/validate_pyyaml_20260818/验证报告.md | 概念 | project | 03_项目概念/验证报告.md | migrate_non_adr | 路径、文件名、标题或正文命中概念关键词 | 否 |
| 01_Sprint记录/Sprint01/S1-04/S1-04_原始需求.md | 设计 | issue | 01_Sprint记录/Sprint01/S1-04/S1-04_原始需求.md | retain | 路径、文件名、标题或正文命中设计关键词；相对路径包含 Issue 标识 | 否 |
| 01_Sprint记录/Sprint01/设计文档/ConfigNode字典方法_设计.md | 设计 | project | 05_项目设计/ConfigNode字典方法_设计.md | migrate_non_adr | 路径、文件名、标题或正文命中设计关键词；相对路径未包含 Issue 标识 | 否 |
| 01_requirements/cross_platform_path_requirements.md | 概念 | project | 03_项目概念/cross_platform_path_requirements.md | migrate_non_adr | 路径、文件名、标题或正文命中概念关键词 | 否 |
| 01_requirements/interpreter_shutdown_safety_requirements.md | 约束 | project | 04_项目约束/interpreter_shutdown_safety_requirements.md | migrate_non_adr | 路径、文件名、标题或正文命中约束关键词；相对路径未包含 Issue 标识 | 否 |
| 01_requirements/minimal_logger_requirements.md | 约束 | project | 04_项目约束/minimal_logger_requirements.md | migrate_non_adr | 路径、文件名、标题或正文命中约束关键词；相对路径未包含 Issue 标识 | 否 |
| 01_requirements/multiprocess_support_requirements.md | 待人工分类 | manual | 01_requirements/multiprocess_support_requirements.md | manual_classification | 没有足够的类型关键词证据 | 否 |
| 01_requirements/path_configuration_requirements.md | 概念 | project | 03_项目概念/path_configuration_requirements.md | migrate_non_adr | 路径、文件名、标题或正文命中概念关键词 | 否 |
| 01_requirements/test_mode_requirements.md | 待人工分类 | manual | 01_requirements/test_mode_requirements.md | manual_classification | 没有足够的类型关键词证据 | 否 |
| 02_architecture/architecture_design.md | 概念 | project | 03_项目概念/architecture_design.md | migrate_non_adr | 路径、文件名、标题或正文命中概念关键词 | 否 |
| 02_architecture/cross_platform_architecture_design.md | 设计 | project | 05_项目设计/cross_platform_architecture_design.md | migrate_non_adr | 路径、文件名、标题或正文命中设计关键词；相对路径未包含 Issue 标识 | 否 |
| 02_架构决策记录/ADR-001_ConfigManager持久化职责边界.md | ADR | project | 02_架构决策记录/ADR-001_ConfigManager持久化职责边界.md | delegate_to_architecture_design | 路径位于 02_架构决策记录 或文件名以 ADR-数字 开头 | 否 |
| 02_架构决策记录/ADR-001_test_mode数据库切换职责边界.md | ADR | project | 02_架构决策记录/ADR-001_test_mode数据库切换职责边界.md | delegate_to_architecture_design | 路径位于 02_架构决策记录 或文件名以 ADR-数字 开头 | 否 |
| 02_架构决策记录/ADR-002_YAML候选验证与原子提交顺序.md | ADR | project | 02_架构决策记录/ADR-002_YAML候选验证与原子提交顺序.md | delegate_to_architecture_design | 路径位于 02_架构决策记录 或文件名以 ADR-数字 开头 | 否 |
| 02_架构决策记录/ADR-002_test_mode数据库地址数据流.md | ADR | project | 02_架构决策记录/ADR-002_test_mode数据库地址数据流.md | delegate_to_architecture_design | 路径位于 02_架构决策记录 或文件名以 ADR-数字 开头 | 否 |
| 03_design/autosave_thread_safety_summary.md | 设计 | project | 05_项目设计/autosave_thread_safety_summary.md | migrate_non_adr | 路径、文件名、标题或正文命中设计关键词；相对路径未包含 Issue 标识 | 否 |
| 03_design/config_file_path_feature_design.md | 设计 | project | 05_项目设计/config_file_path_feature_design.md | migrate_non_adr | 路径、文件名、标题或正文命中设计关键词；相对路径未包含 Issue 标识 | 否 |
| 03_design/debug_mode_dynamic_fix_report.md | 概念 | project | 03_项目概念/debug_mode_dynamic_fix_report.md | migrate_non_adr | 路径、文件名、标题或正文命中概念关键词 | 否 |
| 03_design/interpreter_shutdown_safety_design.md | 设计 | project | 05_项目设计/interpreter_shutdown_safety_design.md | migrate_non_adr | 路径、文件名、标题或正文命中设计关键词；相对路径未包含 Issue 标识 | 否 |
| 03_design/minimal_logger_design.md | 设计 | project | 05_项目设计/minimal_logger_design.md | migrate_non_adr | 路径、文件名、标题或正文命中设计关键词；相对路径未包含 Issue 标识 | 否 |
| 03_design/minimal_logger_detailed_design.md | 概念 | project | 03_项目概念/minimal_logger_detailed_design.md | migrate_non_adr | 路径、文件名、标题或正文命中概念关键词 | 否 |
| 03_design/multiprocess_support_design.md | 设计 | project | 05_项目设计/multiprocess_support_design.md | migrate_non_adr | 路径、文件名、标题或正文命中设计关键词；相对路径未包含 Issue 标识 | 否 |
| 03_design/path_configuration_design.md | 概念 | project | 03_项目概念/path_configuration_design.md | migrate_non_adr | 路径、文件名、标题或正文命中概念关键词 | 否 |
| 03_design/path_field_recognition_v2.1.md | 设计 | project | 05_项目设计/path_field_recognition_v2.1.md | migrate_non_adr | 路径、文件名、标题或正文命中设计关键词；相对路径未包含 Issue 标识 | 否 |
| 03_design/raw_yaml_format_support_design.md | 设计 | project | 05_项目设计/raw_yaml_format_support_design.md | migrate_non_adr | 路径、文件名、标题或正文命中设计关键词；相对路径未包含 Issue 标识 | 否 |
| 03_design/test_mode_path_replacement_design.md | 概念 | project | 03_项目概念/test_mode_path_replacement_design.md | migrate_non_adr | 路径、文件名、标题或正文命中概念关键词 | 否 |
| 03_design/yaml_comments_preservation_design.md | 设计 | project | 05_项目设计/yaml_comments_preservation_design.md | migrate_non_adr | 路径、文件名、标题或正文命中设计关键词；相对路径未包含 Issue 标识 | 否 |
| 99_归档/01_需求文档/需求规格说明书.md | 约束 | project | 04_项目约束/需求规格说明书.md | migrate_non_adr | 路径、文件名、标题或正文命中约束关键词；相对路径未包含 Issue 标识 | 否 |
| 99_归档/02_产品待办列表/产品待办列表.md | 待人工分类 | manual | 99_归档/02_产品待办列表/产品待办列表.md | manual_classification | 没有足够的类型关键词证据 | 否 |
| 99_归档/02_架构设计/架构设计.md | 概念 | project | 03_项目概念/架构设计.md | migrate_non_adr | 路径、文件名、标题或正文命中概念关键词 | 否 |
| 99_归档/03_概要设计文档/概要设计.md | 概念 | project | 03_项目概念/概要设计.md | migrate_non_adr | 路径、文件名、标题或正文命中概念关键词 | 否 |
| 99_归档/04_详细设计/architecture_design.md | 设计 | project | 05_项目设计/architecture_design.md | migrate_non_adr | 路径、文件名、标题或正文命中设计关键词；相对路径未包含 Issue 标识 | 否 |
| 99_归档/04_详细设计/autosave_thread_safety_summary.md | 设计 | project | 05_项目设计/autosave_thread_safety_summary.md | migrate_non_adr | 路径、文件名、标题或正文命中设计关键词；相对路径未包含 Issue 标识 | 否 |
| 99_归档/04_详细设计/config_file_path_feature_design.md | 设计 | project | 05_项目设计/config_file_path_feature_design.md | migrate_non_adr | 路径、文件名、标题或正文命中设计关键词；相对路径未包含 Issue 标识 | 否 |
| 99_归档/04_详细设计/confignode_math_operations_design.md | 设计 | project | 05_项目设计/confignode_math_operations_design.md | migrate_non_adr | 路径、文件名、标题或正文命中设计关键词；相对路径未包含 Issue 标识 | 否 |
| 99_归档/04_详细设计/confignode_math_operations_requirements.md | 设计 | project | 05_项目设计/confignode_math_operations_requirements.md | migrate_non_adr | 路径、文件名、标题或正文命中设计关键词；相对路径未包含 Issue 标识 | 否 |
| 99_归档/04_详细设计/cross_platform_architecture_design.md | 设计 | project | 05_项目设计/cross_platform_architecture_design.md | migrate_non_adr | 路径、文件名、标题或正文命中设计关键词；相对路径未包含 Issue 标识 | 否 |
| 99_归档/04_详细设计/cross_platform_path_requirements.md | 概念 | project | 03_项目概念/cross_platform_path_requirements.md | migrate_non_adr | 路径、文件名、标题或正文命中概念关键词 | 否 |
| 99_归档/04_详细设计/debug_mode_dynamic_fix_report.md | 概念 | project | 03_项目概念/debug_mode_dynamic_fix_report.md | migrate_non_adr | 路径、文件名、标题或正文命中概念关键词 | 否 |
| 99_归档/04_详细设计/interpreter_shutdown_safety_design.md | 设计 | project | 05_项目设计/interpreter_shutdown_safety_design.md | migrate_non_adr | 路径、文件名、标题或正文命中设计关键词；相对路径未包含 Issue 标识 | 否 |
| 99_归档/04_详细设计/interpreter_shutdown_safety_requirements.md | 约束 | project | 04_项目约束/interpreter_shutdown_safety_requirements.md | migrate_non_adr | 路径、文件名、标题或正文命中约束关键词；相对路径未包含 Issue 标识 | 否 |
| 99_归档/04_详细设计/multiprocess_support_design.md | 设计 | project | 05_项目设计/multiprocess_support_design.md | migrate_non_adr | 路径、文件名、标题或正文命中设计关键词；相对路径未包含 Issue 标识 | 否 |
| 99_归档/04_详细设计/multiprocess_support_requirements.md | 设计 | project | 05_项目设计/multiprocess_support_requirements.md | migrate_non_adr | 路径、文件名、标题或正文命中设计关键词；相对路径未包含 Issue 标识 | 否 |
| 99_归档/04_详细设计/path_configuration_design.md | 设计 | project | 05_项目设计/path_configuration_design.md | migrate_non_adr | 路径、文件名、标题或正文命中设计关键词；相对路径未包含 Issue 标识 | 否 |
| 99_归档/04_详细设计/path_configuration_requirements.md | 概念 | project | 03_项目概念/path_configuration_requirements.md | migrate_non_adr | 路径、文件名、标题或正文命中概念关键词 | 否 |
| 99_归档/04_详细设计/path_field_recognition_v2.1.md | 设计 | project | 05_项目设计/path_field_recognition_v2.1.md | migrate_non_adr | 路径、文件名、标题或正文命中设计关键词；相对路径未包含 Issue 标识 | 否 |
| 99_归档/04_详细设计/raw_yaml_format_support_design.md | 设计 | project | 05_项目设计/raw_yaml_format_support_design.md | migrate_non_adr | 路径、文件名、标题或正文命中设计关键词；相对路径未包含 Issue 标识 | 否 |
| 99_归档/04_详细设计/test_mode_path_replacement_design.md | 设计 | project | 05_项目设计/test_mode_path_replacement_design.md | migrate_non_adr | 路径、文件名、标题或正文命中设计关键词；相对路径未包含 Issue 标识 | 否 |
| 99_归档/04_详细设计/test_mode_requirements.md | 概念 | project | 03_项目概念/test_mode_requirements.md | migrate_non_adr | 路径、文件名、标题或正文命中概念关键词 | 否 |
| 99_归档/04_详细设计/tsb_tensorboard_path_unification.md | 概念 | project | 03_项目概念/tsb_tensorboard_path_unification.md | migrate_non_adr | 路径、文件名、标题或正文命中概念关键词 | 否 |
| 99_归档/04_详细设计/windows_compatibility_design.md | 设计 | project | 05_项目设计/windows_compatibility_design.md | migrate_non_adr | 路径、文件名、标题或正文命中设计关键词；相对路径未包含 Issue 标识 | 否 |
| 99_归档/04_详细设计/yaml_comments_preservation_design.md | 设计 | project | 05_项目设计/yaml_comments_preservation_design.md | migrate_non_adr | 路径、文件名、标题或正文命中设计关键词；相对路径未包含 Issue 标识 | 否 |
| 99_归档/04_详细设计/yaml_type_validation_design.md | 设计 | project | 05_项目设计/yaml_type_validation_design.md | migrate_non_adr | 路径、文件名、标题或正文命中设计关键词；相对路径未包含 Issue 标识 | 否 |
| 99_归档/04_详细设计/yaml_type_validation_requirements.md | 设计 | project | 05_项目设计/yaml_type_validation_requirements.md | migrate_non_adr | 路径、文件名、标题或正文命中设计关键词；相对路径未包含 Issue 标识 | 否 |
| 99_归档/05_测试方案/YAML注释保留测试方案.md | 设计 | project | 05_项目设计/YAML注释保留测试方案.md | migrate_non_adr | 路径、文件名、标题或正文命中设计关键词；相对路径未包含 Issue 标识 | 否 |
| 99_归档/05_测试方案/tsb_tensorboard_path_test_plan.md | 设计 | project | 05_项目设计/tsb_tensorboard_path_test_plan.md | migrate_non_adr | 路径、文件名、标题或正文命中设计关键词；相对路径未包含 Issue 标识 | 否 |
| 99_归档/05_测试方案/windows_compatibility_test_plan.md | 设计 | project | 05_项目设计/windows_compatibility_test_plan.md | migrate_non_adr | 路径、文件名、标题或正文命中设计关键词；相对路径未包含 Issue 标识 | 否 |
| 99_归档/05_测试方案/性能测试方案.md | 设计 | project | 05_项目设计/性能测试方案.md | migrate_non_adr | 路径、文件名、标题或正文命中设计关键词；相对路径未包含 Issue 标识 | 否 |
| 99_归档/06_任务清单/20250628缩减功能.md | 概念 | project | 03_项目概念/20250628缩减功能.md | migrate_non_adr | 路径、文件名、标题或正文命中概念关键词 | 否 |
| 99_归档/06_任务清单/20250629任务清单.md | 概念 | project | 03_项目概念/20250629任务清单.md | migrate_non_adr | 路径、文件名、标题或正文命中概念关键词 | 否 |
| 99_归档/06_任务清单/任务清单20250705.md | 设计 | project | 05_项目设计/任务清单20250705.md | migrate_non_adr | 路径、文件名、标题或正文命中设计关键词；相对路径未包含 Issue 标识 | 否 |
| 99_归档/06_功能规范/tsb_logs_dir_unification/design.md | 设计 | project | 05_项目设计/design.md | migrate_non_adr | 路径、文件名、标题或正文命中设计关键词；相对路径未包含 Issue 标识 | 否 |
| 99_归档/06_功能规范/tsb_logs_dir_unification/requirements.md | 约束 | project | 04_项目约束/requirements.md | migrate_non_adr | 路径、文件名、标题或正文命中约束关键词；相对路径未包含 Issue 标识 | 否 |
| 99_归档/06_功能规范/tsb_logs_dir_unification/tasks.md | 概念 | project | 03_项目概念/tasks.md | migrate_non_adr | 路径、文件名、标题或正文命中概念关键词 | 否 |
| 99_归档/features/tsb_logs_path_update.md | 概念 | project | 03_项目概念/tsb_logs_path_update.md | migrate_non_adr | 路径、文件名、标题或正文命中概念关键词 | 否 |
| 99_归档/specs/tsb_logs_path_update/design.md | 概念 | project | 03_项目概念/design.md | migrate_non_adr | 路径、文件名、标题或正文命中概念关键词 | 否 |
| 99_归档/specs/tsb_logs_path_update/requirements.md | 概念 | project | 03_项目概念/requirements.md | migrate_non_adr | 路径、文件名、标题或正文命中概念关键词 | 否 |
| 99_归档/specs/tsb_logs_path_update/tasks.md | 概念 | project | 03_项目概念/tasks.md | migrate_non_adr | 路径、文件名、标题或正文命中概念关键词 | 否 |
| 99_归档/任务清单/20250705/任务清单20250705.md | 设计 | project | 05_项目设计/任务清单20250705.md | migrate_non_adr | 路径、文件名、标题或正文命中设计关键词；相对路径未包含 Issue 标识 | 否 |
| 99_归档/规范/AI主导的个人量化交易系统开发规范.md | 概念 | project | 03_项目概念/AI主导的个人量化交易系统开发规范.md | migrate_non_adr | 路径、文件名、标题或正文命中概念关键词 | 否 |
| 99_归档/规范/敏捷开发阶段特点.md | 概念 | project | 03_项目概念/敏捷开发阶段特点.md | migrate_non_adr | 路径、文件名、标题或正文命中概念关键词 | 否 |
| 规范/AI主导的个人量化交易系统开发规范.md | 概念 | project | 03_项目概念/AI主导的个人量化交易系统开发规范.md | migrate_non_adr | 路径、文件名、标题或正文命中概念关键词 | 否 |
| 规范/敏捷开发阶段特点.md | 概念 | project | 03_项目概念/敏捷开发阶段特点.md | migrate_non_adr | 路径、文件名、标题或正文命中概念关键词 | 否 |

## 引用校验

- 检查链接：0
- 有效链接：0
- 缺失链接：0
- 越界链接：0

## 扫描异常

无

## 待澄清问题

1. `00_待办列表/产品待办列表.md`：无法依据现有证据确定文档类型和目标载体
2. `01_Sprint记录/Sprint01/S1-02/S1-02_测试报告.md`：无法依据现有证据确定文档类型和目标载体
3. `01_Sprint记录/Sprint01/S1-02/S1-02_遗留问题.md`：Issue 级文档出现项目级适用信号，是否提升为项目级文档
4. `01_requirements/multiprocess_support_requirements.md`：无法依据现有证据确定文档类型和目标载体
5. `01_requirements/test_mode_requirements.md`：无法依据现有证据确定文档类型和目标载体
6. `99_归档/02_产品待办列表/产品待办列表.md`：无法依据现有证据确定文档类型和目标载体
7. `99_归档/规范/AI主导的个人量化交易系统开发规范.md`：迁移目标存在冲突：03_项目概念/AI主导的个人量化交易系统开发规范.md
8. `规范/AI主导的个人量化交易系统开发规范.md`：迁移目标存在冲突：03_项目概念/AI主导的个人量化交易系统开发规范.md
9. `01_requirements/cross_platform_path_requirements.md`：迁移目标存在冲突：03_项目概念/cross_platform_path_requirements.md
10. `99_归档/04_详细设计/cross_platform_path_requirements.md`：迁移目标存在冲突：03_项目概念/cross_platform_path_requirements.md
11. `03_design/debug_mode_dynamic_fix_report.md`：迁移目标存在冲突：03_项目概念/debug_mode_dynamic_fix_report.md
12. `99_归档/04_详细设计/debug_mode_dynamic_fix_report.md`：迁移目标存在冲突：03_项目概念/debug_mode_dynamic_fix_report.md
13. `01_requirements/path_configuration_requirements.md`：迁移目标存在冲突：03_项目概念/path_configuration_requirements.md
14. `99_归档/04_详细设计/path_configuration_requirements.md`：迁移目标存在冲突：03_项目概念/path_configuration_requirements.md
15. `99_归档/06_功能规范/tsb_logs_dir_unification/tasks.md`：迁移目标存在冲突：03_项目概念/tasks.md
16. `99_归档/specs/tsb_logs_path_update/tasks.md`：迁移目标存在冲突：03_项目概念/tasks.md
17. `99_归档/规范/敏捷开发阶段特点.md`：迁移目标存在冲突：03_项目概念/敏捷开发阶段特点.md
18. `规范/敏捷开发阶段特点.md`：迁移目标存在冲突：03_项目概念/敏捷开发阶段特点.md
19. `01_requirements/interpreter_shutdown_safety_requirements.md`：迁移目标存在冲突：04_项目约束/interpreter_shutdown_safety_requirements.md
20. `99_归档/04_详细设计/interpreter_shutdown_safety_requirements.md`：迁移目标存在冲突：04_项目约束/interpreter_shutdown_safety_requirements.md
21. `03_design/autosave_thread_safety_summary.md`：迁移目标存在冲突：05_项目设计/autosave_thread_safety_summary.md
22. `99_归档/04_详细设计/autosave_thread_safety_summary.md`：迁移目标存在冲突：05_项目设计/autosave_thread_safety_summary.md
23. `03_design/config_file_path_feature_design.md`：迁移目标存在冲突：05_项目设计/config_file_path_feature_design.md
24. `99_归档/04_详细设计/config_file_path_feature_design.md`：迁移目标存在冲突：05_项目设计/config_file_path_feature_design.md
25. `02_architecture/cross_platform_architecture_design.md`：迁移目标存在冲突：05_项目设计/cross_platform_architecture_design.md
26. `99_归档/04_详细设计/cross_platform_architecture_design.md`：迁移目标存在冲突：05_项目设计/cross_platform_architecture_design.md
27. `03_design/interpreter_shutdown_safety_design.md`：迁移目标存在冲突：05_项目设计/interpreter_shutdown_safety_design.md
28. `99_归档/04_详细设计/interpreter_shutdown_safety_design.md`：迁移目标存在冲突：05_项目设计/interpreter_shutdown_safety_design.md
29. `03_design/multiprocess_support_design.md`：迁移目标存在冲突：05_项目设计/multiprocess_support_design.md
30. `99_归档/04_详细设计/multiprocess_support_design.md`：迁移目标存在冲突：05_项目设计/multiprocess_support_design.md
31. `03_design/path_field_recognition_v2.1.md`：迁移目标存在冲突：05_项目设计/path_field_recognition_v2.1.md
32. `99_归档/04_详细设计/path_field_recognition_v2.1.md`：迁移目标存在冲突：05_项目设计/path_field_recognition_v2.1.md
33. `03_design/raw_yaml_format_support_design.md`：迁移目标存在冲突：05_项目设计/raw_yaml_format_support_design.md
34. `99_归档/04_详细设计/raw_yaml_format_support_design.md`：迁移目标存在冲突：05_项目设计/raw_yaml_format_support_design.md
35. `03_design/yaml_comments_preservation_design.md`：迁移目标存在冲突：05_项目设计/yaml_comments_preservation_design.md
36. `99_归档/04_详细设计/yaml_comments_preservation_design.md`：迁移目标存在冲突：05_项目设计/yaml_comments_preservation_design.md
37. `99_归档/06_任务清单/任务清单20250705.md`：迁移目标存在冲突：05_项目设计/任务清单20250705.md
38. `99_归档/任务清单/20250705/任务清单20250705.md`：迁移目标存在冲突：05_项目设计/任务清单20250705.md

## 执行门禁

用户确认后才可迁移非 ADR 内容；正确归属文档保持原位。

ADR 仅委托 architecture-design，不由本 Skill 直接写入、移动、归档或重编号。

本报告是一次性工作产物，不创建长期项目分类索引。

## 澄清帧 PDG-CLAR-001-v1

- `grilling-llm` 迭代次数：1
- 确认对象：`00_待办列表/产品待办列表.md` 的分类与目标载体。
- 直接证据：文件标题为“产品待办列表”，正文声明其记录全量需求池，并包含运营状态表；它不是项目概念、约束、设计或单一 Issue 原始需求文件。
- 候选结论：判定为产品待办运营文档，原位保留在 `00_待办列表/产品待办列表.md`；本确认不决定后续是否保留其中重复的 US-001 详情区块。
- 用户问题：是否确认把该文件作为产品待办运营文档原位保留？
- 选项 1：确认当前分类与载体（推荐）。
- 选项 2：修改分类或目标载体；请给出自定义口径。
- 用户回复：`1`
- 结果：`confirmed`；分类为产品待办运营文档，目标载体保持 `00_待办列表/产品待办列表.md`。

## S1-01 治理范围

- 把 `US-001` 重编号为 `S1-01`。
- 只治理 S1-01 的直接内容、路径和标识引用；其他 Issue 的文档分类与迁移不属于本次动作范围。
- `PDG-CLAR-001-v1` 已确认 `00_待办列表/产品待办列表.md` 是运营文档并原位保留。
- 原始需求真源是 `00_待办列表/Sprint待办列表/Sprint01.md` 的“用户故事详情”整段；迁移时原样写入 `01_Sprint记录/Sprint01/S1-01/S1-01_原始需求.md`，只更新 Issue ID。
- `Sprint01.md` 保留运营跟踪表，更新 Issue ID，并移除已经迁入 Issue 目录的详情区块。
- `产品待办列表.md` 原位更新 Issue ID。
- `ConfigNode字典方法_设计.md` 明确对应本 Issue；目标载体等待单项确认。
- 其他项目文档内的 `US-001` 标识按用户要求更新为 `S1-01`，不改变这些文档的目录、阶段结论或其他内容。
- `src/` 和 `tests/` 没有待替换的 Issue 标识，本次不修改生产代码或测试代码。

## 澄清帧 PDG-S101-PATH-001-v1

- `grilling-llm` 迭代次数：1
- 确认对象：`01_Sprint记录/Sprint01/设计文档/ConfigNode字典方法_设计.md` 的 S1-01 目标载体。
- 直接证据：该文档明确对应当前 Issue；当前仓库没有指向其文件路径的 Markdown 引用；`01_Sprint记录/Sprint01/S1-01/S1-01_设计.md` 不存在。
- 候选 1：迁移并重命名为 `01_Sprint记录/Sprint01/S1-01/S1-01_设计.md`，让原始需求与设计共同归属 S1-01 Issue 目录。
- 候选 2：保留在 `01_Sprint记录/Sprint01/设计文档/ConfigNode字典方法_设计.md`，只更新正文 Issue ID。
- 推荐：候选 1；它与“只治理 S1-01”和“迁移对应内容到 Issue 目录”的目标一致，且当前仓库没有路径引用需要修复。
- 用户问题：S1-01 设计文档采用哪个目标载体？
- 用户回复：`1`
- 结果：`confirmed`；目标载体为 `01_Sprint记录/Sprint01/S1-01/S1-01_设计.md`。

## 汇总确认帧 PDG-S101-PLAN-v1

- `grilling-llm` 迭代次数：1
- 基线：`sprint01@71cd4904a117b62181023bd5aa4142987a4cd0d9`
- 作用域：只治理 `US-001 → S1-01` 的直接内容、路径和标识引用。
- 原始需求来源：`00_待办列表/Sprint待办列表/Sprint01.md` 的完整“用户故事详情”区块，已由用户逐字确认。
- 当前引用：`docs/` 中 21 处 `US-001`，分布在 7 个现有文档；`docs/` 中没有 `S1-01`。
- 代码边界：`src/` 与 `tests/` 没有 Issue ID 引用，不修改生产代码或测试代码。
- ADR：无新增、修订、替代、归档、迁移或委托动作。
- Markdown 引用：首次扫描检查 0 个相对链接，无缺失或越界引用；设计文件路径在当前仓库中没有引用。

### 分类与动作

| 源或内容 | 作用域与载体 | 动作 | 目标或结果 |
|:---|:---|:---|:---|
| `00_待办列表/Sprint待办列表/Sprint01.md` | Sprint 运营文档 | `retain` + 提取原始需求 | 跟踪行改为 `S1-01`；移除已迁出的“用户故事详情”区块；状态、点数、优先级和统计不变 |
| `Sprint01.md` 的完整“用户故事详情”区块 | S1-01 原始需求 | `migrate_non_adr` | 新建 `01_Sprint记录/Sprint01/S1-01/S1-01_原始需求.md`；增加文件一级标题，原始区块只更新 Issue ID |
| `00_待办列表/产品待办列表.md` | 产品待办运营文档 | `retain` | 表格与详情标题中的 Issue ID 更新为 `S1-01`；其他内容不变 |
| `01_Sprint记录/Sprint01/设计文档/ConfigNode字典方法_设计.md` | S1-01 Issue 级设计 | `migrate_non_adr` | 移动并重命名为 `01_Sprint记录/Sprint01/S1-01/S1-01_设计.md`；正文 Issue ID 更新为 `S1-01` |
| S1-02/S1-03 文档中对旧 Issue ID 的 16 处直接引用 | 既有历史阶段文档 | `retain` | 只把 Issue ID 更新为 `S1-01`，目录、阶段结论和其他正文不变 |

### 执行与验证

1. 复核源、目标、Git 基线和任务外工作树状态。
2. 通过精确补丁创建原始需求文件、移动设计文件、更新 21 处文档标识并删除 Sprint 内嵌详情。
3. 确认 `docs/`、`src/`、`tests/` 不再出现旧 Issue ID，S1-01 目标文件存在且原始需求业务内容完整。
4. 对同一 `docs_root` 重新运行只读扫描器，并把 S1-01 复验结果追加到本报告。
5. 运行 Sprint 待办结构校验、`git diff --check`、精确路径状态与 `$no-negative-echo` 最终表面检查。
6. 调用 `$auto-commit`，只提交本任务项目文档和两份任务记录；所有现有 S1-04 未跟踪文件保持任务外。

### 风险与回退

- 移动设计文件可能影响仓库外部的未登记路径引用；仓库内扫描未发现引用。提交前可按 source→target 映射恢复路径，提交后使用普通 Git 反向提交恢复。
- 历史阶段文档只替换 Issue ID；逐文件差异检查保证不改变原有状态、结论、提交哈希或测试证据。
- 当前存在任务外 S1-04 未跟踪文件；精确 pathspec 和提交后读回用于防止纳入本任务。

### 用户问题

是否确认按 `PDG-S101-PLAN-v1` 执行上述完整迁移、替换、复扫、验证和限定提交？

1. 确认完整计划并执行（推荐）。
2. 修改约束；请指出需要调整的具体文件或动作。

- 用户回复：`1`
- 结果：`confirmed`；完整计划获准执行。

## 复扫与验证结果

- 复扫根目录：`D:\Tony\Documents\invest2025\project\config_manager\docs`
- 复扫文档数量：106。
- 数量变化：首次扫描 103；本任务新增 S1-01 原始需求 1 份；并发出现的任务外 S1-04 Markdown 2 份保持不动。
- `01_Sprint记录/Sprint01/S1-01/S1-01_设计.md`：`design / issue / retain`。
- `01_Sprint记录/Sprint01/S1-01/S1-01_原始需求.md`：扫描器因没有“原始需求”类别返回 `manual_classification`；用户已明确确认该正文就是原始需求，人工分类结果为 `issue original requirement / retain`，目标载体已确认，无未决歧义。
- 迁移结果：2/2；原始需求区块已迁入 S1-01 原始需求文件，设计文件已迁入并重命名为 S1-01 设计文件。
- Issue ID 复验：实施前 `docs/` 有 21 处旧 ID；实施后 `docs/`、`src/`、`tests/` 零匹配。
- Markdown 引用复验：检查 0，有效 0，缺失 0，越界 0。
- ADR 委托：0；本次没有 ADR 生命周期动作。
- Sprint 运营元数据：校验 Issue 4、警告 0、变更路径 0。
- 差异质量：`git diff --check` 退出码 0；逐文件审查确认 S1-02/S1-03 文档只替换 Issue ID。
- 任务外边界：当前 S1-04 未跟踪文件未修改，不属于本次报告或提交路径。
- `no-negative-echo`：正式报告和 8 个项目文档对被替代编号的精确匹配为 0；设计文档第 84、241 行的 Unicode `REVIEW` 字符在 HEAD 旧文件中已存在，人工复核通过。

```text
=== 项目文档治理完成 ===
作用域：project / S1-01
扫描根目录：D:\Tony\Documents\invest2025\project\config_manager\docs
报告：.codex/task-records/2026/08/26/2026-08-26-us001-to-s1-01-governance-scan.md
分类条目：106
迁移：2/2
ADR 委托：0
引用复验：0 / 0 / 0
未决阻塞：0
```
