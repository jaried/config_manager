# tests/config_manager/test_tc0002_002_async_envs_scenario.py
from __future__ import annotations
from datetime import datetime

start_time = datetime.now()

import pytest
import tempfile
import asyncio
import os
import sys
from ruamel.yaml import YAML
from unittest.mock import patch, MagicMock
from src.config_manager.config_manager import get_config_manager, _clear_instances_for_testing

# 创建YAML实例用于测试
yaml = YAML()
yaml.default_flow_style = False


@pytest.fixture(autouse=True)
def cleanup_instances():
    """每个测试后清理实例"""
    yield
    _clear_instances_for_testing()
    return


async def mock_main() -> None:
    """模拟主入口函数"""
    # 模拟 setup_project_environment()
    # 模拟 init_custom_logger_system()

    # 启动调度器
    scheduler = MockScheduler()
    await scheduler.run_all()
    return


def test_tc0002_002_001_async_main_scheduler_flow():
    """测试异步主程序调用调度器的完整流程"""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_file = os.path.join(tmpdir, 'async_test_config.yaml')

        # 模拟真实的异步嵌套场景
        async def mock_main():
            """模拟main.py中的main()函数"""
            # 第一次调用 - 模拟main.py中的配置初始化
            cfg_main = get_config_manager(
                config_path=config_file,
                autosave_delay=0.1,
                watch=False
            )
            cfg_main.main_module_data = "from_main"
            cfg_main.main_startup_time = datetime.now().isoformat()

            # 等待自动保存
            await asyncio.sleep(0.2)

            # 模拟调用scheduler.run_all()
            scheduler = MockScheduler()
            await scheduler.run_all()

            return cfg_main

        # 运行完整的异步流程（就像真实的 asyncio.run(main()) ）
        result_cfg_main = asyncio.run(mock_main())

        # 验证main配置的数据
        assert result_cfg_main.get('main_module_data') == "from_main"
        assert result_cfg_main.get('main_startup_time') is not None

        # 验证scheduler在异步中设置的数据也存在
        # 注意：由于MockScheduler中调用的是get_config_manager()无参数
        # 它可能创建了不同的实例，这取决于默认路径的解析

        # 验证备份文件存在
        backup_path = result_cfg_main._get_backup_path()
        assert os.path.exists(backup_path)
    return


class MockScheduler:
    """模拟调度器类 - 更真实的异步场景"""

    async def run_all(self) -> None:
        """模拟运行完整的爬取流程 - 异步中的异步调用"""
        try:
            # 模拟异步初始化
            await asyncio.sleep(0.1)

            # 读取配置 - 这里会调用 get_config_manager()
            # 在真实场景中，这可能会创建新实例或使用现有实例
            config = get_config_manager()

            # 模拟检查配置项（就像真实场景中检查'titls'）
            if not hasattr(config, 'titls') and config.get('titls') is None:
                # 模拟配置项缺失的情况
                config.missing_config_error = "配置文件中缺少 'titls' 配置项"

            # 模拟一些配置操作
            config.test_async_value = "async_test_data"
            config.scheduler_status = "running"
            config.scheduler_start_time = datetime.now().isoformat()

            # 模拟异步工作
            await asyncio.sleep(0.1)

            # 模拟更多异步操作
            config.scheduler_progress = "processing"
            await asyncio.sleep(0.1)

            config.scheduler_progress = "completed"

            return
        except Exception as e:
            # 模拟异常处理
            config = get_config_manager()
            config.scheduler_error = str(e)
            raise e


def test_tc0002_002_002_envs_path_simulation():
    """测试模拟envs路径的配置加载场景"""
    with tempfile.TemporaryDirectory() as tmpdir:
        # 创建模拟的envs路径结构
        envs_config_dir = os.path.join(tmpdir, 'envs', 'base_python3.12', 'Lib', 'site-packages', 'config')
        os.makedirs(envs_config_dir, exist_ok=True)
        envs_config_file = os.path.join(envs_config_dir, 'config.yaml')

        # 创建初始配置文件
        initial_config = {
            '__data__': {
                'envs_test': 'envs_environment',
                'python_version': '3.12'
            }
        }
        with open(envs_config_file, 'w', encoding='utf-8') as f:
            yaml.dump(initial_config, f)

        async def simulate_envs_scenario():
            # 模拟第一次调用（正常项目路径）
            project_config_file = os.path.join(tmpdir, 'project_config.yaml')
            cfg1 = get_config_manager(
                config_path=project_config_file,
                autosave_delay=0.1,
                watch=False
            )
            cfg1.project_data = "project_environment"

            await asyncio.sleep(0.2)

            # 清理实例，模拟不同模块的调用
            _clear_instances_for_testing()

            # 模拟第二次调用（envs路径）
            cfg2 = get_config_manager(
                config_path=envs_config_file,
                autosave_delay=0.1,
                watch=False
            )

            # 验证加载了envs配置
            assert cfg2.get('envs_test') == 'envs_environment'
            assert cfg2.get('python_version') == '3.12'

            # 添加新数据
            cfg2.scheduler_envs_data = "from_envs_scheduler"

            await asyncio.sleep(0.2)

            return cfg1, cfg2

        cfg1, cfg2 = asyncio.run(simulate_envs_scenario())

        # 验证两个配置管理器是独立的
        assert cfg1 is not cfg2

        # 验证各自的备份文件都存在
        backup_path1 = cfg1._get_backup_path()
        backup_path2 = cfg2._get_backup_path()

        assert os.path.exists(backup_path1)
        assert os.path.exists(backup_path2)

        # 验证备份路径不同
        assert backup_path1 != backup_path2
    return


def test_tc0002_002_003_multiple_async_calls_same_path():
    """测试多个异步调用使用相同路径的场景"""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_file = os.path.join(tmpdir, 'shared_async_config.yaml')

        async def async_worker(worker_id: int, delay: float):
            """模拟异步工作者"""
            cfg = get_config_manager(
                config_path=config_file,
                autosave_delay=0.1,
                watch=False
            )

            # 设置工作者特定的数据
            setattr(cfg, f'worker_{worker_id}_data', f'data_from_worker_{worker_id}')
            setattr(cfg, f'worker_{worker_id}_timestamp', datetime.now().isoformat())

            # 模拟异步工作
            await asyncio.sleep(delay)

            return cfg, worker_id

        async def run_multiple_workers():
            # 并发运行多个异步工作者
            tasks = [
                async_worker(1, 0.1),
                async_worker(2, 0.15),
                async_worker(3, 0.05)
            ]

            results = await asyncio.gather(*tasks)
            return results

        async def test_with_final_wait():
            results = await run_multiple_workers()

            # 验证所有工作者使用的是同一个配置实例（单例模式）
            cfg_instances = [result[0] for result in results]
            for i in range(1, len(cfg_instances)):
                assert cfg_instances[0] is cfg_instances[i]

            # 验证所有工作者的数据都存在
            cfg = cfg_instances[0]
            for worker_id in [1, 2, 3]:
                assert cfg.get(f'worker_{worker_id}_data') == f'data_from_worker_{worker_id}'
                assert cfg.get(f'worker_{worker_id}_timestamp') is not None

            # 等待自动保存完成
            await asyncio.sleep(0.3)

            return cfg

        result_cfg = asyncio.run(test_with_final_wait())

        # 验证备份文件存在
        backup_path = result_cfg._get_backup_path()
        assert os.path.exists(backup_path)
    return


def test_tc0002_002_004_async_exception_handling():
    """测试异步环境中的异常处理"""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_file = os.path.join(tmpdir, 'exception_test_config.yaml')

        async def async_operation_with_exception():
            """模拟可能抛出异常的异步操作"""
            cfg = get_config_manager(
                config_path=config_file,
                autosave_delay=0.1,
                watch=False
            )

            cfg.before_exception = "data_before_exception"

            # 等待自动保存
            await asyncio.sleep(0.2)

            # 模拟异常情况
            try:
                cfg.exception_test = "this_will_cause_exception"
                # 模拟一个可能的异常场景
                if True:  # 模拟条件
                    raise ValueError("模拟的异步异常")
            except ValueError as e:
                # 异常处理后继续设置配置
                cfg.after_exception = "data_after_exception_handling"
                cfg.exception_message = str(e)

                # 等待自动保存
                await asyncio.sleep(0.2)

                return cfg

        result_cfg = asyncio.run(async_operation_with_exception())

        # 验证异常前后的数据都被保存
        assert result_cfg.get('before_exception') == "data_before_exception"
        assert result_cfg.get('after_exception') == "data_after_exception_handling"
        assert result_cfg.get('exception_message') == "模拟的异步异常"

        # 验证备份文件存在
        backup_path = result_cfg._get_backup_path()
        assert os.path.exists(backup_path)
    return


def test_tc0002_002_005_mock_real_scenario():
    """测试模拟真实场景：main.py -> scheduler.run_all()"""
    with tempfile.TemporaryDirectory() as tmpdir:
        # 设置项目配置文件路径
        project_config = os.path.join(tmpdir, 'project', 'src', 'config', 'config.yaml')
        os.makedirs(os.path.dirname(project_config), exist_ok=True)

        # 设置envs配置文件路径
        envs_config = os.path.join(tmpdir, 'envs', 'base_python3.12', 'Lib', 'site-packages', 'config', 'config.yaml')
        os.makedirs(os.path.dirname(envs_config), exist_ok=True)

        # 创建初始envs配置
        envs_initial_config = {
            '__data__': {
                'environment': 'conda_env',
                'python_path': '/envs/base_python3.12'
            }
        }
        with open(envs_config, 'w', encoding='utf-8') as f:
            yaml.dump(envs_initial_config, f)

        async def simulate_real_scenario():
            # 第一步：模拟main.py中的调用
            cfg_main = get_config_manager(
                config_path=project_config,
                autosave_delay=0.1,
                watch=False
            )
            cfg_main.main_startup = "main_module_started"
            cfg_main.project_root = tmpdir

            await asyncio.sleep(0.2)

            # 保存main配置的备份路径和数据，用于后续验证
            main_backup_path = cfg_main._get_backup_path()
            main_config_path = cfg_main.get_config_path()
            main_data = {
                'main_startup': cfg_main.get('main_startup'),
                'project_root': cfg_main.get('project_root')
            }

            # 第二步：模拟scheduler中的调用（可能使用不同路径）
            # 清理实例模拟不同模块调用
            _clear_instances_for_testing()

            # 模拟scheduler调用时使用envs路径
            cfg_scheduler = get_config_manager(
                config_path=envs_config,
                autosave_delay=0.1,
                watch=False
            )

            # 验证加载了envs配置
            assert cfg_scheduler.get('environment') == 'conda_env'

            # 添加scheduler数据
            cfg_scheduler.scheduler_started = "scheduler_module_started"
            cfg_scheduler.crawl_status = "initialized"

            await asyncio.sleep(0.2)

            # 第三步：模拟后续的配置操作
            cfg_scheduler.crawl_progress = "50%"
            cfg_scheduler.last_update = datetime.now().isoformat()

            await asyncio.sleep(0.2)

            # 重新加载main配置以验证数据持久性
            cfg_main_reloaded = get_config_manager(
                config_path=main_config_path,
                autosave_delay=0.1,
                watch=False
            )

            return cfg_main_reloaded, cfg_scheduler, main_backup_path, main_data

        cfg_main_reloaded, cfg_scheduler, main_backup_path, expected_main_data = asyncio.run(simulate_real_scenario())

        # 验证两个配置管理器是独立的
        assert cfg_main_reloaded is not cfg_scheduler

        # 验证main配置（从重新加载的实例中）
        assert cfg_main_reloaded.get('main_startup') == expected_main_data['main_startup']
        assert cfg_main_reloaded.get('project_root') == expected_main_data['project_root']

        # 验证scheduler配置
        assert cfg_scheduler.get('environment') == 'conda_env'
        assert cfg_scheduler.get('scheduler_started') == "scheduler_module_started"
        assert cfg_scheduler.get('crawl_status') == "initialized"
        assert cfg_scheduler.get('crawl_progress') == "50%"

        # 验证备份文件都存在
        scheduler_backup = cfg_scheduler._get_backup_path()

        assert os.path.exists(main_backup_path)
        assert os.path.exists(scheduler_backup)

        # 验证备份文件路径不同
        assert main_backup_path != scheduler_backup

        # 验证备份文件内容
        with open(scheduler_backup, 'r', encoding='utf-8') as f:
            scheduler_backup_content = yaml.load(f)

        assert scheduler_backup_content['__data__']['environment'] == 'conda_env'
        assert scheduler_backup_content['__data__']['scheduler_started'] == "scheduler_module_started"

        # 验证main配置的备份文件内容
        with open(main_backup_path, 'r', encoding='utf-8') as f:
            main_backup_content = yaml.load(f)

        assert main_backup_content['__data__']['main_startup'] == "main_module_started"
        assert main_backup_content['__data__']['project_root'] == expected_main_data['project_root']
    return


@pytest.mark.asyncio
async def test_tc0002_002_006_pytest_async_decorator():
    """使用pytest.mark.asyncio装饰器的异步测试"""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_file = os.path.join(tmpdir, 'pytest_async_config.yaml')

        # 第一个异步操作
        cfg1 = get_config_manager(
            config_path=config_file,
            autosave_delay=0.1,
            watch=False
        )
        cfg1.pytest_async_test = "async_with_decorator"

        # 等待自动保存
        await asyncio.sleep(0.2)

        # 第二个异步操作
        cfg1.async_operation_count = 1

        await asyncio.sleep(0.1)

        cfg1.async_operation_count = 2

        # 最终等待
        await asyncio.sleep(0.2)

        # 验证数据
        assert cfg1.get('pytest_async_test') == "async_with_decorator"
        assert cfg1.get('async_operation_count') == 2

        # 验证备份文件
        backup_path = cfg1._get_backup_path()
        assert os.path.exists(backup_path)
    return

