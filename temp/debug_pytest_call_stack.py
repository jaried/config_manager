#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试在pytest环境下调用栈的内容
"""

import os
import sys
import tempfile
import inspect

# 添加src路径
src_path = os.path.join(os.path.dirname(__file__), '..', 'src')
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from config_manager.core.call_chain import CallChainTracker

def debug_call_stack():
    """调试调用栈内容"""
    print("=== 调试调用栈内容 ===")
    
    # 获取调用栈
    stack = inspect.stack()
    print(f"调用栈长度: {len(stack)}")
    
    # 显示前10个调用栈帧
    for i, frame_info in enumerate(stack[:10]):
        print(f"\n--- 帧 {i} ---")
        print(f"文件名: {frame_info.filename}")
        print(f"函数名: {frame_info.function}")
        print(f"行号: {frame_info.lineno}")
        print(f"模块名: {frame_info.frame.f_globals.get('__name__', 'unknown')}")
        
        # 检查是否是pytest相关
        if 'pytest' in frame_info.filename.lower():
            print("  -> 这是pytest相关帧")
        if 'test' in frame_info.filename.lower():
            print("  -> 这是测试相关帧")
    
    # 创建调用链追踪器并测试
    tracker = CallChainTracker()
    call_chain = tracker.get_call_chain()
    print(f"\n=== 调用链结果 ===")
    print(f"调用链: {call_chain}")
    
    # 手动分析调用栈
    print(f"\n=== 手动分析调用栈 ===")
    call_parts = []
    
    # 从最后一个开始（最早的调用），显示所有调用
    # 反转顺序以正确显示调用关系：调用者->被调用者
    for i in range(len(stack) - 1, 0, -1):
        frame_info = stack[i]
        filename = frame_info.filename
        function_name = frame_info.function
        line_number = frame_info.lineno
        module_name = frame_info.frame.f_globals.get('__name__', 'unknown')
        
        # 跳过pytest内部帧
        if 'pytest' in filename.lower() or 'pytest' in module_name.lower():
            continue
            
        # 跳过测试框架内部帧
        if 'test' in filename.lower() and 'config_manager' not in filename:
            continue
            
        call_info = f"[{len(stack) - i:02d}|M:{module_name}|P:{os.path.basename(filename)}|F:{function_name}:{line_number}]"
        call_parts.append(call_info)
        print(f"添加调用信息: {call_info}")
    
    if call_parts:
        manual_chain = " -> ".join(call_parts)
        print(f"\n手动构建的调用链: {manual_chain}")
    else:
        print("\n没有找到有效的调用信息")

if __name__ == "__main__":
    debug_call_stack() 