#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""配置管理器模块

该模块负责配置信息的加密存储、加载和管理，使用AES加密算法保护敏感信息。
"""

import os
import json
import logging
import base64
from pathlib import Path
from typing import Dict, Any, Optional

# 导入加密相关库
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.fernet import Fernet
from cryptography.hazmat.backends import default_backend


class ConfigManager:
    """配置管理器类，负责配置信息的加密存储和管理"""
    
    # 配置文件路径
    def __init__(self):
        """初始化配置管理器"""
        self.logger = logging.getLogger("ai_write_helper.config")
        
        # 获取应用数据目录
        self.app_data_dir = self._get_app_data_dir()
        self.config_file = os.path.join(self.app_data_dir, "config.json")
        self.key_file = os.path.join(self.app_data_dir, "secret.key")
        
        # 确保应用数据目录存在
        os.makedirs(self.app_data_dir, exist_ok=True)
        
        # 初始化加密密钥
        self.fernet = None
        self._initialize_encryption()
        
        # 默认配置
        self.default_config = {
            "api_key": "",
            "document_path": "",
            "recent_documents": [],
            "prompt_template": "请基于以下文档内容和新信息生成补充内容：\n\n文档内容：{document_content}\n\n新信息：{selected_text}\n\n请保持内容风格一致，逻辑连贯，并确保新增内容与原有内容自然衔接。",
            "max_tokens": 2000,
            "temperature": 0.7,
            "auto_save": True,
            "theme": "light",
            "start_minimized": False,
            "listen_enabled": True
        }
    
    def _get_app_data_dir(self) -> str:
        """获取应用数据目录
        
        Returns:
            str: 应用数据目录路径
        """
        # 根据操作系统获取应用数据目录
        if os.name == "nt":  # Windows
            app_data = os.getenv("APPDATA")
            return os.path.join(app_data, "AIWriteHelper")
        else:  # macOS, Linux
            home = os.path.expanduser("~")
            if os.uname().sysname == "Darwin":  # macOS
                return os.path.join(home, "Library", "Application Support", "AIWriteHelper")
            else:  # Linux
                return os.path.join(home, ".config", "aiwritehelper")
    
    def _initialize_encryption(self):
        """初始化加密系统"""
        try:
            # 尝试加载现有密钥
            if os.path.exists(self.key_file):
                with open(self.key_file, "rb") as f:
                    key = f.read()
            else:
                # 生成新密钥
                key = self._generate_key()
                # 保存密钥到文件
                with open(self.key_file, "wb") as f:
                    f.write(key)
                # 设置文件权限（仅限当前用户读取）
                if os.name == "nt":  # Windows
                    import win32security
                    import win32file
                    import win32api
                    # 设置Windows文件权限
                    security_descriptor = win32security.GetFileSecurity(
                        self.key_file, win32security.DACL_SECURITY_INFORMATION
                    )
                    dacl = win32security.ACL()
                    user_sid = win32security.GetTokenInformation(
                        win32security.OpenProcessToken(
                            win32api.GetCurrentProcess(), win32security.TOKEN_QUERY
                        ),
                        win32security.TokenUser
                    )[0]
                    dacl.AddAccessAllowedAce(
                        win32security.ACL_REVISION, 
                        win32file.GENERIC_READ | win32file.GENERIC_WRITE, 
                        user_sid
                    )
                    security_descriptor.SetSecurityDescriptorDacl(True, dacl, False)
                    win32security.SetFileSecurity(
                        self.key_file, 
                        win32security.DACL_SECURITY_INFORMATION, 
                        security_descriptor
                    )
                else:  # Unix-like
                    # 设置权限为600（仅所有者可读写）
                    os.chmod(self.key_file, 0o600)
            
            # 初始化Fernet加密器
            self.fernet = Fernet(key)
            self.logger.info("加密系统初始化成功")
            
        except Exception as e:
            self.logger.error(f"初始化加密系统失败: {str(e)}")
            raise
    
    def _generate_key(self) -> bytes:
        """生成加密密钥
        
        Returns:
            bytes: 生成的密钥
        """
        # 生成随机盐值
        salt = os.urandom(16)
        
        # 使用固定的应用标识作为密码，结合随机盐值生成密钥
        # 注意：在生产环境中，可能需要考虑更复杂的密钥派生机制
        password = b"AIWriteHelperSecureAppKey"
        
        # 使用PBKDF2生成密钥
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=default_backend()
        )
        key = base64.urlsafe_b64encode(kdf.derive(password))
        
        return key
    
    def encrypt(self, data: str) -> str:
        """加密数据
        
        Args:
            data: 要加密的字符串
            
        Returns:
            str: 加密后的base64编码字符串
        """
        if not self.fernet:
            raise ValueError("加密系统未初始化")
        
        try:
            encrypted_data = self.fernet.encrypt(data.encode('utf-8'))
            return encrypted_data.decode('utf-8')
        except Exception as e:
            self.logger.error(f"加密数据失败: {str(e)}")
            raise
    
    def decrypt(self, encrypted_data: str) -> str:
        """解密数据
        
        Args:
            encrypted_data: 加密的base64编码字符串
            
        Returns:
            str: 解密后的字符串
        """
        if not self.fernet:
            raise ValueError("加密系统未初始化")
        
        try:
            decrypted_data = self.fernet.decrypt(encrypted_data.encode('utf-8'))
            return decrypted_data.decode('utf-8')
        except Exception as e:
            self.logger.error(f"解密数据失败: {str(e)}")
            raise
    
    def load_config(self) -> Dict[str, Any]:
        """加载配置
        
        Returns:
            Dict[str, Any]: 配置字典
        """
        self.logger.info(f"加载配置文件: {self.config_file}")
        
        # 如果配置文件不存在，返回默认配置
        if not os.path.exists(self.config_file):
            self.logger.warning("配置文件不存在，使用默认配置")
            return self.default_config.copy()
        
        try:
            # 读取配置文件
            with open(self.config_file, "r", encoding="utf-8") as f:
                config = json.load(f)
            
            # 解密敏感信息
            if "api_key_encrypted" in config:
                try:
                    config["api_key"] = self.decrypt(config["api_key_encrypted"])
                except Exception as e:
                    self.logger.error(f"解密API密钥失败: {str(e)}")
                    config["api_key"] = ""
                # 移除加密后的字段
                del config["api_key_encrypted"]
            
            # 合并默认配置，确保所有必要的配置项都存在
            merged_config = self.default_config.copy()
            merged_config.update(config)
            
            self.logger.info("配置加载成功")
            return merged_config
            
        except json.JSONDecodeError as e:
            self.logger.error(f"解析配置文件失败: {str(e)}")
            return self.default_config.copy()
        except Exception as e:
            self.logger.error(f"加载配置失败: {str(e)}")
            return self.default_config.copy()
    
    def save_config(self, config: Dict[str, Any], update_recent: bool = True) -> bool:
        """保存配置
        
        Args:
            config: 要保存的配置字典
            update_recent: 是否更新最近文档列表（避免循环调用）
            
        Returns:
            bool: 是否保存成功
        """
        self.logger.info(f"保存配置文件: {self.config_file}")
        temp_file = self.config_file + ".tmp"
        
        try:
            # 创建配置副本，避免修改原始配置
            config_copy = config.copy()
            
            # 加密敏感信息
            if "api_key" in config_copy and config_copy["api_key"]:
                config_copy["api_key_encrypted"] = self.encrypt(config_copy["api_key"])
                # 移除明文API密钥
                del config_copy["api_key"]
            
            # 保存配置到文件（使用临时文件确保原子性）
            with open(temp_file, "w", encoding="utf-8") as f:
                json.dump(config_copy, f, ensure_ascii=False, indent=2)
            
            # 原子性地替换配置文件
            if os.name == "nt":  # Windows
                # Windows上需要先删除目标文件
                if os.path.exists(self.config_file):
                    os.remove(self.config_file)
                os.rename(temp_file, self.config_file)
            else:  # Unix-like
                os.replace(temp_file, self.config_file)
            
            # 更新最近使用的文档列表（避免循环调用）
            if update_recent and "document_path" in config and config["document_path"]:
                self._update_recent_documents(config["document_path"])
            
            self.logger.info("配置保存成功")
            return True
            
        except Exception as e:
            self.logger.error(f"保存配置失败: {str(e)}")
            # 清理临时文件
            if os.path.exists(temp_file):
                os.remove(temp_file)
            return False
    
    def _update_recent_documents(self, document_path: str):
        """更新最近使用的文档列表
        
        Args:
            document_path: 文档路径
        """
        try:
            # 加载当前配置
            config = self.load_config()
            recent_docs = config.get("recent_documents", [])
            
            # 如果文档已存在，移除旧的条目
            if document_path in recent_docs:
                recent_docs.remove(document_path)
            
            # 添加到列表开头
            recent_docs.insert(0, document_path)
            
            # 限制列表长度
            max_recent = 10
            if len(recent_docs) > max_recent:
                recent_docs = recent_docs[:max_recent]
            
            # 更新配置
            config["recent_documents"] = recent_docs
            
            # 保存配置，设置update_recent=False避免循环调用
            self.save_config(config, update_recent=False)
            
        except Exception as e:
            self.logger.error(f"更新最近文档列表失败: {str(e)}")
    
    def validate_config(self, config: Dict[str, Any]) -> Dict[str, str]:
        """验证配置
        
        Args:
            config: 要验证的配置字典
            
        Returns:
            Dict[str, str]: 验证错误信息，键为配置项，值为错误信息
        """
        errors = {}
        
        # 验证文档路径
        if "document_path" in config and config["document_path"]:
            if not os.path.exists(config["document_path"]):
                errors["document_path"] = "文档路径不存在"
            elif not os.path.isfile(config["document_path"]):
                errors["document_path"] = "指定路径不是文件"
            else:
                # 验证文件扩展名
                ext = os.path.splitext(config["document_path"])[1].lower()
                supported_extensions = [".txt", ".md", ".docx"]
                if ext not in supported_extensions:
                    errors["document_path"] = f"不支持的文件格式，仅支持: {', '.join(supported_extensions)}"
        
        # 验证模型参数
        if "max_tokens" in config:
            try:
                max_tokens = int(config["max_tokens"])
                if max_tokens < 1 or max_tokens > 4000:
                    errors["max_tokens"] = "max_tokens必须在1到4000之间"
            except ValueError:
                errors["max_tokens"] = "max_tokens必须是整数"
        
        if "temperature" in config:
            try:
                temperature = float(config["temperature"])
                if temperature < 0 or temperature > 2:
                    errors["temperature"] = "temperature必须在0到2之间"
            except ValueError:
                errors["temperature"] = "temperature必须是数字"
        
        return errors
    
    def reset_config(self) -> bool:
        """重置配置到默认值
        
        Returns:
            bool: 是否重置成功
        """
        self.logger.info("重置配置到默认值")
        
        try:
            # 保存默认配置
            return self.save_config(self.default_config.copy())
        except Exception as e:
            self.logger.error(f"重置配置失败: {str(e)}")
            return False
    
    def get_config_path(self) -> str:
        """获取配置文件路径
        
        Returns:
            str: 配置文件路径
        """
        return self.config_file