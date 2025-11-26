#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""日志管理模块

该模块负责配置和管理应用的日志系统，支持多级别日志记录、日志轮转等功能。
"""

import os
import logging
import logging.handlers
from pathlib import Path
from typing import Optional, Dict, Any


class LogManager:
    """日志管理器类，负责配置和管理应用的日志系统"""
    
    # 默认日志配置
    DEFAULT_LOG_LEVEL = logging.INFO
    MAX_LOG_SIZE = 10 * 1024 * 1024  # 10MB
    BACKUP_COUNT = 5  # 保留5个备份文件
    
    def __init__(self):
        """初始化日志管理器"""
        # 获取应用数据目录
        self.app_data_dir = self._get_app_data_dir()
        self.log_dir = os.path.join(self.app_data_dir, "logs")
        self.log_file = os.path.join(self.log_dir, "ai_write_helper.log")
        
        # 确保日志目录存在
        os.makedirs(self.log_dir, exist_ok=True)
        
        # 日志格式
        self.log_format = (
            "%(asctime)s - %(name)s - %(levelname)s - "
            "%(filename)s:%(lineno)d - %(message)s"
        )
        self.date_format = "%Y-%m-%d %H:%M:%S"
        
        # 已配置的日志器
        self.loggers: Dict[str, logging.Logger] = {}
        
        # 根日志器配置标志
        self.root_configured = False
    
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
            if hasattr(os, 'uname') and os.uname().sysname == "Darwin":  # macOS
                return os.path.join(home, "Library", "Application Support", "AIWriteHelper")
            else:  # Linux
                return os.path.join(home, ".config", "aiwritehelper")
    
    def configure_root_logger(self, log_level: int = DEFAULT_LOG_LEVEL):
        """配置根日志器
        
        Args:
            log_level: 日志级别
        """
        if self.root_configured:
            return
        
        # 获取根日志器
        root_logger = logging.getLogger()
        root_logger.setLevel(log_level)
        
        # 清除已有的处理器
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
        
        # 添加文件处理器
        file_handler = self._create_file_handler(log_level)
        root_logger.addHandler(file_handler)
        
        # 添加控制台处理器
        console_handler = self._create_console_handler(log_level)
        root_logger.addHandler(console_handler)
        
        self.root_configured = True
        
    def _create_file_handler(self, log_level: int) -> logging.handlers.RotatingFileHandler:
        """创建文件日志处理器
        
        Args:
            log_level: 日志级别
            
        Returns:
            logging.handlers.RotatingFileHandler: 文件日志处理器
        """
        # 创建带轮转功能的文件处理器
        handler = logging.handlers.RotatingFileHandler(
            self.log_file,
            maxBytes=self.MAX_LOG_SIZE,
            backupCount=self.BACKUP_COUNT,
            encoding="utf-8"
        )
        
        handler.setLevel(log_level)
        
        # 设置日志格式
        formatter = logging.Formatter(
            fmt=self.log_format,
            datefmt=self.date_format
        )
        handler.setFormatter(formatter)
        
        return handler
    
    def _create_console_handler(self, log_level: int) -> logging.StreamHandler:
        """创建控制台日志处理器
        
        Args:
            log_level: 日志级别
            
        Returns:
            logging.StreamHandler: 控制台日志处理器
        """
        handler = logging.StreamHandler()
        handler.setLevel(log_level)
        
        # 设置日志格式
        formatter = logging.Formatter(
            fmt=self.log_format,
            datefmt=self.date_format
        )
        handler.setFormatter(formatter)
        
        return handler
    
    def get_logger(self, name: str, log_level: Optional[int] = None) -> logging.Logger:
        """获取指定名称的日志器
        
        Args:
            name: 日志器名称
            log_level: 日志级别，如果为None则使用默认级别
            
        Returns:
            logging.Logger: 日志器实例
        """
        # 如果日志器已存在，直接返回
        if name in self.loggers:
            return self.loggers[name]
        
        # 确保根日志器已配置
        if not self.root_configured:
            self.configure_root_logger()
        
        # 创建新的日志器
        logger = logging.getLogger(name)
        
        # 设置日志级别
        if log_level is not None:
            logger.setLevel(log_level)
        
        # 保存到已配置的日志器字典
        self.loggers[name] = logger
        
        return logger
    
    def set_level(self, log_level: int):
        """设置所有日志器的级别
        
        Args:
            log_level: 日志级别
        """
        # 更新根日志器级别
        if self.root_configured:
            root_logger = logging.getLogger()
            root_logger.setLevel(log_level)
            
            # 更新所有处理器的级别
            for handler in root_logger.handlers:
                handler.setLevel(log_level)
        
        # 更新所有已配置的日志器级别
        for logger in self.loggers.values():
            logger.setLevel(log_level)
    
    def enable_debug_logging(self):
        """启用调试日志级别"""
        self.set_level(logging.DEBUG)
    
    def disable_debug_logging(self):
        """禁用调试日志级别，恢复到默认级别"""
        self.set_level(self.DEFAULT_LOG_LEVEL)
    
    def get_log_file_path(self) -> str:
        """获取日志文件路径
        
        Returns:
            str: 日志文件路径
        """
        return self.log_file
    
    def clear_old_logs(self):
        """清除旧的日志文件"""
        try:
            # 获取日志目录中的所有文件
            if not os.path.exists(self.log_dir):
                return
            
            log_files = []
            for filename in os.listdir(self.log_dir):
                if filename.startswith("ai_write_helper.log"):
                    file_path = os.path.join(self.log_dir, filename)
                    log_files.append((file_path, os.path.getmtime(file_path)))
            
            # 按修改时间排序，保留最新的几个文件
            log_files.sort(key=lambda x: x[1], reverse=True)
            
            # 删除超出备份数量的旧文件
            files_to_delete = log_files[self.BACKUP_COUNT + 1:]
            for file_path, _ in files_to_delete:
                try:
                    os.remove(file_path)
                except Exception as e:
                    # 记录删除失败的日志，但不抛出异常
                    error_logger = self.get_logger("ai_write_helper.log_manager")
                    error_logger.error(f"删除旧日志文件失败 {file_path}: {str(e)}")
                    
        except Exception as e:
            # 记录清除旧日志失败的日志
            error_logger = self.get_logger("ai_write_helper.log_manager")
            error_logger.error(f"清除旧日志文件失败: {str(e)}")


# 创建全局日志管理器实例
_log_manager_instance = None

def get_log_manager() -> LogManager:
    """获取全局日志管理器实例
    
    Returns:
        LogManager: 日志管理器实例
    """
    global _log_manager_instance
    if _log_manager_instance is None:
        _log_manager_instance = LogManager()
    return _log_manager_instance

def get_logger(name: str, log_level: Optional[int] = None) -> logging.Logger:
    """便捷函数：获取指定名称的日志器
    
    Args:
        name: 日志器名称
        log_level: 日志级别
        
    Returns:
        logging.Logger: 日志器实例
    """
    return get_log_manager().get_logger(name, log_level)

def configure_logging(log_level: int = LogManager.DEFAULT_LOG_LEVEL):
    """便捷函数：配置日志系统
    
    Args:
        log_level: 日志级别
    """
    log_manager = get_log_manager()
    log_manager.configure_root_logger(log_level)
    log_manager.clear_old_logs()