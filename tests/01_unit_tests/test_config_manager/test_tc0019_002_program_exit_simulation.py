# tests/01_unit_tests/test_config_manager/test_tc0019_002_program_exit_simulation.py
from __future__ import annotations
from datetime import datetime

import subprocess
import sys
import tempfile
import os
import time
import pytest


def test_program_exit_without_hanging():
    """测试程序退出时不会挂起（模拟真实使用场景）"""
    
    # 创建测试脚本
    test_script = '''
import time
import tempfile
import os
from config_manager import get_config_manager

def main():
    """模拟用户程序的主函数"""
    # 创建临时配置文件
    with tempfile.TemporaryDirectory() as temp_dir:
        config_path = os.path.join(temp_dir, "test_config.yaml")
        
        # 创建配置管理器，启用文件监视器
        config = get_config_manager(
            config_path=config_path,
            test_mode=True,
            auto_create=True,
            watch=True
        )
        
        # 模拟一些工作
        config.set('test_value', 'hello')
        print(f"Config test_value: {config.get('test_value')}")
        
        # 模拟短暂工作
        time.sleep(1.0)
        
        # 手动清理以确保线程正确停止
        if hasattr(config, '_cleanup'):
            config._cleanup()
        
        print("✅ 程序正常结束")

if __name__ == "__main__":
    main()
'''
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(test_script)
        script_path = f.name
    
    try:
        # 运行测试脚本，设置较短的超时时间
        start_time = time.time()
        result = subprocess.run(
            [sys.executable, script_path],
            capture_output=True,
            text=True,
            timeout=10.0  # 10秒超时，正常情况下应该在几秒内完成
        )
        end_time = time.time()
        
        execution_time = end_time - start_time
        print(f"脚本执行时间: {execution_time:.2f}秒")
        print(f"脚本输出: {result.stdout}")
        if result.stderr:
            print(f"脚本错误: {result.stderr}")
        
        # 验证程序正常退出
        assert result.returncode == 0, f"程序退出码应该为0，实际为{result.returncode}"
        
        # 验证执行时间合理（应该在5秒内完成）
        assert execution_time < 5.0, f"程序执行时间过长: {execution_time:.2f}秒，可能存在线程挂起问题"
        
        # 验证输出包含期望内容
        assert "✅ 程序正常结束" in result.stdout, "程序应该正常执行完成"
        assert "Config test_value: hello" in result.stdout, "配置功能应该正常工作"
        
    except subprocess.TimeoutExpired:
        pytest.fail("程序执行超时，可能存在线程挂起问题")
        
    finally:
        # 清理测试脚本
        if os.path.exists(script_path):
            os.unlink(script_path)


def test_multiple_config_managers_program_exit():
    """测试多个配置管理器实例时程序正常退出"""
    
    test_script = '''
import time
import tempfile
import os
from config_manager import get_config_manager

def main():
    """模拟使用多个配置管理器实例的程序"""
    configs = []
    temp_dirs = []
    
    try:
        # 创建多个配置管理器实例
        for i in range(3):
            temp_dir = tempfile.mkdtemp()
            temp_dirs.append(temp_dir)
            config_path = os.path.join(temp_dir, f"config_{i}.yaml")
            
            config = get_config_manager(
                config_path=config_path,
                test_mode=True,
                auto_create=True,
                watch=True
            )
            config.set(f'value_{i}', f'test_value_{i}')
            configs.append(config)
        
        print(f"创建了 {len(configs)} 个配置管理器实例")
        
        # 模拟一些工作
        time.sleep(1.0)
        
        # 手动清理所有配置管理器
        for config in configs:
            if hasattr(config, '_cleanup'):
                config._cleanup()
        
        print("✅ 多实例程序正常结束")
        
    finally:
        # 清理临时目录
        import shutil
        for temp_dir in temp_dirs:
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)

if __name__ == "__main__":
    main()
'''
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(test_script)
        script_path = f.name
    
    try:
        start_time = time.time()
        result = subprocess.run(
            [sys.executable, script_path],
            capture_output=True,
            text=True,
            timeout=15.0  # 更长的超时时间，因为创建多个实例
        )
        end_time = time.time()
        
        execution_time = end_time - start_time
        print(f"多实例脚本执行时间: {execution_time:.2f}秒")
        print(f"脚本输出: {result.stdout}")
        if result.stderr:
            print(f"脚本错误: {result.stderr}")
        
        # 验证程序正常退出
        assert result.returncode == 0, f"程序退出码应该为0，实际为{result.returncode}"
        
        # 验证执行时间合理
        assert execution_time < 10.0, f"多实例程序执行时间过长: {execution_time:.2f}秒"
        
        # 验证输出
        assert "✅ 多实例程序正常结束" in result.stdout, "多实例程序应该正常执行完成"
        assert "创建了 3 个配置管理器实例" in result.stdout, "应该成功创建多个实例"
        
    except subprocess.TimeoutExpired:
        pytest.fail("多实例程序执行超时，可能存在线程挂起问题")
        
    finally:
        if os.path.exists(script_path):
            os.unlink(script_path)


def test_signal_handling_graceful_shutdown():
    """测试信号处理和优雅关闭"""
    
    test_script = '''
import signal
import time
import tempfile
import os
from config_manager import get_config_manager

# 全局配置管理器引用，供信号处理器使用
global_config = None

def signal_handler(signum, frame):
    """信号处理器"""
    global global_config
    print(f"收到信号 {signum}，开始优雅关闭...")
    # 手动清理配置管理器
    if global_config and hasattr(global_config, '_cleanup'):
        global_config._cleanup()
    print("✅ 信号处理完成，程序即将退出")
    exit(0)

def main():
    """模拟处理信号的程序"""
    global global_config
    
    # 注册信号处理器
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    
    with tempfile.TemporaryDirectory() as temp_dir:
        config_path = os.path.join(temp_dir, "signal_test_config.yaml")
        
        config = get_config_manager(
            config_path=config_path,
            test_mode=True,
            auto_create=True,
            watch=True
        )
        global_config = config  # 设置全局引用
        
        config.set('signal_test', 'active')
        print("配置管理器已启动，等待信号...")
        
        # 模拟程序运行，等待信号
        try:
            time.sleep(30)  # 在测试中会被信号中断
        except KeyboardInterrupt:
            print("收到键盘中断信号")
        
        print("✅ 程序正常结束")

if __name__ == "__main__":
    main()
'''
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(test_script)
        script_path = f.name
    
    try:
        # 启动程序
        import signal
        process = subprocess.Popen(
            [sys.executable, script_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # 等待程序启动
        time.sleep(2.0)
        
        # 发送SIGTERM信号
        process.send_signal(signal.SIGTERM)
        
        # 等待程序退出
        try:
            stdout, stderr = process.communicate(timeout=5.0)
            execution_time = 5.0  # 最大等待时间
        except subprocess.TimeoutExpired:
            # 强制终止
            process.kill()
            stdout, stderr = process.communicate()
            pytest.fail("程序未能在信号后及时退出")
        
        print(f"信号测试输出: {stdout}")
        if stderr:
            print(f"信号测试错误: {stderr}")
        
        # 验证程序正常响应信号
        assert process.returncode == 0, f"程序应该正常退出，退出码: {process.returncode}"
        assert "收到信号" in stdout, "程序应该收到并处理信号"
        
    finally:
        if os.path.exists(script_path):
            os.unlink(script_path)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])