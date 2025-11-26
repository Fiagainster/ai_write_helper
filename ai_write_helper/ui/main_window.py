#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""主窗口模块

该模块实现应用程序的主配置窗口，包含API密钥设置、文档路径选择和主题提示词编辑功能。
"""

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QFileDialog,
    QTextEdit, QMessageBox, QGroupBox
)
from PyQt6.QtCore import Qt, pyqtSignal


class MainWindow(QMainWindow):
    """应用程序主窗口"""
    
    # 信号定义
    config_saved = pyqtSignal()
    
    def __init__(self, config_manager, api_service, document_service):
        """初始化主窗口
        
        Args:
            config_manager: 配置管理器实例
            api_service: API服务实例
            document_service: 文档服务实例
        """
        super().__init__()
        self.config_manager = config_manager
        self.api_service = api_service
        self.document_service = document_service
        
        # 加载现有配置
        self.config = self.config_manager.load_config()
        
        # 设置窗口属性
        self.setWindowTitle("AI写作助手")
        self.setGeometry(100, 100, 600, 500)
        self.setFixedSize(600, 500)
        
        # 初始化状态栏
        self.init_status_bar()
        
        # 初始化UI
        self.init_ui()
        
        # 加载配置到界面
        self.load_config_to_ui()
    
    def init_ui(self):
        """初始化用户界面"""
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # API密钥设置
        api_group = QGroupBox("API设置")
        api_layout = QVBoxLayout()
        api_layout.setSpacing(10)
        
        # API密钥输入
        key_layout = QHBoxLayout()
        key_layout.addWidget(QLabel("DeepSeek API密钥:"))
        self.api_key_input = QLineEdit()
        self.api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        key_layout.addWidget(self.api_key_input)
        
        # 验证按钮
        self.validate_button = QPushButton("验证密钥")
        self.validate_button.clicked.connect(self.validate_api_key)
        key_layout.addWidget(self.validate_button)
        
        api_layout.addLayout(key_layout)
        
        # 状态标签
        self.api_status_label = QLabel("请输入并验证API密钥")
        api_layout.addWidget(self.api_status_label)
        
        api_group.setLayout(api_layout)
        main_layout.addWidget(api_group)
        
        # 文档路径设置
        doc_group = QGroupBox("文档设置")
        doc_layout = QVBoxLayout()
        doc_layout.setSpacing(10)
        
        # 文档路径输入
        path_layout = QHBoxLayout()
        path_layout.addWidget(QLabel("目标文档路径:"))
        self.doc_path_input = QLineEdit()
        path_layout.addWidget(self.doc_path_input)
        
        # 浏览按钮
        browse_button = QPushButton("浏览...")
        browse_button.clicked.connect(self.browse_document)
        path_layout.addWidget(browse_button)
        
        doc_layout.addLayout(path_layout)
        
        doc_group.setLayout(doc_layout)
        main_layout.addWidget(doc_group)
        
        # 主题提示词设置
        prompt_group = QGroupBox("主题提示词")
        prompt_layout = QVBoxLayout()
        prompt_layout.setSpacing(10)
        
        # 提示词说明
        prompt_desc = QLabel("指导AI补写内容的主题方向和风格偏好")
        prompt_desc.setStyleSheet("color: #666; font-size: 12px;")
        prompt_layout.addWidget(prompt_desc)
        
        # 提示词输入
        self.template_editor = QTextEdit()
        self.template_editor.setMinimumHeight(100)
        self.template_editor.setPlaceholderText("例如：'请以技术博客风格撰写'、'使用正式学术语言'等")
        prompt_layout.addWidget(self.template_editor)
        
        prompt_group.setLayout(prompt_layout)
        main_layout.addWidget(prompt_group)
        
        # 创建底部按钮布局
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.save_button = QPushButton("保存配置")
        self.save_button.setFixedWidth(120)
        self.save_button.clicked.connect(self.save_config)
        button_layout.addWidget(self.save_button)
        
        main_layout.addLayout(button_layout)
    
    def load_config_to_ui(self):
        """加载配置到UI界面"""
        # 加载API密钥
        if 'api_key' in self.config:
            self.api_key_input.setText(self.config['api_key'])
        
        # 加载文档路径
        if 'document_path' in self.config:
            self.doc_path_input.setText(self.config['document_path'])
        
        # 加载主题提示词
        if 'templates' in self.config and 'default' in self.config['templates']:
            self.template_editor.setPlainText(self.config['templates']['default'])
    
    def validate_api_key(self):
        """验证API密钥"""
        api_key = self.api_key_input.text().strip()
        if not api_key:
            QMessageBox.warning(self, "警告", "请输入API密钥")
            return
        
        # 调用API服务验证密钥
        try:
            is_valid = self.api_service.validate_key(api_key)
            if is_valid:
                self.api_status_label.setText("✓ API密钥有效")
                self.api_status_label.setStyleSheet("color: green")
                QMessageBox.information(self, "成功", "API密钥验证成功")
            else:
                self.api_status_label.setText("✗ API密钥无效")
                self.api_status_label.setStyleSheet("color: red")
                QMessageBox.critical(self, "错误", "API密钥验证失败")
        except Exception as e:
            self.api_status_label.setText(f"✗ 验证失败: {str(e)}")
            self.api_status_label.setStyleSheet("color: red")
            QMessageBox.critical(self, "错误", f"验证过程出错: {str(e)}")
    
    def browse_document(self):
        """浏览并选择文档"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择文档文件",
            "",
            "所有文件 (*);;文本文件 (*.txt);;Markdown文件 (*.md);;Word文档 (*.docx)"
        )
        
        if file_path:
            self.doc_path_input.setText(file_path)
    
    def save_config(self):
        """保存所有配置"""
        try:
            # 获取API密钥
            api_key = self.api_key_input.text().strip()
            if not api_key:
                QMessageBox.warning(self, "警告", "请输入API密钥")
                return
            self.config['api_key'] = api_key
            
            # 获取文档路径
            document_path = self.doc_path_input.text().strip()
            if not document_path:
                QMessageBox.warning(self, "警告", "请选择目标文档")
                return
            self.config['document_path'] = document_path
            
            # 获取主题提示词
            theme_prompt = self.template_editor.toPlainText().strip()
            if 'templates' not in self.config:
                self.config['templates'] = {}
            self.config['templates']['default'] = theme_prompt
            
            # 验证文档路径是否有效
            if not self.document_service.validate_path(document_path):
                QMessageBox.warning(self, "警告", "文档路径无效或无权限访问")
                return
            
            # 保存配置
            self.config_manager.save_config(self.config)
            
            # 发出配置已保存信号
            self.config_saved.emit()
            
            QMessageBox.information(self, "成功", "配置保存成功")
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"保存配置失败: {str(e)}")
    
    def init_status_bar(self):
        """初始化状态栏"""
        self.statusBar().showMessage("就绪")
    
    def on_processing_started(self):
        """处理开始信号"""
        self.statusBar().showMessage("正在处理...")
    
    def on_processing_completed(self, message):
        """处理完成信号"""
        self.statusBar().showMessage(f"成功: {message}")
    
    def on_processing_failed(self, error):
        """处理失败信号"""
        self.statusBar().showMessage(f"错误: {error}")
    
    def connect_monitor_signals(self, monitor_service):
        """连接监控服务信号
        
        Args:
            monitor_service: 文本监控服务实例
        """
        monitor_service.processing_started.connect(self.on_processing_started)
        monitor_service.processing_completed.connect(self.on_processing_completed)
        monitor_service.processing_failed.connect(self.on_processing_failed)
    
    def closeEvent(self, event):
        """窗口关闭事件
        
        由于移除了托盘功能，现在窗口关闭时应该正常退出应用
        """
        # 正常接受关闭事件，允许窗口关闭
        event.accept()
        # 通知应用退出
        from PyQt6.QtCore import QCoreApplication
        QCoreApplication.quit()