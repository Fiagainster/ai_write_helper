#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""文档服务单元测试"""

import os
import tempfile
import unittest
from unittest.mock import patch, MagicMock

from ai_write_helper.services.document import DocumentService


class TestDocumentService(unittest.TestCase):
    """文档服务测试类"""
    
    def setUp(self):
        """测试前设置"""
        # 创建文档服务实例
        self.document_service = DocumentService()
        
        # 创建临时目录
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """测试后清理"""
        # 删除临时目录中的所有文件
        for root, dirs, files in os.walk(self.temp_dir, topdown=False):
            for file in files:
                os.remove(os.path.join(root, file))
            for dir in dirs:
                os.rmdir(os.path.join(root, dir))
        os.rmdir(self.temp_dir)
    
    def test_read_text_file(self):
        """测试读取文本文件"""
        # 创建临时文本文件
        test_content = "这是测试文本内容\n第二行内容"
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False, dir=self.temp_dir, encoding="utf-8") as temp_file:
            temp_file.write(test_content)
            temp_file_path = temp_file.name
        
        try:
            # 读取文件
            content = self.document_service.read_document(temp_file_path)
            
            # 验证内容
            self.assertEqual(content, test_content)
        finally:
            os.unlink(temp_file_path)
    
    def test_read_markdown_file(self):
        """测试读取Markdown文件"""
        # 创建临时Markdown文件
        test_content = "# 测试标题\n\n这是**测试**内容"
        with tempfile.NamedTemporaryFile(suffix=".md", delete=False, dir=self.temp_dir, encoding="utf-8") as temp_file:
            temp_file.write(test_content)
            temp_file_path = temp_file.name
        
        try:
            # 读取文件
            content = self.document_service.read_document(temp_file_path)
            
            # 验证内容
            self.assertEqual(content, test_content)
        finally:
            os.unlink(temp_file_path)
    
    def test_write_text_file(self):
        """测试写入文本文件"""
        # 创建临时文件路径
        temp_file_path = os.path.join(self.temp_dir, "test_write.txt")
        test_content = "这是要写入的内容\n新的一行"
        
        # 写入文件
        self.document_service.write_document(temp_file_path, test_content)
        
        # 验证文件存在
        self.assertTrue(os.path.exists(temp_file_path))
        
        # 验证内容
        with open(temp_file_path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertEqual(content, test_content)
    
    def test_write_markdown_file(self):
        """测试写入Markdown文件"""
        # 创建临时文件路径
        temp_file_path = os.path.join(self.temp_dir, "test_write.md")
        test_content = "# 新标题\n\n这是Markdown内容"
        
        # 写入文件
        self.document_service.write_document(temp_file_path, test_content)
        
        # 验证文件存在
        self.assertTrue(os.path.exists(temp_file_path))
        
        # 验证内容
        with open(temp_file_path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertEqual(content, test_content)
    
    def test_append_to_file(self):
        """测试追加内容到文件"""
        # 创建临时文件
        initial_content = "初始内容\n"
        append_content = "追加的内容"
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False, dir=self.temp_dir, encoding="utf-8") as temp_file:
            temp_file.write(initial_content)
            temp_file_path = temp_file.name
        
        try:
            # 追加内容
            self.document_service.write_document(temp_file_path, append_content, mode="append")
            
            # 验证内容
            with open(temp_file_path, "r", encoding="utf-8") as f:
                content = f.read()
            self.assertEqual(content, initial_content + append_content)
        finally:
            os.unlink(temp_file_path)
    
    def test_path_validation(self):
        """测试路径验证功能"""
        # 测试有效路径
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False, dir=self.temp_dir) as temp_file:
            valid_path = temp_file.name
        
        try:
            # 应该通过验证
            self.assertTrue(self.document_service.validate_path(valid_path))
            
            # 测试无效路径
            invalid_path = os.path.join(self.temp_dir, "nonexistent_file.txt")
            self.assertFalse(self.document_service.validate_path(invalid_path))
            
            # 测试目录路径（不是文件）
            dir_path = self.temp_dir
            self.assertFalse(self.document_service.validate_path(dir_path))
            
            # 测试不支持的文件格式
            with tempfile.NamedTemporaryFile(suffix=".csv", delete=False, dir=self.temp_dir) as temp_file:
                unsupported_format_path = temp_file.name
            
            try:
                self.assertFalse(self.document_service.validate_path(unsupported_format_path))
            finally:
                os.unlink(unsupported_format_path)
        finally:
            os.unlink(valid_path)
    
    def test_get_file_info(self):
        """测试获取文件信息功能"""
        # 创建临时文件
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False, dir=self.temp_dir, encoding="utf-8") as temp_file:
            temp_file.write("测试内容")
            temp_file_path = temp_file.name
        
        try:
            # 获取文件信息
            info = self.document_service.get_file_info(temp_file_path)
            
            # 验证信息
            self.assertIn("path", info)
            self.assertIn("name", info)
            self.assertIn("size", info)
            self.assertIn("extension", info)
            self.assertIn("created_at", info)
            self.assertIn("modified_at", info)
            
            self.assertEqual(info["extension"], ".txt")
            self.assertEqual(info["size"], 4)  # "测试内容"的字节数取决于编码
        finally:
            os.unlink(temp_file_path)
    
    @patch("ai_write_helper.services.document.DocumentService._read_docx")
    def test_read_docx_file(self, mock_read_docx):
        """测试读取DOCX文件"""
        # 模拟_read_docx方法的返回值
        mock_read_docx.return_value = "DOCX文件内容"
        
        # 创建临时DOCX文件路径
        temp_file_path = os.path.join(self.temp_dir, "test.docx")
        
        # 创建空文件
        open(temp_file_path, "w").close()
        
        try:
            # 读取文件
            content = self.document_service.read_document(temp_file_path)
            
            # 验证内容
            self.assertEqual(content, "DOCX文件内容")
            
            # 验证调用了_read_docx方法
            mock_read_docx.assert_called_once_with(temp_file_path)
        finally:
            os.unlink(temp_file_path)
    
    def test_file_not_found(self):
        """测试文件不存在的情况"""
        # 不存在的文件路径
        nonexistent_path = os.path.join(self.temp_dir, "nonexistent.txt")
        
        # 尝试读取不存在的文件，应该抛出异常
        with self.assertRaises(Exception):
            self.document_service.read_document(nonexistent_path)
    
    def test_invalid_mode(self):
        """测试无效的写入模式"""
        # 创建临时文件
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False, dir=self.temp_dir) as temp_file:
            temp_file_path = temp_file.name
        
        try:
            # 尝试使用无效的模式写入，应该抛出异常
            with self.assertRaises(ValueError):
                self.document_service.write_document(temp_file_path, "content", mode="invalid_mode")
        finally:
            os.unlink(temp_file_path)


if __name__ == "__main__":
    unittest.main()