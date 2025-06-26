# tests/config_manager/test_tc0008_002_call_chain_integration.py
from __future__ import annotations
from datetime import datetime

start_time = datetime.now()

import pytest
import tempfile
import os
import sys
import time
import asyncio
from io import StringIO
from contextlib import redirect_stdout
import shutil

# 添加src到路径，确保能导入配置管理器
project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
src_path = os.path.join(project_root, 'src')
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from config_manager.config_manager import get_config_manager, _clear_instances_for_testing
import config_manager.config_manager as cm_module


@pytest.fixture(autouse=True)
def cleanup_instances():
    """每个测试后清理实例"""
    # 临时开启调用链显示，因为这些是调用链集成测试
    original_switch = cm_module.ENABLE_CALL_CHAIN_DISPLAY
    cm_module.ENABLE_CALL_CHAIN_DISPLAY = True
    
    try:
        yield
    finally:
        # 恢复原始开关状态
        cm_module.ENABLE_CALL_CHAIN_DISPLAY = original_switch
        _clear_instances_for_testing()
    return


class MockApplication:
    """模拟应用程序类，用于测试真实场景下的调用链"""

    def __init__(self, config_path: str):
        self.config_path = config_path
        self.config = None

    def startup(self):
        """应用程序启动方法"""
        self.initialize_services()
        return

    def initialize_services(self):
        """初始化服务"""
        self.setup_configuration()
        return

    def setup_configuration(self):
        """设置配置"""
        output = StringIO()
        with redirect_stdout(output):
            self.config = get_config_manager(
                config_path=self.config_path,
                watch=False,
                autosave_delay=0.1
            )
            self.config.app_name = "MockApplication"
            self.config.version = "1.0.0"

        return output.getvalue()


def test_tc0008_002_001_real_world_application_startup():
    """测试真实世界应用程序启动时的调用链"""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_file = os.path.join(tmpdir, 'app_startup_test.yaml')

        app = MockApplication(config_file)
        startup_output = app.setup_configuration()

        # 验证调用链显示了完整的启动流程
        assert "调用链:" in startup_output
        assert "setup_configuration" in startup_output

        # 验证配置被正确设置
        assert app.config.app_name == "MockApplication"
        assert app.config.version == "1.0.0"

        print(f"应用程序启动调用链:\n{startup_output}")
        return


# tests/config_manager/test_tc0008_002_call_chain_integration.py
# 修复深层嵌套函数调用的调用链测试

def test_tc0008_002_002_deep_nested_function_calls():
    """测试深层嵌套函数调用的调用链"""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_file = os.path.join(tmpdir, 'deep_nested_test.yaml')

        def level_1():
            """第1层函数"""
            return level_2()

        def level_2():
            """第2层函数"""
            return level_3()

        def level_3():
            """第3层函数"""
            return level_4()

        def level_4():
            """第4层函数"""
            return level_5()

        def level_5():
            """第5层函数"""
            output = StringIO()
            with redirect_stdout(output):
                cfg = get_config_manager(
                    config_path=config_file,
                    watch=False,
                    autosave_delay=0.1
                )
                cfg.deep_nested_test = "success"

            return cfg, output.getvalue()

        cfg, output = level_1()

        # 验证深层嵌套的调用链
        assert "调用链:" in output

        # 修复断言：调用链实际上从config_manager内部开始，可能会被截断
        # 检查调用链是否包含我们的函数
        if "调用链:" in output:
            call_chain_line = None
            for line in output.split('\n'):
                if "调用链:" in line:
                    call_chain_line = line
                    break

            if call_chain_line:
                call_chain = call_chain_line.replace("调用链: ", "")

                # 验证调用链包含level_5函数（最内层的函数应该总是存在）
                assert "level_5" in call_chain

                # 验证调用链包含至少一些层级的函数
                # 由于调用链可能被截断（显示为...），不是所有level_1到level_5都会出现
                level_functions_in_chain = [f"level_{i}" for i in range(1, 6) if f"level_{i}" in call_chain]
                assert len(
                    level_functions_in_chain) >= 3, f"调用链应该包含至少3个level函数，实际包含: {level_functions_in_chain}"

                # 验证level_5（最内层）确实在调用链中
                assert "level_5" in level_functions_in_chain

                # 如果调用链被截断，应该包含"..."
                if "..." in call_chain:
                    print("调用链被截断，这是正常的深度限制行为")

        print(f"深层嵌套调用链:\n{output}")
        return


def test_tc0008_002_003_multiple_config_instances():
    """测试多个配置实例的调用链"""
    # 使用手动清理来避免Windows权限问题
    tmpdir = tempfile.mkdtemp()
    config_file_1 = os.path.join(tmpdir, 'config_1.yaml')
    config_file_2 = os.path.join(tmpdir, 'config_2.yaml')
    
    # 记录创建的配置管理器实例，便于清理
    created_configs = []

    try:
        def create_config_1():
            """创建第一个配置"""
            output = StringIO()
            with redirect_stdout(output):
                cfg = get_config_manager(
                    config_path=config_file_1,
                    watch=False,
                    autosave_delay=0.1
                )
                cfg.instance_id = "config_1"
                created_configs.append(cfg)

            return cfg, output.getvalue()

        def create_config_2():
            """创建第二个配置"""
            output = StringIO()
            with redirect_stdout(output):
                cfg = get_config_manager(
                    config_path=config_file_2,
                    watch=False,
                    autosave_delay=0.1
                )
                cfg.instance_id = "config_2"
                created_configs.append(cfg)

            return cfg, output.getvalue()

        cfg1, output1 = create_config_1()
        cfg2, output2 = create_config_2()

        # 验证两个不同的配置实例都有正确的调用链
        assert "调用链:" in output1
        assert "create_config_1" in output1

        assert "调用链:" in output2
        assert "create_config_2" in output2

        # 验证实例是独立的
        assert cfg1.instance_id == "config_1"
        assert cfg2.instance_id == "config_2"
        assert cfg1 is not cfg2

        print(f"配置1调用链:\n{output1}")
        print(f"配置2调用链:\n{output2}")

    finally:
        # 手动清理，确保所有文件操作完成
        try:
            # 先清理配置管理器实例
            for cfg in created_configs:
                if hasattr(cfg, '_cleanup'):
                    try:
                        cfg._cleanup()
                    except:
                        pass
            
            _clear_instances_for_testing()

            # 等待所有异步操作和文件操作完成
            time.sleep(0.5)

            # 尝试删除临时目录
            max_attempts = 5
            for attempt in range(max_attempts):
                try:
                    assert tmpdir.startswith(tempfile.gettempdir()), f"禁止删除非临时目录: {tmpdir}"
                    shutil.rmtree(tmpdir)
                    break
                except (OSError, PermissionError) as e:
                    if attempt < max_attempts - 1:
                        # 等待更长时间让Windows释放文件
                        time.sleep(0.5)
                    else:
                        # 最后一次尝试失败，只打印警告，不抛出异常
                        print(f"警告：无法删除临时目录 {tmpdir}: {e}")
        except Exception as e:
            print(f"清理过程中的错误: {e}")

    return


def test_tc0008_002_004_call_chain_performance():
    """测试调用链功能的性能"""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_file = os.path.join(tmpdir, 'performance_test.yaml')

        def measure_call_chain_overhead():
            """测量调用链开销"""
            start_time_val = time.time()

            # 执行多次配置创建来测量性能
            for i in range(10):
                output = StringIO()
                with redirect_stdout(output):
                    cfg = get_config_manager(
                        config_path=config_file,
                        watch=False,
                        autosave_delay=0.1
                    )
                    cfg.performance_test_iteration = i

                # 清理实例以便下次创建新的
                _clear_instances_for_testing()

            end_time_val = time.time()
            return end_time_val - start_time_val

        execution_time = measure_call_chain_overhead()

        # 验证调用链功能不会造成严重的性能问题
        # 10次操作应该在合理时间内完成（考虑到文件I/O和路径配置初始化，5秒以内是合理的）
        assert execution_time < 5.0, f"调用链功能可能存在性能问题，执行时间: {execution_time:.3f}秒"

        print(f"调用链性能测试: 10次操作耗时 {execution_time:.3f}秒")
        return


def test_tc0008_002_005_call_chain_with_module_start_time():
    """测试调用链与模块start_time的集成"""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_file = os.path.join(tmpdir, 'start_time_integration_test.yaml')

        # 设置当前模块的start_time
        test_start_time = datetime(2025, 6, 2, 16, 45, 30)
        current_module = sys.modules[__name__]
        original_start_time = getattr(current_module, 'start_time', None)
        setattr(current_module, 'start_time', test_start_time)

        try:
            def function_with_module_start_time():
                """使用模块start_time的函数"""
                output = StringIO()
                with redirect_stdout(output):
                    cfg = get_config_manager(
                        config_path=config_file,
                        watch=False,
                        autosave_delay=0.1,
                        first_start_time=test_start_time
                    )
                    cfg.module_start_time_test = "success"

                return cfg, output.getvalue()

            cfg, output = function_with_module_start_time()

            # 验证调用链正常显示
            assert "调用链:" in output
            assert "function_with_module_start_time" in output

            # 验证start_time被正确获取和使用
            if hasattr(cfg, '_first_start_time'):
                assert cfg._first_start_time == test_start_time

            # 验证start_time被保存到配置中
            saved_start_time = cfg.get('first_start_time')
            if saved_start_time:
                parsed_time = datetime.fromisoformat(saved_start_time)
                assert parsed_time == test_start_time

            print(f"模块start_time集成测试调用链:\n{output}")

        finally:
            # 恢复原始start_time
            if original_start_time is not None:
                setattr(current_module, 'start_time', original_start_time)
            elif hasattr(current_module, 'start_time'):
                delattr(current_module, 'start_time')

        return


@pytest.mark.asyncio
async def test_tc0008_002_006_async_scheduler_scenario():
    """测试异步调度器场景下的调用链"""
    # 使用手动清理来避免Windows权限问题
    tmpdir = tempfile.mkdtemp()
    config_file = os.path.join(tmpdir, 'async_scheduler_test.yaml')

    # 记录创建的配置管理器实例，便于清理
    created_config = None

    try:
        class MockScheduler:
            """模拟调度器类"""

            def __init__(self):
                self.config = None

            async def run_all(self):
                """模拟run_all方法"""
                await self.initialize_config()
                await self.execute_tasks()
                return

            async def initialize_config(self):
                """初始化配置"""
                output = StringIO()
                with redirect_stdout(output):
                    self.config = get_config_manager(
                        config_path=config_file,
                        watch=False,
                        autosave_delay=0.1
                    )
                    self.config.scheduler_status = "initialized"
                    # 保存实例引用
                    nonlocal created_config
                    created_config = self.config

                return output.getvalue()

            async def execute_tasks(self):
                """执行任务"""
                if self.config:
                    self.config.scheduler_status = "running"
                await asyncio.sleep(0.1)
                return

        scheduler = MockScheduler()
        init_output = await scheduler.initialize_config()
        await scheduler.execute_tasks()

        # 验证异步场景下的调用链
        assert "调用链:" in init_output
        assert "initialize_config" in init_output

        # 验证配置状态
        assert scheduler.config.scheduler_status == "running"

        print(f"异步调度器场景调用链:\n{init_output}")

    finally:
        # 手动清理，确保所有文件操作完成
        try:
            # 先清理配置管理器实例
            _clear_instances_for_testing()

            # 如果有创建的配置实例，确保其清理完成
            if created_config and hasattr(created_config, '_cleanup'):
                try:
                    created_config._cleanup()
                except:
                    pass

            # 等待所有异步操作和文件操作完成
            await asyncio.sleep(0.5)

            # 同步等待，确保Windows文件系统释放文件句柄
            time.sleep(0.5)

            # 尝试删除临时目录
            max_attempts = 5
            for attempt in range(max_attempts):
                try:
                    assert tmpdir.startswith(tempfile.gettempdir()), f"禁止删除非临时目录: {tmpdir}"
                    shutil.rmtree(tmpdir)
                    break
                except (OSError, PermissionError) as e:
                    if attempt < max_attempts - 1:
                        # 等待更长时间让Windows释放文件
                        await asyncio.sleep(0.5)
                        time.sleep(0.5)
                    else:
                        # 最后一次尝试失败，只打印警告，不抛出异常
                        print(f"警告：无法删除临时目录 {tmpdir}: {e}")
        except Exception as e:
            print(f"清理过程中的错误: {e}")

    return


def test_tc0008_002_007_exception_handling_scenario():
    """测试异常处理场景下的调用链"""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_file = os.path.join(tmpdir, 'exception_test.yaml')

        def function_that_might_fail():
            """可能失败的函数"""
            try:
                output = StringIO()
                with redirect_stdout(output):
                    cfg = get_config_manager(
                        config_path=config_file,
                        watch=False,
                        autosave_delay=0.1
                    )
                    cfg.test_before_exception = "success"

                # 模拟一些可能的异常情况
                # 这里我们不实际抛出异常，只是演示调用链在异常处理中的使用
                return cfg, output.getvalue()

            except Exception as e:
                # 在实际应用中，这里可能会记录调用链用于调试
                return None, str(e)

        def error_handling_wrapper():
            """错误处理包装器"""
            try:
                return function_that_might_fail()
            except Exception as e:
                return None, f"包装器捕获异常: {e}"

        cfg, output = error_handling_wrapper()

        # 验证即使在异常处理场景下，调用链也能正常工作
        assert cfg is not None
        assert "调用链:" in output
        assert "function_that_might_fail" in output

        print(f"异常处理场景调用链:\n{output}")
        return