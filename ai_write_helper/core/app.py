#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""应用核心类

该模块包含App类，作为整个应用程序的核心控制中心，负责初始化和协调各个组件。
"""

import logging
from threading import Thread

from ..config.manager import ConfigManager
from ..services.monitor import TextMonitorService
from ..services.api import APIService
from ..services.document import DocumentService
from ..ui.main_window import MainWindow
from ..ui.tray import TrayIcon


class App:
    """应用程序核心类，协调所有组件的工作"""
    
    def __init__(self):
        """初始化应用程序"""
        self.logger = self._setup_logging()
        self.logger.info("正在初始化AI写作助手应用...")
        
        # 初始化各个服务组件
        self.config_manager = ConfigManager()
        self.document_service = DocumentService()
        self.api_service = APIService(self.config_manager)
        
        # UI组件
        self.main_window = None
        self.tray_icon = None
        
        # 后台服务
        self.monitor_service = None
        self.monitor_thread = None
    
    def _setup_logging(self):
        """设置日志系统"""
        logger = logging.getLogger("ai_write_helper")
        logger.setLevel(logging.INFO)
        
        # 创建文件处理器
        handler = logging.FileHandler("app.log", encoding="utf-8")
        handler.setLevel(logging.INFO)
        
        # 设置日志格式
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        
        # 添加处理器到日志器
        logger.addHandler(handler)
        
        return logger
    
    def run(self):
        """运行应用程序"""
        from PyQt6.QtWidgets import QApplication
        
        # 创建Qt应用程序实例
        qt_app = QApplication([])
        qt_app.setQuitOnLastWindowClosed(False)
        
        # 初始化UI
        self.main_window = MainWindow(
            self.config_manager,
            self.api_service,
            self.document_service
        )
        
        # 初始化系统托盘
        self.tray_icon = TrayIcon(self.main_window)
        self.tray_icon.show()
        
        # 启动文本监听服务
        self._start_monitor_service()
        
        # 显示主窗口
        self.main_window.show()
        
        # 运行Qt事件循环
        sys.exit(qt_app.exec())
    
    def _start_monitor_service(self):
        """启动文本监听服务"""
        self.monitor_service = TextMonitorService(
            self.config_manager,
            self.api_service,
            self.document_service
        )
        
        # 在单独的线程中运行监听服务
        self.monitor_thread = Thread(
            target=self.monitor_service.start,
            daemon=True
        )
        self.monitor_thread.start()
        self.logger.info("文本监听服务已启动")


# 导入sys模块
import sys