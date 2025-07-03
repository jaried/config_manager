#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试ENABLE_CALL_CHAIN_DISPLAY开启时不显示配置数据
"""
from __future__ import annotations
from datetime import datetime

start_time = datetime.now()

import sys
import os
import tempfile
from io import StringIO
from contextlib import redirect_stdout

# 添加src路径
project_root = os.path.dirname(os.path.dirname(__file__))
src_path = os.path.join(project_root, 'src')
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from config_manager.config_manager import get_config_manager, _clear_instances_for_testing
import config_manager.config_manager as cm_module


def test_no_config_data_display():
    """测试ENABLE_CALL_CHAIN_DISPLAY开启时不显示配置数据"""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_file = os.path.join(tmpdir, 'test_config.yaml')
        
        # 确保开关开启
        original_switch = cm_module.ENABLE_CALL_CHAIN_DISPLAY
        cm_module.ENABLE_CALL_CHAIN_DISPLAY = True
        
        try:
            # 清理实例
            _clear_instances_for_testing()
            
            # 捕获输出
            output = StringIO()
            with redirect_stdout(output):
                cfg = get_config_manager(
                    config_path=config_file,
                    watch=False,
                    autosave_delay=0.1
                )
                # 设置一些测试数据
                cfg.test_data = "敏感测试数据"
                cfg.secret_key = "my_secret_key_123"
                cfg.nested = {}
                cfg.nested.password = "password123"
                cfg.nested.api_token = "token_abc_xyz"
                
                # 手动保存
                cfg.save()
            
            captured_output = output.getvalue()
            print("=== 测试输出 ===")
            print(captured_output)
            print("=== 输出结束 ===")
            
            # 验证调用链信息存在
            call_chain_found = "调用链:" in captured_output
            print(f"✓ 调用链信息存在: {call_chain_found}")
            
            # 验证不包含敏感配置数据
            sensitive_data = [
                "敏感测试数据", "secret_key", "my_secret_key_123", 
                "password123", "token_abc_xyz", "'test_data':",
                "__data__': {", "_data内容:"
            ]
            
            data_found = []
            for data in sensitive_data:
                if data in captured_output:
                    data_found.append(data)
            
            if data_found:
                print(f"❌ 错误：输出中包含了配置数据: {data_found}")
                return False
            else:
                print("✓ 成功：输出中不包含配置数据")
            
            # 验证包含基本操作信息但不包含数据
            expected_messages = [
                "检测到标准格式，加载__data__节点",
                "配置加载完成", 
                "开始保存配置",
                "保存结果:"
            ]
            
            missing_messages = []
            for msg in expected_messages:
                if msg not in captured_output:
                    missing_messages.append(msg)
            
            if missing_messages:
                print(f"⚠ 缺少的信息: {missing_messages}")
            else:
                print("✓ 基本操作信息完整")
            
            return len(data_found) == 0 and call_chain_found
            
        finally:
            # 恢复原始开关状态
            cm_module.ENABLE_CALL_CHAIN_DISPLAY = original_switch
            _clear_instances_for_testing()


if __name__ == "__main__":
    print("测试ENABLE_CALL_CHAIN_DISPLAY不显示配置数据")
    print("=" * 50)
    
    result = test_no_config_data_display()
    
    print("\n" + "=" * 50)
    if result:
        print("🎉 测试通过！")
        print("✓ ENABLE_CALL_CHAIN_DISPLAY开启时显示调用链但不显示配置数据")
    else:
        print("❌ 测试失败")
        print("配置数据仍在显示中") 