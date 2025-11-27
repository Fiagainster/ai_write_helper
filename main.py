#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""AI写作助手 - 主入口文件

该模块是AI写作助手应用的主入口，负责初始化应用环境、配置系统、启动服务和UI界面。

使用方法:
    python main.py
"""

import os
import sys
import signal
import logging
import traceback
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer, QCoreApplication, QMetaObject, Qt
from PyQt6.QtWidgets import QMainWindow
from PyQt6.QtCore import QThread, pyqtSignal

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ai_write_helper.core.log_manager import LogManager
from ai_write_helper.core.config_manager import ConfigManager
from ai_write_helper.core.exceptions import AIWriteHelperError
from ai_write_helper.services.monitor import TextMonitorService
from ai_write_helper.services.api import APIService
from ai_write_helper.services.document import DocumentService
from ai_write_helper.ui.main_window import MainWindow


class AIWriteHelperApplication:
    """AI写作助手应用程序主类
    
    负责协调各模块间的交互，管理应用生命周期。
    """
    
    def __init__(self):
        """初始化应用程序"""
        # 应用名称和版本
        self.app_name = "AI写作助手"
        self.app_version = "1.0.0"
        
        # 初始化组件
        self.log_manager = None
        self.config_manager = None
        self.document_service = None
        self.api_service = None
        self.monitor_service = None
        self.main_window = None
        # 移除托盘图标引用
        
        # 应用运行状态
        self.is_running = False
    
    def initialize(self):
        """初始化应用环境和组件
        
        Returns:
            bool: 初始化是否成功
        """
        try:
            # 初始化日志系统
            self._init_logging()
            logging.info(f"启动{self.app_name} v{self.app_version}...")
            
            # 初始化配置管理器
            self._init_config()
            
            # 初始化服务组件
            self._init_services()
            
            # 初始化UI组件
            self._init_ui()
            
            # 连接信号和槽
            self._connect_signals()
            
            # 注册退出信号处理
            self._register_exit_handlers()
            
            logging.info("应用初始化成功")
            self.is_running = True
            return True
            
        except Exception as e:
            # 如果日志系统已初始化，则使用logging记录错误
            if self.log_manager:
                logging.critical(f"应用初始化失败: {str(e)}")
                logging.critical(traceback.format_exc())
            else:
                # 日志系统未初始化，直接打印错误
                print(f"严重错误: 无法初始化应用: {str(e)}")
                print(traceback.format_exc())
            return False
    
    def _init_logging(self):
        """初始化日志系统"""
        self.log_manager = LogManager()
        self.log_manager.configure_root_logger()
    
    def _init_config(self):
        """初始化配置管理器"""
        self.config_manager = ConfigManager()
        # 直接加载配置，ConfigManager内部会处理默认配置逻辑
        self.config = self.config_manager.load_config()
        logging.info("配置已加载")
    
    def _init_services(self):
        """初始化服务组件"""
        # 初始化文档服务
        self.document_service = DocumentService(self.config_manager)
        
        # 初始化API服务
        self.api_service = APIService(self.config_manager)
        
        # 初始化监控服务
        self.monitor_service = TextMonitorService(
            config_manager=self.config_manager,
            api_service=self.api_service,
            document_service=self.document_service
        )
    
    def _init_ui(self):
        """初始化UI组件"""
        # 创建主窗口
        self.main_window = MainWindow(self.config_manager, self.api_service, self.document_service)
        
        # 直接显示主窗口（不再隐藏）
        self.main_window.show()
        self.main_window.raise_()
        self.main_window.activateWindow()
        logging.info("主窗口已显示")
    
    def _connect_signals(self):
        """连接各组件间的信号和槽"""
        # 连接配置更新信号
        if self.main_window and self.config_manager:
            self.main_window.config_saved.connect(self._on_config_updated)
        
        # 连接监控服务信号到主窗口
        if self.main_window and self.monitor_service:
            self.main_window.connect_monitor_signals(self.monitor_service)
            
            # 将主窗口引用传递给监控服务
            self.monitor_service.main_window = self.main_window
    
    def _on_config_updated(self):
        """配置更新时的处理函数"""
        logging.info("配置已更新，重新初始化服务")
        
        try:
            # 获取最新配置
            self.config = self.config_manager.load_config()
            
            # 重新初始化服务
            self._init_services()
            
            # 重新连接信号
            self._connect_signals()
            
            # 启动监控服务
            self.monitor_service.start()
                
            logging.info("服务重新初始化成功")
        except Exception as e:
            logging.error(f"重新初始化服务失败: {str(e)}")
            logging.error(traceback.format_exc())
    


    def _register_exit_handlers(self):
        """注册应用退出处理函数"""
        # 注册信号处理函数
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        # 在Windows上，SIGBREAK等同于Ctrl+Break
        if hasattr(signal, 'SIGBREAK'):
            signal.signal(signal.SIGBREAK, self._signal_handler)
    
    def _signal_handler(self, sig, frame):
        """信号处理函数
        
        Args:
            sig (int): 信号编号
            frame: 当前栈帧
        """
        signal_name = signal.Signals(sig).name if hasattr(signal, 'Signals') else str(sig)
        logging.info(f"接收到信号 {signal_name}，准备退出应用")
        
        # 在主线程中调用quit方法
        QMetaObject.invokeMethod(
            QCoreApplication.instance(),
            "quit",
            Qt.ConnectionType.QueuedConnection
        )
        
        # 确保程序能够退出
        import threading
        def force_exit():
            import time
            time.sleep(1)  # 给应用1秒时间正常退出
            logging.critical("强制退出应用...")
            import os
            os._exit(1)  # 强制退出
        
        # 启动一个线程来确保应用退出
        exit_thread = threading.Thread(target=force_exit)
        exit_thread.daemon = True
        exit_thread.start()
    
    def start(self):
        """启动应用程序
        
        Returns:
            int: 退出代码
        """
        # 初始化应用
        if not self.initialize():
            logging.critical("应用初始化失败，无法启动")
            return 1
        
        # 直接启动监控服务
        # 用户可以在配置窗口中设置API密钥和文档路径
        try:
            self.monitor_service.start()
            logging.info("文本监控服务已启动")
        except Exception as e:
            logging.error(f"启动监控服务失败: {str(e)}")
            logging.error(traceback.format_exc())
        
        # 进入应用主循环
        try:
            # 应用主循环
            return QApplication.instance().exec()
            
        except Exception as e:
            logging.critical(f"应用运行出错: {str(e)}")
            logging.critical(traceback.format_exc())
            return 1
        finally:
            # 清理资源
            self.cleanup()
    
    def quit(self):
        """优雅退出应用"""
        logging.info("准备退出应用...")
        
        # 停止监控服务
        if self.monitor_service:
            try:
                # 检查is_running属性是否存在
                is_running = hasattr(self.monitor_service, 'is_running') and callable(getattr(self.monitor_service, 'is_running')) and self.monitor_service.is_running()
                if is_running:
                    self.monitor_service.stop()
                    logging.info("文本监控服务已停止")
            except Exception as e:
                logging.error(f"停止监控服务时出错: {str(e)}")
        
        # 隐藏UI组件 - 只保留主窗口相关代码
        if self.main_window:
            self.main_window.hide()
        
        # 清理资源
        self.cleanup()
        
        # 退出应用
        QCoreApplication.quit()
    
    def cleanup(self):
        """清理资源"""
        # 确保logging模块可用
        try:
            import logging
            logging.info("清理应用资源...")
            
            # 保存配置
            if self.config_manager and hasattr(self, 'config'):
                try:
                    self.config_manager.save_config(self.config)
                    logging.info("配置已保存")
                except Exception as e:
                    logging.error(f"保存配置时出错: {str(e)}")
            
            # 关闭日志
            try:
                logging.shutdown()
                print("日志系统已关闭")
            except Exception as e:
                print(f"关闭日志系统时出错: {str(e)}")
        except Exception as e:
            print(f"清理过程中发生错误: {str(e)}")
        
        self.is_running = False
        # 最后一条日志已无法记录，但不影响程序退出


def main():
    """应用主函数"""
    # 确保只创建一个QApplication实例
    app = QApplication.instance()
    if not app:
        # 设置应用信息
        QApplication.setApplicationName("AI写作助手")
        QApplication.setOrganizationName("AI Writing Helper")
        QApplication.setApplicationVersion("1.0.0")
        
        # 创建应用实例
        app = QApplication(sys.argv)
    
    # 创建并启动应用
    ai_app = AIWriteHelperApplication()
    exit_code = ai_app.start()
    
    # 退出应用
    sys.exit(exit_code)


if __name__ == "__main__":
    main()