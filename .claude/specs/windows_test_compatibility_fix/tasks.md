# Windows测试兼容性修复任务清单

## 主要任务

### 1. 修复YAML编码问题（REQ-003）
- [ ] 1.1 修改test_yaml_comments_preservation.py中的临时文件创建
  - [ ] 1.1.1 为所有NamedTemporaryFile添加encoding='utf-8'参数
  - [ ] 1.1.2 测试4个失败的测试函数是否通过
- [ ] 1.2 验证YAML注释保留功能正常工作
  - [ ] 1.2.1 运行test_yaml_comments_preservation测试
  - [ ] 1.2.2 确认注释被正确保留

### 2. 修复路径格式验证问题（REQ-001, REQ-004）
- [ ] 2.1 修复test_tc0006_singleton_path_resolution.py的路径验证
  - [ ] 2.1.1 替换硬编码的'/tmp/tests/'为平台无关的验证
  - [ ] 2.1.2 使用tempfile.gettempdir()获取实际临时目录
- [ ] 2.2 验证缓存键格式测试通过
  - [ ] 2.2.1 运行test_tc0006_005_cache_key_format_validation测试
  - [ ] 2.2.2 确认Windows路径格式被正确处理

### 3. 修复路径比较一致性问题（REQ-005）
- [ ] 3.1 修复test_tsb_path_integration.py的路径比较
  - [ ] 3.1.1 在startswith比较前统一路径分隔符
  - [ ] 3.1.2 使用PathResolver.normalize_path规范化路径
- [ ] 3.2 验证路径比较功能
  - [ ] 3.2.1 运行test_complete_path_generation_workflow测试
  - [ ] 3.2.2 确认路径比较正确

### 4. 修复相对路径转换问题（REQ-002）
- [ ] 4.1 增强PathResolver的路径处理
  - [ ] 4.1.1 在generate_tsb_logs_path中添加相对路径检查
  - [ ] 4.1.2 使用os.path.abspath转换相对路径
- [ ] 4.2 验证路径转换功能
  - [ ] 4.2.1 运行test_relative_vs_absolute_paths测试
  - [ ] 4.2.2 确认所有相对路径被正确转换

### 5. 清理和优化
- [ ] 5.1 清理临时文件处理
  - [ ] 5.1.1 确保所有临时文件在测试后被删除
  - [ ] 5.1.2 修复PermissionError相关问题
- [ ] 5.2 代码质量检查
  - [ ] 5.2.1 运行ruff检查并修复问题
  - [ ] 5.2.2 确保代码符合项目规范

### 6. 全面测试验证
- [ ] 6.1 Windows平台测试
  - [ ] 6.1.1 运行完整测试套件
  - [ ] 6.1.2 确认所有测试通过（除skip外）
- [ ] 6.2 跨平台验证
  - [ ] 6.2.1 验证修改不影响Linux/macOS测试
  - [ ] 6.2.2 记录测试结果

## 任务依赖关系

```
1.1 → 1.2
2.1 → 2.2
3.1 → 3.2
1.2, 2.2, 3.2, 4.2 → 5.1
5.1 → 5.2
5.2 → 6.1
6.1 → 6.2
```

## 预计时间

- 任务1：20分钟
- 任务2：15分钟
- 任务3：15分钟
- 任务4：10分钟
- 任务5：20分钟
- **总计**：约80分钟

## 成功标准

每个任务完成后，相关的测试必须通过。最终所有7个失败的测试都必须通过。