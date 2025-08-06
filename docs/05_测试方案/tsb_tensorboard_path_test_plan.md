# TSB日志和TensorBoard路径统一化测试方案

## 测试目标

验证tsb_logs_dir和tensorboard_dir路径统一化功能的正确性、性能和稳定性。

## 测试范围

### 功能测试

#### 1. 路径格式测试
- **测试点**：验证tsb_logs_dir生成的路径格式
- **期望结果**：`{work_dir}/tsb_logs/{yyyy}/{ww}/{mmdd}/{HHMMSS}`
- **测试用例**：
  ```python
  def test_tsb_logs_dir_format():
      config = get_config_manager(test_mode=True)
      config.set('work_dir', '/tmp/test')
      
      # 验证路径格式
      tsb_dir = config.paths.tsb_logs_dir
      assert tsb_dir.startswith('/tmp/test/tsb_logs/')
      
      # 验证路径结构
      parts = tsb_dir.split('/')
      assert parts[-5] == 'tsb_logs'
      assert len(parts[-4]) == 4  # 年份
      assert len(parts[-3]) == 2  # 周数
      assert len(parts[-2]) == 4  # 月日
      assert len(parts[-1]) == 6  # 时分秒
  ```

#### 2. 路径一致性测试
- **测试点**：验证tensorboard_dir始终等于tsb_logs_dir
- **期望结果**：两个路径完全相同
- **测试用例**：
  ```python
  def test_tensorboard_dir_equals_tsb_logs_dir():
      config = get_config_manager(test_mode=True)
      config.set('work_dir', '/tmp/test')
      
      # 多次访问验证一致性
      for _ in range(10):
          assert config.paths.tensorboard_dir == config.paths.tsb_logs_dir
  ```

#### 3. 只读属性测试
- **测试点**：验证tensorboard_dir不能被设置
- **期望结果**：抛出AttributeError
- **测试用例**：
  ```python
  def test_tensorboard_dir_readonly():
      config = get_config_manager(test_mode=True)
      
      with pytest.raises(AttributeError) as exc_info:
          config.paths.tensorboard_dir = "/custom/path"
      
      assert "只读属性" in str(exc_info.value)
  ```

#### 4. ISO周数测试
- **测试点**：验证ISO周数计算的正确性
- **期望结果**：符合ISO 8601标准
- **测试用例**：
  ```python
  def test_iso_week_calculation():
      from datetime import datetime
      
      # 测试特殊日期
      test_cases = [
          (datetime(2025, 1, 1), 1),    # 2025年第1周
          (datetime(2024, 12, 30), 1),  # 属于2025年第1周
          (datetime(2025, 12, 25), 52), # 2025年第52周
      ]
      
      for date, expected_week in test_cases:
          config = get_config_manager(
              test_mode=True,
              first_start_time=date
          )
          config.set('work_dir', '/tmp/test')
          
          tsb_dir = config.paths.tsb_logs_dir
          week_part = tsb_dir.split('/')[-3]
          assert int(week_part) == expected_week
  ```

### 性能测试

#### 1. 缓存效果测试
- **测试点**：验证1秒缓存机制
- **期望结果**：缓存期内返回相同路径
- **测试用例**：
  ```python
  def test_path_caching():
      config = get_config_manager(test_mode=True)
      config.set('work_dir', '/tmp/test')
      
      # 第一次访问
      path1 = config.paths.tsb_logs_dir
      
      # 0.5秒内再次访问（应该从缓存返回）
      time.sleep(0.5)
      path2 = config.paths.tsb_logs_dir
      assert path1 == path2
      
      # 等待缓存过期
      time.sleep(0.6)
      path3 = config.paths.tsb_logs_dir
      # 路径可能不同（如果时间戳变化）
  ```

#### 2. 访问性能测试
- **测试点**：测试大量访问的性能
- **期望结果**：平均访问时间 < 0.1ms
- **测试用例**：
  ```python
  def test_access_performance():
      config = get_config_manager(test_mode=True)
      config.set('work_dir', '/tmp/test')
      
      import timeit
      
      def access_paths():
          _ = config.paths.tsb_logs_dir
          _ = config.paths.tensorboard_dir
      
      # 测试10000次访问
      time_taken = timeit.timeit(access_paths, number=10000)
      avg_time = time_taken / 10000
      
      assert avg_time < 0.0001  # < 0.1ms
  ```

### 边界测试

#### 1. 无work_dir测试
- **测试点**：work_dir未设置时的行为
- **期望结果**：返回空字符串
- **测试用例**：
  ```python
  def test_no_work_dir():
      config = get_config_manager(test_mode=True)
      
      # 不设置work_dir
      assert config.paths.tsb_logs_dir == ''
      assert config.paths.tensorboard_dir == ''
  ```

#### 2. 特殊字符路径测试
- **测试点**：包含特殊字符的路径
- **期望结果**：正确处理路径
- **测试用例**：
  ```python
  def test_special_char_paths():
      config = get_config_manager(test_mode=True)
      
      # 测试包含空格的路径
      config.set('work_dir', '/tmp/test dir/项目')
      tsb_dir = config.paths.tsb_logs_dir
      assert '/tmp/test dir/项目/tsb_logs/' in tsb_dir
  ```

### 集成测试

#### 1. 配置保存和加载测试
- **测试点**：配置保存后重新加载
- **期望结果**：动态路径正确生成
- **测试用例**：
  ```python
  def test_config_save_load():
      # 创建并保存配置
      config1 = get_config_manager(test_mode=True)
      config1.set('work_dir', '/tmp/test')
      tsb_dir1 = config1.paths.tsb_logs_dir
      config1.save()
      
      # 重新加载配置
      config2 = get_config_manager(
          config_path=config1.config_path,
          test_mode=True
      )
      
      # 验证路径生成
      assert config2.paths.work_dir == '/tmp/test'
      # 注意：由于时间变化，路径可能不同
  ```

#### 2. 多进程访问测试
- **测试点**：多进程环境下的路径访问
- **期望结果**：各进程正确生成路径
- **测试用例**：
  ```python
  def test_multiprocess_access():
      from multiprocessing import Process, Queue
      
      def worker(queue):
          config = get_config_manager(test_mode=True)
          config.set('work_dir', '/tmp/test')
          
          tsb_dir = config.paths.tsb_logs_dir
          tb_dir = config.paths.tensorboard_dir
          
          queue.put({
              'tsb_dir': tsb_dir,
              'tb_dir': tb_dir,
              'equal': tsb_dir == tb_dir
          })
      
      queue = Queue()
      processes = []
      
      # 启动多个进程
      for _ in range(4):
          p = Process(target=worker, args=(queue,))
          p.start()
          processes.append(p)
      
      # 等待完成
      for p in processes:
          p.join()
      
      # 验证结果
      while not queue.empty():
          result = queue.get()
          assert result['equal']  # 验证路径一致性
  ```

## 测试数据

### 正常数据
- 标准work_dir路径
- 各种有效的时间戳
- 不同平台的路径格式

### 异常数据
- 空的work_dir
- 无效的时间戳
- 超长路径
- 特殊字符路径

### 边界数据
- 年初和年末的日期
- 跨年的ISO周数
- 极端时间值

## 测试环境

### 环境要求
- Python 3.12+
- pytest测试框架
- 多平台测试（Windows、Linux）

### 测试工具
- pytest：单元测试框架
- pytest-cov：覆盖率分析
- pytest-benchmark：性能测试

## 测试执行

### 执行顺序
1. 单元测试
2. 集成测试
3. 性能测试
4. 压力测试

### 执行命令
```bash
# 运行所有测试
pytest tests/test_tsb_tensorboard_paths.py -v

# 运行性能测试
pytest tests/test_tsb_tensorboard_paths.py -v -k performance

# 生成覆盖率报告
pytest tests/test_tsb_tensorboard_paths.py --cov=config_manager
```

## 验收标准

### 功能验收
- 所有功能测试用例通过
- 路径格式符合规范
- tensorboard_dir始终等于tsb_logs_dir

### 性能验收
- 平均访问时间 < 0.1ms
- 缓存命中率 > 95%
- 无内存泄漏

### 稳定性验收
- 连续运行24小时无异常
- 多进程并发访问无冲突
- 边界情况处理正确

## 风险和缓解

### 风险1：时区影响
- **描述**：不同时区可能影响周数计算
- **缓解**：使用UTC时间或本地时间一致性

### 风险2：缓存失效
- **描述**：缓存机制可能导致路径不一致
- **缓解**：1秒短缓存，快速失效

### 风险3：向后兼容
- **描述**：旧配置文件的tensorboard_dir设置
- **缓解**：自动忽略旧设置，不影响功能