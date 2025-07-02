# tests/01_unit_tests/config_manager/test_tc0009_001_call_chain_switch.py
from __future__ import annotations
from datetime import datetime

start_time = datetime.now()

import pytest
import tempfile
import os
import sys
from io import StringIO
from contextlib import redirect_stdout
from unittest.mock import patch

# 添加src到路径
# 项目根目录由conftest.py自动配置

from src.config_manager import get_config_manager
from src.config_manager.config_manager import _clear_instances_for_testing


@pytest.fixture(autouse=True)
def cleanup_instances():
    """每个测试后清理实例"""
    yield
    _clear_instances_for_testing()
    return



class TestCallChainSwitch:
    """测试调用链显示开关功能"""

    def test_tc0009_001_001_switch_disabled_no_call_chain(self):
        """测试开关关闭时不显示调用链"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = os.path.join(tmpdir, 'switch_off_test.yaml')

            # 确保开关关闭
            import src.config_manager.config_manager as cm_module
            original_switch = cm_module.ENABLE_CALL_CHAIN_DISPLAY
            cm_module.ENABLE_CALL_CHAIN_DISPLAY = False

            try:
                # 捕获所有输出
                output = StringIO()
                with redirect_stdout(output):
                    cfg = get_config_manager(
                        config_path=config_file,
                        watch=False,
                        autosave_delay=0.1
                    )
                    cfg.switch_test = "disabled_test"
                    cfg.save()

                captured_output = output.getvalue()
                print(f"开关关闭时的输出:\n{captured_output}")

                # 验证不包含调用链信息
                assert "调用链:" not in captured_output
                assert "创建配置调用链:" not in captured_output
                assert "加载配置调用链:" not in captured_output
                assert "保存配置时的调用链:" not in captured_output
                assert "初始化时调用链:" not in captured_output

                # 但应该包含基本的配置操作信息
                assert ("配置文件不存在" in captured_output or
                        "配置已从" in captured_output)

                print("✓ 开关关闭时成功屏蔽了调用链显示")

            finally:
                # 恢复原始开关状态
                cm_module.ENABLE_CALL_CHAIN_DISPLAY = original_switch
        return

    def test_tc0009_001_002_switch_enabled_shows_call_chain(self):
        """测试开关开启时显示调用链"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = os.path.join(tmpdir, 'switch_on_test.yaml')

            # 确保开关开启
            import src.config_manager.config_manager as cm_module
            original_switch = cm_module.ENABLE_CALL_CHAIN_DISPLAY
            cm_module.ENABLE_CALL_CHAIN_DISPLAY = True

            try:
                # 捕获所有输出
                output = StringIO()
                with redirect_stdout(output):
                    cfg = get_config_manager(
                        config_path=config_file,
                        watch=False,
                        autosave_delay=0.1
                    )
                    cfg.switch_test = "enabled_test"
                    cfg.save()

                captured_output = output.getvalue()
                print(f"开关开启时的输出:\n{captured_output}")

                # 验证包含调用链信息
                call_chain_indicators = [
                    "调用链:",
                    "创建配置调用链:",
                    "加载配置调用链:",
                    "保存配置时的调用链:",
                    "初始化时调用链:"
                ]

                found_indicators = [indicator for indicator in call_chain_indicators
                                    if indicator in captured_output]

                assert len(found_indicators) >= 1, f"开关开启时应该显示调用链信息，但只找到: {found_indicators}"

                # 验证调用链内容格式
                if "调用链:" in captured_output:
                    lines = captured_output.split('\n')
                    chain_lines = [line for line in lines if "调用链:" in line]

                    for chain_line in chain_lines:
                        # 验证调用链格式包含环境信息
                        assert "[P:" in chain_line, f"调用链应包含进程信息: {chain_line}"
                        assert "|T:" in chain_line, f"调用链应包含线程信息: {chain_line}"

                print("✓ 开关开启时成功显示了调用链信息")

            finally:
                # 恢复原始开关状态
                cm_module.ENABLE_CALL_CHAIN_DISPLAY = original_switch
        return

    def test_tc0009_001_003_switch_toggle_behavior(self):
        """测试开关动态切换行为"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = os.path.join(tmpdir, 'switch_toggle_test.yaml')

            import src.config_manager.config_manager as cm_module
            original_switch = cm_module.ENABLE_CALL_CHAIN_DISPLAY

            try:
                # 第一次：开关关闭
                cm_module.ENABLE_CALL_CHAIN_DISPLAY = False
                _clear_instances_for_testing()

                output1 = StringIO()
                with redirect_stdout(output1):
                    cfg1 = get_config_manager(
                        config_path=config_file,
                        watch=False,
                        autosave_delay=0.1
                    )
                    cfg1.toggle_test_1 = "first_test"

                captured_output1 = output1.getvalue()
                assert "调用链:" not in captured_output1
                print("✓ 第一次测试：开关关闭，无调用链显示")

                # 第二次：开关开启
                cm_module.ENABLE_CALL_CHAIN_DISPLAY = True
                _clear_instances_for_testing()

                output2 = StringIO()
                with redirect_stdout(output2):
                    cfg2 = get_config_manager(
                        config_path=config_file,
                        watch=False,
                        autosave_delay=0.1
                    )
                    cfg2.toggle_test_2 = "second_test"

                captured_output2 = output2.getvalue()
                assert "调用链:" in captured_output2
                print("✓ 第二次测试：开关开启，显示调用链")

                # 第三次：再次关闭
                cm_module.ENABLE_CALL_CHAIN_DISPLAY = False
                _clear_instances_for_testing()

                output3 = StringIO()
                with redirect_stdout(output3):
                    cfg3 = get_config_manager(
                        config_path=config_file,
                        watch=False,
                        autosave_delay=0.1
                    )
                    cfg3.toggle_test_3 = "third_test"

                captured_output3 = output3.getvalue()
                assert "调用链:" not in captured_output3
                print("✓ 第三次测试：开关再次关闭，无调用链显示")

                print("✓ 开关动态切换功能正常")

            finally:
                # 恢复原始开关状态
                cm_module.ENABLE_CALL_CHAIN_DISPLAY = original_switch
        return

    def test_tc0009_001_004_different_operations_respect_switch(self):
        """测试不同操作都遵守开关设置"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = os.path.join(tmpdir, 'operations_test.yaml')

            import src.config_manager.config_manager as cm_module
            original_switch = cm_module.ENABLE_CALL_CHAIN_DISPLAY

            try:
                # 测试开关关闭时的各种操作
                cm_module.ENABLE_CALL_CHAIN_DISPLAY = False

                output = StringIO()
                with redirect_stdout(output):
                    # 创建配置管理器
                    cfg = get_config_manager(
                        config_path=config_file,
                        watch=False,
                        autosave_delay=0.1
                    )

                    # 设置配置
                    cfg.operation_test = "test_value"

                    # 手动保存
                    cfg.save()

                    # 重新加载
                    cfg.reload()

                    # 更新配置
                    cfg.update({'batch_update': 'batch_value'})

                captured_output = output.getvalue()

                # 验证所有操作都没有显示调用链
                call_chain_keywords = [
                    "调用链:",
                    "创建配置调用链:",
                    "加载配置调用链:",
                    "保存配置时的调用链:",
                    "重新加载配置时的调用链:",
                    "安排自动保存时的调用链:",
                    "初始化时调用链:"
                ]

                for keyword in call_chain_keywords:
                    assert keyword not in captured_output, f"开关关闭时不应显示: {keyword}"

                # 但应该有基本的操作信息
                assert ("配置文件不存在" in captured_output or
                        "配置已从" in captured_output)

                print("✓ 所有操作都正确遵守了开关关闭设置")

            finally:
                # 恢复原始开关状态
                cm_module.ENABLE_CALL_CHAIN_DISPLAY = original_switch
        return

    def test_tc0009_001_005_switch_with_nested_function_calls(self):
        """测试在嵌套函数调用中开关的行为"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = os.path.join(tmpdir, 'nested_test.yaml')

            import src.config_manager.config_manager as cm_module
            original_switch = cm_module.ENABLE_CALL_CHAIN_DISPLAY

            def level_3_function():
                """第三层函数"""
                cfg = get_config_manager(
                    config_path=config_file,
                    watch=False,
                    autosave_delay=0.1
                )
                cfg.nested_test = "deep_call"
                cfg.save()
                return cfg

            def level_2_function():
                """第二层函数"""
                return level_3_function()

            def level_1_function():
                """第一层函数"""
                return level_2_function()

            try:
                # 测试开关关闭
                cm_module.ENABLE_CALL_CHAIN_DISPLAY = False

                output = StringIO()
                with redirect_stdout(output):
                    cfg = level_1_function()

                captured_output = output.getvalue()

                # 即使是深层嵌套调用，也不应该显示调用链
                assert "调用链:" not in captured_output
                assert "level_1_function" not in captured_output
                assert "level_2_function" not in captured_output
                assert "level_3_function" not in captured_output

                print("✓ 嵌套函数调用中开关关闭正常工作")

                # 测试开关开启
                _clear_instances_for_testing()
                cm_module.ENABLE_CALL_CHAIN_DISPLAY = True

                output2 = StringIO()
                with redirect_stdout(output2):
                    cfg2 = level_1_function()

                captured_output2 = output2.getvalue()

                # 开启时应该显示调用链和函数名
                assert "调用链:" in captured_output2
                # 调用链中应该包含我们的函数名
                functions_in_chain = ["level_1_function", "level_2_function", "level_3_function"]
                found_functions = [func for func in functions_in_chain if func in captured_output2]

                assert len(found_functions) >= 1, f"开启时应该在调用链中显示函数名，找到: {found_functions}"

                print("✓ 嵌套函数调用中开关开启正常工作")

            finally:
                # 恢复原始开关状态
                cm_module.ENABLE_CALL_CHAIN_DISPLAY = original_switch
        return

    def test_tc0009_001_006_switch_default_state(self):
        """测试开关的默认状态"""
        import src.config_manager.config_manager as cm_module

        # 验证开关存在且为布尔类型（不验证具体默认值，因为会经常变化）
        assert hasattr(cm_module, 'ENABLE_CALL_CHAIN_DISPLAY'), "调用链显示开关应该存在"
        assert isinstance(cm_module.ENABLE_CALL_CHAIN_DISPLAY, bool), "调用链显示开关应该是布尔类型"

        print(f"✓ 开关默认状态验证通过：当前值为 {cm_module.ENABLE_CALL_CHAIN_DISPLAY}")
        return

    def test_tc0009_001_007_switch_type_validation(self):
        """测试开关类型验证"""
        import src.config_manager.config_manager as cm_module
        original_switch = cm_module.ENABLE_CALL_CHAIN_DISPLAY

        try:
            # 验证开关是布尔类型
            assert isinstance(cm_module.ENABLE_CALL_CHAIN_DISPLAY, bool), "开关应该是布尔类型"

            # 测试设置为不同的布尔值
            cm_module.ENABLE_CALL_CHAIN_DISPLAY = True
            assert cm_module.ENABLE_CALL_CHAIN_DISPLAY is True

            cm_module.ENABLE_CALL_CHAIN_DISPLAY = False
            assert cm_module.ENABLE_CALL_CHAIN_DISPLAY is False

            print("✓ 开关类型验证通过：布尔类型")

        finally:
            # 恢复原始开关状态
            cm_module.ENABLE_CALL_CHAIN_DISPLAY = original_switch
        return


if __name__ == "__main__":
    # 直接运行测试
    test_instance = TestCallChainSwitch()

    print("开始调用链显示开关测试")
    print("=" * 50)

    try:
        test_instance.test_tc0009_001_001_switch_disabled_no_call_chain()
        print("✓ 测试1通过：开关关闭时不显示调用链")

        test_instance.test_tc0009_001_002_switch_enabled_shows_call_chain()
        print("✓ 测试2通过：开关开启时显示调用链")

        test_instance.test_tc0009_001_003_switch_toggle_behavior()
        print("✓ 测试3通过：开关动态切换行为")

        test_instance.test_tc0009_001_004_different_operations_respect_switch()
        print("✓ 测试4通过：所有操作遵守开关设置")

        test_instance.test_tc0009_001_005_switch_with_nested_function_calls()
        print("✓ 测试5通过：嵌套函数调用中的开关行为")

        test_instance.test_tc0009_001_006_switch_default_state()
        print("✓ 测试6通过：开关默认状态验证")

        test_instance.test_tc0009_001_007_switch_type_validation()
        print("✓ 测试7通过：开关类型验证")

        print("\n" + "=" * 50)
        print("🎉 所有调用链显示开关测试通过！")
        print("\n测试总结：")
        print("• 开关关闭时成功屏蔽所有调用链显示")
        print("• 开关开启时正常显示完整调用链信息")
        print("• 开关可以动态切换并立即生效")
        print("• 所有配置操作都正确遵守开关设置")
        print("• 嵌套函数调用中开关行为正常")
        print("• 开关默认状态和类型验证正确")

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback

        traceback.print_exc()
    finally:
        # 最终清理
        _clear_instances_for_testing()
