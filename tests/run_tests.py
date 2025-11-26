#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""测试运行器

该脚本用于运行所有单元测试，提供简单的命令行接口。
"""

import os
import sys
import unittest
import argparse
from unittest import TestLoader, TextTestRunner


# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def run_all_tests(verbosity: int = 2, pattern: str = "test_*.py"):
    """运行所有测试
    
    Args:
        verbosity: 输出详细程度 (0, 1, 2)
        pattern: 测试文件匹配模式
        
    Returns:
        int: 测试结果状态码，0表示所有测试通过，1表示有测试失败
    """
    # 获取测试目录
    test_dir = os.path.dirname(os.path.abspath(__file__))
    
    print(f"运行测试目录: {test_dir}")
    print(f"测试文件匹配模式: {pattern}")
    print("=" * 70)
    
    # 创建测试加载器
    loader = TestLoader()
    
    # 发现所有测试
    suite = loader.discover(test_dir, pattern=pattern)
    
    # 创建测试运行器
    runner = TextTestRunner(verbosity=verbosity)
    
    # 运行测试
    result = runner.run(suite)
    
    # 打印测试统计信息
    print("=" * 70)
    print(f"测试总数: {result.testsRun}")
    print(f"通过测试: {result.testsRun - len(result.failures) - len(result.errors)}")
    
    if result.failures:
        print(f"失败测试: {len(result.failures)}")
        for test, error in result.failures:
            print(f"  - {test.id()}")
    
    if result.errors:
        print(f"错误测试: {len(result.errors)}")
        for test, error in result.errors:
            print(f"  - {test.id()}")
    
    print("=" * 70)
    
    # 返回状态码
    return 0 if result.wasSuccessful() else 1


def run_specific_test(test_name: str, verbosity: int = 2):
    """运行特定的测试
    
    Args:
        test_name: 测试名称，可以是模块名、类名或方法名
        verbosity: 输出详细程度
        
    Returns:
        int: 测试结果状态码
    """
    # 获取测试目录
    test_dir = os.path.dirname(os.path.abspath(__file__))
    
    print(f"运行特定测试: {test_name}")
    print("=" * 70)
    
    try:
        # 尝试导入测试模块
        parts = test_name.split(".")
        
        if len(parts) == 1:
            # 模块名
            module_name = f"tests.{parts[0]}"
            module = __import__(module_name, fromlist=["*"])
            suite = TestLoader().loadTestsFromModule(module)
        elif len(parts) == 2:
            # 模块名.类名
            module_name = f"tests.{parts[0]}"
            module = __import__(module_name, fromlist=["*"])
            test_class = getattr(module, parts[1])
            suite = TestLoader().loadTestsFromTestCase(test_class)
        elif len(parts) == 3:
            # 模块名.类名.方法名
            module_name = f"tests.{parts[0]}"
            module = __import__(module_name, fromlist=["*"])
            test_class = getattr(module, parts[1])
            suite = TestLoader().loadTestsFromName(parts[2], test_class)
        else:
            print(f"无效的测试名称格式: {test_name}")
            print("请使用以下格式之一:")
            print("  - 模块名 (如: test_config_manager)")
            print("  - 模块名.类名 (如: test_config_manager.TestConfigManager)")
            print("  - 模块名.类名.方法名 (如: test_config_manager.TestConfigManager.test_encrypt_decrypt)")
            return 1
        
        # 运行测试
        runner = TextTestRunner(verbosity=verbosity)
        result = runner.run(suite)
        
        # 打印测试统计信息
        print("=" * 70)
        print(f"测试总数: {result.testsRun}")
        print(f"通过测试: {result.testsRun - len(result.failures) - len(result.errors)}")
        
        if result.failures:
            print(f"失败测试: {len(result.failures)}")
            for test, error in result.failures:
                print(f"  - {test.id()}")
        
        if result.errors:
            print(f"错误测试: {len(result.errors)}")
            for test, error in result.errors:
                print(f"  - {test.id()}")
        
        print("=" * 70)
        
        return 0 if result.wasSuccessful() else 1
        
    except ImportError as e:
        print(f"无法导入测试模块: {e}")
        return 1
    except AttributeError as e:
        print(f"无法找到测试类或方法: {e}")
        return 1
    except Exception as e:
        print(f"运行测试时出错: {e}")
        return 1


def main():
    """主函数"""
    # 创建命令行参数解析器
    parser = argparse.ArgumentParser(description="运行AI写作助手的单元测试")
    
    # 添加参数
    parser.add_argument(
        "test_name", 
        nargs="?", 
        default=None,
        help="要运行的特定测试名称（可选）"
    )
    
    parser.add_argument(
        "-v", "--verbosity",
        type=int,
        choices=[0, 1, 2],
        default=2,
        help="测试输出详细程度 (默认: 2)"
    )
    
    parser.add_argument(
        "--pattern",
        type=str,
        default="test_*.py",
        help="测试文件匹配模式 (默认: test_*.py)"
    )
    
    # 解析参数
    args = parser.parse_args()
    
    # 运行测试
    if args.test_name:
        exit_code = run_specific_test(args.test_name, args.verbosity)
    else:
        exit_code = run_all_tests(args.verbosity, args.pattern)
    
    # 退出
    sys.exit(exit_code)


if __name__ == "__main__":
    main()