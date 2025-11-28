#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
光标位置测试脚本
用于测试不同文档格式的光标位置获取和插入功能
"""

import os
import sys

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ai_write_helper.services.document import DocumentService
from ai_write_helper.core.config_manager import ConfigManager


def test_cursor_insertion():
    """测试光标插入功能"""
    # 创建配置管理器实例
    config_manager = ConfigManager()
    
    # 创建文档服务实例
    document_service = DocumentService(config_manager)
    
    # 测试文本文件
    test_txt_file = "test_cursor.txt"
    
    # 写入初始内容
    initial_content = "这是一个测试文档。\n光标应该在这里：[CURSOR]\n这是文档的结尾。"
    with open(test_txt_file, 'w', encoding='utf-8') as f:
        f.write(initial_content)
    
    print(f"初始文本文件内容：\n{initial_content}")
    
    # 测试光标插入
    insert_content = "这是插入的内容。"
    
    # 读取文件内容
    with open(test_txt_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 查找光标标记
    cursor_pos = content.find("[CURSOR]")
    if cursor_pos != -1:
        # 在光标位置插入内容
        new_content = content[:cursor_pos] + insert_content + content[cursor_pos+8:]
        
        print(f"\n插入后的内容：\n{new_content}")
        
        # 写入新内容
        with open(test_txt_file, 'w', encoding='utf-8') as f:
            f.write(new_content)
    
    # 清理测试文件
    if os.path.exists(test_txt_file):
        os.remove(test_txt_file)
    
    print("\n测试完成！")


if __name__ == "__main__":
    test_cursor_insertion()
