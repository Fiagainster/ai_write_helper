#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""主窗口模块

该模块实现应用程序的主配置窗口，包含API密钥设置、文档路径选择和主题提示词编辑功能。
"""

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QFileDialog,
    QTextEdit, QMessageBox, QGroupBox, QComboBox,
    QTabWidget, QSystemTrayIcon, QMenu, QCheckBox
)
from PyQt6.QtGui import QAction, QPainter, QBrush, QColor, QFont, QPen
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QPoint, QRect


class MinimizeBall(QWidget):
    """最小化球类，用于显示最小化后的窗口和进度信息"""
    
    # 信号定义
    clicked = pyqtSignal()  # 点击信号
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 设置窗口属性
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(60, 60)
        
        # 进度信息
        self.progress_text = ""
        self.progress_timer = QTimer(self)
        self.progress_timer.setSingleShot(True)
        self.progress_timer.timeout.connect(self.clear_progress)
        
        # 鼠标事件
        self.mouse_press_pos = None
        self.mouse_move_pos = None
        
        # 动画效果
        self.animation_timer = QTimer(self)
        self.animation_timer.timeout.connect(self.update)
        self.animation_timer.start(50)  # 20fps动画
        self.animation_offset = 0
    
    def paintEvent(self, event):
        """绘制最小化球"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        
        # 绘制阴影效果
        shadow_rect = QRect(2, 2, self.width(), self.height())
        shadow_brush = QBrush(QColor(0, 0, 0, 30))
        painter.setBrush(shadow_brush)
        painter.setPen(QPen(Qt.PenStyle.NoPen))
        painter.drawEllipse(shadow_rect)
        
        # 绘制圆形背景（渐变效果，增强立体感）
        center = self.rect().center()
        radius = self.width() // 2 - 2
        
        # 主渐变
        gradient = QBrush(QColor(76, 175, 80, 230))
        painter.setBrush(gradient)
        painter.setPen(QPen(Qt.PenStyle.NoPen))
        painter.drawEllipse(center, radius, radius)
        
        # 高光效果（增强立体感）
        highlight_rect = QRect(center.x() - radius // 2, center.y() - radius // 2, radius, radius)
        highlight_brush = QBrush(QColor(255, 255, 255, 40))
        painter.setBrush(highlight_brush)
        painter.drawEllipse(highlight_rect)
        
        # 动态波纹效果
        self.animation_offset = (self.animation_offset + 1) % 100
        ripple_radius = radius + self.animation_offset // 10
        ripple_pen = QPen(QColor(255, 255, 255, 20 - self.animation_offset // 5))
        ripple_pen.setWidth(1)
        painter.setPen(ripple_pen)
        painter.setBrush(QBrush(Qt.BrushStyle.NoBrush))
        painter.drawEllipse(center, ripple_radius, ripple_radius)
        
        # 绘制进度文字
        if self.progress_text:
            # 限制为3个字符
            display_text = self.progress_text[:3]
            painter.setPen(QColor(255, 255, 255))
            painter.setFont(QFont("微软雅黑", 12, QFont.Weight.Bold))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, display_text)
    
    def mousePressEvent(self, event):
        """鼠标按下事件"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.mouse_press_pos = event.globalPosition().toPoint()
            self.mouse_move_pos = event.globalPosition().toPoint()
        elif event.button() == Qt.MouseButton.RightButton:
            # 右键点击展开窗口
            self.clicked.emit()
    
    def mouseMoveEvent(self, event):
        """鼠标移动事件"""
        if event.buttons() == Qt.MouseButton.LeftButton and self.mouse_press_pos:
            current_pos = event.globalPosition().toPoint()
            delta = current_pos - self.mouse_move_pos
            self.move(self.pos() + delta)
            self.mouse_move_pos = current_pos
    
    def mouseReleaseEvent(self, event):
        """鼠标释放事件"""
        if event.button() == Qt.MouseButton.LeftButton:
            # 检查是否是点击事件（移动距离很小）
            if self.mouse_press_pos and self.mouse_move_pos:
                delta = self.mouse_move_pos - self.mouse_press_pos
                if abs(delta.x()) < 5 and abs(delta.y()) < 5:
                    # 点击事件，展开窗口
                    self.clicked.emit()
            self.mouse_press_pos = None
            self.mouse_move_pos = None
    
    def set_progress(self, text, duration=1000):
        """设置进度信息
        
        Args:
            text: 进度文字
            duration: 显示时长（毫秒）
        """
        self.progress_text = text
        self.update()
        self.progress_timer.start(duration)
    
    def clear_progress(self):
        """清除进度信息"""
        self.progress_text = ""
        self.update()
    
    def show_ball(self):
        """显示最小化球"""
        self.show()
    
    def hide_ball(self):
        """隐藏最小化球"""
        self.hide()


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
        self.setGeometry(100, 100, 450, 350)
        self.setFixedSize(450, 200)
        
        # 初始化状态栏
        self.init_status_bar()
        
        # 初始化最小化球
        self.minimize_ball = MinimizeBall()
        self.minimize_ball.clicked.connect(self.restore_from_ball)
        
        # 初始化UI
        self.init_ui()
        
        # 加载配置到界面
        self.load_config_to_ui()
    
    def minimize_to_ball(self):
        """最小化为球"""
        self.hide()
        self.minimize_ball.show_ball()
    
    def restore_from_ball(self):
        """从球恢复窗口"""
        self.minimize_ball.hide_ball()
        self.show()
        self.raise_()
        self.activateWindow()
    

    
    def toggle_minimize(self):
        """切换最小化/恢复状态"""
        if self.isVisible():
            # 当前窗口可见，最小化为球
            self.minimize_to_ball()
        else:
            # 当前窗口不可见，从球恢复
            self.restore_from_ball()
    
    def show_usage(self):
        """显示使用说明"""
        usage_text = """AI写作助手使用说明：

1. 在API设置中输入DeepSeek API密钥并验证
2. 在文档设置中选择目标文档和写入模式
3. 在主题提示词中设置AI补写的方向和风格
4. 保存配置后，在任意应用中选中文本并按下Enter键
5. AI会自动生成补写内容并写入到目标文档中

写入模式说明：
- 增量写入：生成的内容会追加到文档末尾
- 全量重写：生成的内容会替换整个文档
"""
        QMessageBox.information(self, "使用说明", usage_text)
    
    def show_about(self):
        """显示关于信息"""
        about_text = """AI写作助手 v1.0.0

一个基于AI的划词补写工具，支持Word和Markdown文档。

功能特点：
- 全局监听文本选择和Enter键事件
- 支持多种文档格式
- 可配置写入模式
- 支持自定义主题提示词
"""
        QMessageBox.information(self, "关于", about_text)
    
    def show_contact(self):
        """显示联系方式"""
        contact_text = """联系方式：

如有问题或建议，欢迎联系我们：
- 邮箱：508125305@qq.com
"""
        QMessageBox.information(self, "联系方式", contact_text)
    
    def init_ui(self):
        """初始化用户界面"""
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(2)
        main_layout.setContentsMargins(2, 2, 2, 2)
        
        # 创建标签页
        self.tab_widget = QTabWidget()
        # 设置标签页样式，增强层次感
        self.tab_widget.setStyleSheet("""QTabWidget::pane {
            border: 1px solid #ccc;
            border-radius: 4px;
            background: white;
        }
        QTabBar::tab {
            background: #f0f0f0;
            border: 1px solid #ccc;
            border-bottom-color: #ccc;
            border-radius: 4px 4px 0 0;
            padding: 3px 8px;
            margin-right: 1px;
            font-size: 11px;
        }
        QTabBar::tab:selected {
            background: white;
            border-bottom-color: white;
        }""")
        main_layout.addWidget(self.tab_widget)
        
        # API设置标签页
        api_tab = QWidget()
        api_layout = QVBoxLayout(api_tab)
        api_layout.setSpacing(5)
        api_layout.setContentsMargins(5, 5, 5, 5)
        
        # API密钥输入
        key_layout = QHBoxLayout()
        key_label = QLabel("API密钥:")
        key_label.setFixedWidth(60)
        key_label.setStyleSheet("font-size: 11px;")
        key_layout.addWidget(key_label)
        self.api_key_input = QLineEdit()
        self.api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.api_key_input.setFixedHeight(20)
        self.api_key_input.setStyleSheet("font-size: 11px;")
        key_layout.addWidget(self.api_key_input)
        
        # 验证按钮
        self.validate_button = QPushButton("验证")
        self.validate_button.clicked.connect(self.validate_api_key)
        self.validate_button.setFixedWidth(50)
        self.validate_button.setFixedHeight(20)
        self.validate_button.setStyleSheet("font-size: 10px;")
        key_layout.addWidget(self.validate_button)
        
        api_layout.addLayout(key_layout)
        
        # 状态标签
        self.api_status_label = QLabel("请输入并验证API密钥")
        self.api_status_label.setStyleSheet("font-size: 10px; color: #666;")
        api_layout.addWidget(self.api_status_label)
        
        self.tab_widget.addTab(api_tab, "API设置")
        
        # 文档设置标签页
        doc_tab = QWidget()
        doc_layout = QVBoxLayout(doc_tab)
        doc_layout.setSpacing(5)
        doc_layout.setContentsMargins(5, 5, 5, 5)
        
        # 文档路径输入
        path_layout = QHBoxLayout()
        path_label = QLabel("文档路径:")
        path_label.setFixedWidth(60)
        path_label.setStyleSheet("font-size: 11px;")
        path_layout.addWidget(path_label)
        self.doc_path_input = QLineEdit()
        self.doc_path_input.setFixedHeight(20)
        self.doc_path_input.setStyleSheet("font-size: 11px;")
        path_layout.addWidget(self.doc_path_input)
        
        # 浏览按钮
        browse_button = QPushButton("浏览")
        browse_button.clicked.connect(self.browse_document)
        browse_button.setFixedWidth(40)
        browse_button.setFixedHeight(20)
        browse_button.setStyleSheet("font-size: 10px;")
        path_layout.addWidget(browse_button)
        
        doc_layout.addLayout(path_layout)
        
        # 写入模式选择
        write_mode_layout = QHBoxLayout()
        write_mode_label = QLabel("写入模式:")
        write_mode_label.setFixedWidth(70)
        write_mode_label.setStyleSheet("font-size: 11px;")
        write_mode_layout.addWidget(write_mode_label)
        self.write_mode_combo = QComboBox()
        self.write_mode_combo.addItem("增量写入", "incremental")
        self.write_mode_combo.addItem("全量重写", "overwrite")
        self.write_mode_combo.setFixedHeight(25)
        self.write_mode_combo.setStyleSheet("font-size: 11px;")
        write_mode_layout.addWidget(self.write_mode_combo)
        write_mode_layout.addStretch()
        
        doc_layout.addLayout(write_mode_layout)
        

        
        self.tab_widget.addTab(doc_tab, "文档设置")
        
        # 主题提示词标签页
        prompt_tab = QWidget()
        prompt_layout = QVBoxLayout(prompt_tab)
        prompt_layout.setSpacing(5)
        prompt_layout.setContentsMargins(5, 5, 5, 5)
        
        # 提示词说明
        prompt_desc = QLabel("主题提示词")
        prompt_desc.setStyleSheet("font-weight: bold; font-size: 11px;")
        prompt_layout.addWidget(prompt_desc)
        
        # 提示词输入
        self.template_editor = QTextEdit()
        self.template_editor.setMinimumHeight(100)
        self.template_editor.setPlaceholderText("指导AI补写的方向和风格")
        self.template_editor.setStyleSheet("font-size: 11px;")
        prompt_layout.addWidget(self.template_editor)
        
        self.tab_widget.addTab(prompt_tab, "主题提示词")
        
        # 帮助标签页
        help_tab = QWidget()
        help_layout = QVBoxLayout(help_tab)
        help_layout.setSpacing(10)
        help_layout.setContentsMargins(10, 10, 10, 10)
        
        # 使用说明按钮
        usage_button = QPushButton("使用说明")
        usage_button.clicked.connect(self.show_usage)
        usage_button.setFixedHeight(30)
        usage_button.setStyleSheet("font-size: 12px;")
        help_layout.addWidget(usage_button)
        
        # 关于按钮
        about_button = QPushButton("关于")
        about_button.clicked.connect(self.show_about)
        about_button.setFixedHeight(30)
        about_button.setStyleSheet("font-size: 12px;")
        help_layout.addWidget(about_button)
        
        # 联系方式按钮
        contact_button = QPushButton("联系方式")
        contact_button.clicked.connect(self.show_contact)
        contact_button.setFixedHeight(30)
        contact_button.setStyleSheet("font-size: 12px;")
        help_layout.addWidget(contact_button)
        
        # 占位符，使按钮居中显示
        help_layout.addStretch()
        
        self.tab_widget.addTab(help_tab, "帮助")
        
        # 创建底部按钮布局
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        # 最小化/恢复按钮
        self.minimize_button = QPushButton("最小化")
        self.minimize_button.setFixedWidth(80)
        self.minimize_button.setFixedHeight(28)
        self.minimize_button.clicked.connect(self.toggle_minimize)
        self.minimize_button.setStyleSheet("""QPushButton {
            background-color: #2196F3;
            color: white;
            border: none;
            border-radius: 3px;
            padding: 5px 10px;
            font-size: 12px;
        }
        QPushButton:hover {
            background-color: #1976D2;
        }""")
        button_layout.addWidget(self.minimize_button)
        
        self.save_button = QPushButton("保存配置")
        self.save_button.setFixedWidth(100)
        self.save_button.setFixedHeight(28)
        self.save_button.clicked.connect(self.save_config)
        self.save_button.setStyleSheet("""QPushButton {
            background-color: #4CAF50;
            color: white;
            border: none;
            border-radius: 3px;
            padding: 5px 10px;
            font-size: 12px;
        }
        QPushButton:hover {
            background-color: #45a049;
        }""")
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
        
        # 加载写入模式
        if 'write_mode' in self.config:
            write_mode = self.config['write_mode']
            index = self.write_mode_combo.findData(write_mode)
            if index >= 0:
                self.write_mode_combo.setCurrentIndex(index)
        
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
            
            # 获取写入模式
            write_mode = self.write_mode_combo.currentData()
            self.config['write_mode'] = write_mode
            
            # 始终显示最小化球
            self.config['show_minimize_ball'] = True
            
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
        # 连接进度更新信号到最小化球
        monitor_service.progress_updated.connect(self.on_progress_updated)
    
    def on_progress_updated(self, progress_text):
        """处理进度更新信号"""
        # 在最小化球上显示进度信息
        self.minimize_ball.set_progress(progress_text)
    
    def closeEvent(self, event):
        """窗口关闭事件
        
        由于移除了托盘功能，现在窗口关闭时应该正常退出应用
        """
        # 正常接受关闭事件，允许窗口关闭
        event.accept()
        # 通知应用退出
        from PyQt6.QtCore import QCoreApplication
        QCoreApplication.quit()