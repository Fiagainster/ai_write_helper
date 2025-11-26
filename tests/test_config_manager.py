#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""配置管理器单元测试"""

import os
import tempfile
import unittest
from unittest.mock import patch, MagicMock

from ai_write_helper.core.config_manager import ConfigManager


class TestConfigManager(unittest.TestCase):
    """配置管理器测试类"""
    
    def setUp(self):
        """测试前设置"""
        # 创建临时目录作为应用数据目录
        self.temp_dir = tempfile.mkdtemp()
        self.original_env = os.environ.copy()
        
        # 模拟环境变量，使配置管理器使用临时目录
        if os.name == "nt":
            os.environ["APPDATA"] = self.temp_dir
        else:
            os.environ["HOME"] = self.temp_dir
        
        # 保存原始的_get_app_data_dir方法
        self.original_get_app_data_dir = ConfigManager._get_app_data_dir
        
        # 替换_get_app_data_dir方法，使其返回临时目录
        ConfigManager._get_app_data_dir = lambda self: self.temp_dir
        
        # 创建配置管理器实例
        self.config_manager = ConfigManager()
        self.config_manager.temp_dir = self.temp_dir
        
    def tearDown(self):
        """测试后清理"""
        # 恢复原始环境变量
        os.environ.clear()
        os.environ.update(self.original_env)
        
        # 恢复原始方法
        ConfigManager._get_app_data_dir = self.original_get_app_data_dir
        
        # 删除临时文件
        for root, dirs, files in os.walk(self.temp_dir, topdown=False):
            for file in files:
                os.remove(os.path.join(root, file))
            for dir in dirs:
                os.rmdir(os.path.join(root, dir))
        os.rmdir(self.temp_dir)
    
    def test_encrypt_decrypt(self):
        """测试加密和解密功能"""
        # 测试数据
        test_data = "This is a test string for encryption"
        
        # 加密数据
        encrypted_data = self.config_manager.encrypt(test_data)
        
        # 确保加密后的数据与原始数据不同
        self.assertNotEqual(test_data, encrypted_data)
        
        # 解密数据
        decrypted_data = self.config_manager.decrypt(encrypted_data)
        
        # 确保解密后的数据与原始数据相同
        self.assertEqual(test_data, decrypted_data)
    
    def test_save_load_config(self):
        """测试保存和加载配置功能"""
        # 测试配置
        test_config = {
            "api_key": "test_api_key_12345",
            "document_path": "/path/to/document.txt",
            "prompt_template": "Test prompt template",
            "max_tokens": 1000,
            "temperature": 0.8
        }
        
        # 保存配置
        save_result = self.config_manager.save_config(test_config)
        
        # 确保保存成功
        self.assertTrue(save_result)
        
        # 加载配置
        loaded_config = self.config_manager.load_config()
        
        # 检查关键配置项是否正确加载
        self.assertEqual(test_config["api_key"], loaded_config["api_key"])
        self.assertEqual(test_config["document_path"], loaded_config["document_path"])
        self.assertEqual(test_config["prompt_template"], loaded_config["prompt_template"])
        self.assertEqual(test_config["max_tokens"], loaded_config["max_tokens"])
        self.assertEqual(test_config["temperature"], loaded_config["temperature"])
    
    def test_load_default_config(self):
        """测试加载默认配置功能"""
        # 确保配置文件不存在
        if os.path.exists(self.config_manager.config_file):
            os.remove(self.config_manager.config_file)
        
        # 加载配置
        config = self.config_manager.load_config()
        
        # 检查是否包含默认配置项
        self.assertIn("api_key", config)
        self.assertIn("document_path", config)
        self.assertIn("prompt_template", config)
        self.assertIn("max_tokens", config)
        self.assertIn("temperature", config)
    
    def test_validate_config(self):
        """测试配置验证功能"""
        # 创建临时文本文件用于测试
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as temp_file:
            temp_file_path = temp_file.name
        
        try:
            # 有效的配置
            valid_config = {
                "document_path": temp_file_path,
                "max_tokens": 1000,
                "temperature": 0.7
            }
            errors = self.config_manager.validate_config(valid_config)
            self.assertEqual(len(errors), 0)
            
            # 无效的文档路径
            invalid_path_config = {
                "document_path": "/path/to/nonexistent/file.txt"
            }
            errors = self.config_manager.validate_config(invalid_path_config)
            self.assertIn("document_path", errors)
            
            # 无效的文件格式
            with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as temp_csv:
                temp_csv_path = temp_csv.name
            
            try:
                invalid_format_config = {
                    "document_path": temp_csv_path
                }
                errors = self.config_manager.validate_config(invalid_format_config)
                self.assertIn("document_path", errors)
            finally:
                os.unlink(temp_csv_path)
            
            # 无效的max_tokens
            invalid_tokens_config = {
                "max_tokens": "not_an_integer"
            }
            errors = self.config_manager.validate_config(invalid_tokens_config)
            self.assertIn("max_tokens", errors)
            
            # 超出范围的max_tokens
            out_of_range_tokens_config = {
                "max_tokens": 5000
            }
            errors = self.config_manager.validate_config(out_of_range_tokens_config)
            self.assertIn("max_tokens", errors)
            
            # 无效的temperature
            invalid_temp_config = {
                "temperature": "not_a_number"
            }
            errors = self.config_manager.validate_config(invalid_temp_config)
            self.assertIn("temperature", errors)
            
            # 超出范围的temperature
            out_of_range_temp_config = {
                "temperature": 3.0
            }
            errors = self.config_manager.validate_config(out_of_range_temp_config)
            self.assertIn("temperature", errors)
            
        finally:
            os.unlink(temp_file_path)
    
    def test_update_recent_documents(self):
        """测试更新最近文档列表功能"""
        # 创建测试文档路径
        doc1 = "/path/to/doc1.txt"
        doc2 = "/path/to/doc2.txt"
        doc3 = "/path/to/doc3.txt"
        
        # 更新文档1
        self.config_manager._update_recent_documents(doc1)
        config = self.config_manager.load_config()
        self.assertEqual(config["recent_documents"], [doc1])
        
        # 更新文档2
        self.config_manager._update_recent_documents(doc2)
        config = self.config_manager.load_config()
        self.assertEqual(config["recent_documents"], [doc2, doc1])
        
        # 重新更新文档1，应该移到列表开头
        self.config_manager._update_recent_documents(doc1)
        config = self.config_manager.load_config()
        self.assertEqual(config["recent_documents"], [doc1, doc2])
        
        # 更新文档3
        self.config_manager._update_recent_documents(doc3)
        config = self.config_manager.load_config()
        self.assertEqual(config["recent_documents"], [doc3, doc1, doc2])
    
    def test_reset_config(self):
        """测试重置配置功能"""
        # 保存非默认配置
        custom_config = {
            "api_key": "custom_key",
            "document_path": "/custom/path.txt",
            "prompt_template": "Custom template"
        }
        self.config_manager.save_config(custom_config)
        
        # 重置配置
        reset_result = self.config_manager.reset_config()
        self.assertTrue(reset_result)
        
        # 加载配置并验证是否已重置
        reset_config = self.config_manager.load_config()
        self.assertEqual(reset_config["api_key"], "")  # 默认值为空
        self.assertNotEqual(reset_config["prompt_template"], "Custom template")


if __name__ == "__main__":
    unittest.main()