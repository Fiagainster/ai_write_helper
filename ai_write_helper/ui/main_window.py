#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""主窗口模块

该模块实现应用程序的主配置窗口，包含API密钥设置、文档路径选择和主题提示词编辑功能。
"""

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QFileDialog,
    QTextEdit, QMessageBox, QGroupBox, QComboBox,
    QTabWidget, QSystemTrayIcon, QMenu, QCheckBox,
    QScrollArea, QFrame, QDialog
)
from PyQt6.QtGui import QAction, QPainter, QBrush, QColor, QFont, QPen
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QPoint, QRect


class MinimizeBall(QWidget):
    """最小化球类，用于显示最小化后的窗口和进度信息"""
    
    # 状态定义
    STATUS_STANDBY = "standby"
    STATUS_PROCESSING = "processing"
    STATUS_COMPLETED = "completed"
    STATUS_ERROR = "error"
    
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
        
        # 状态管理
        self.status = self.STATUS_STANDBY
        self.status_timer = QTimer(self)
        self.status_timer.setSingleShot(True)
        self.status_timer.timeout.connect(self.reset_to_standby)
        
        # 动画效果（极简版）
        self.animation_timer = QTimer(self)
        self.animation_timer.timeout.connect(self.update)
        self.animation_timer.start(50)  # 20fps动画，足够流畅且不影响性能
        self.animation_offset = 0
        
        # 动态效果开关
        self.dynamic_effects_enabled = True
    
    def set_status(self, status):
        """设置状态
        
        Args:
            status: 状态值
        """
        self.status = status
        
        # 如果是完成或错误状态，1秒后恢复到待机状态
        if status in [self.STATUS_COMPLETED, self.STATUS_ERROR]:
            self.status_timer.start(1000)
        
        self.update()
    
    def reset_to_standby(self):
        """重置到待机状态"""
        self.status = self.STATUS_STANDBY
        self.update()
    
    def set_dynamic_effects(self, enabled):
        """设置动态效果开关
        
        Args:
            enabled: 是否启用动态效果
        """
        self.dynamic_effects_enabled = enabled
        self.update()
    
    def paintEvent(self, event):
        """绘制最小化球"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        
        # 绘制圆形背景
        center = self.rect().center()
        radius = self.width() // 2
        
        # 根据状态设置颜色
        if self.status == self.STATUS_STANDBY:
            # 待机状态：静态绿色
            bg_color = QColor(76, 175, 80, 230)
        elif self.status == self.STATUS_PROCESSING:
            # 处理中状态：缓慢闪烁绿色
            if self.dynamic_effects_enabled:
                # 极简动画：颜色亮度变化，增加变化范围，使效果更明显
                brightness = 50 + (self.animation_offset % 100) // 2
                bg_color = QColor(brightness, 175, 80, 230)
            else:
                bg_color = QColor(76, 175, 80, 230)
        elif self.status == self.STATUS_COMPLETED:
            # 完成状态：亮绿色
            bg_color = QColor(46, 204, 113, 230)
        elif self.status == self.STATUS_ERROR:
            # 错误状态：红色
            bg_color = QColor(231, 76, 60, 230)
        else:
            # 默认状态
            bg_color = QColor(76, 175, 80, 230)
        
        # 绘制背景
        painter.setBrush(QBrush(bg_color))
        painter.setPen(QPen(Qt.PenStyle.NoPen))
        painter.drawEllipse(center, radius, radius)
        
        # 高光效果（增强立体感）
        highlight_brush = QBrush(QColor(255, 255, 255, 40))
        painter.setBrush(highlight_brush)
        painter.drawEllipse(center, radius // 2, radius // 2)
        
        # 绘制进度文字
        if self.progress_text:
            # 限制为3个字符
            display_text = self.progress_text[:3]
            painter.setPen(QColor(255, 255, 255))
            painter.setFont(QFont("微软雅黑", 12, QFont.Weight.Bold))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, display_text)
        
        # 更新动画偏移
        self.animation_offset = (self.animation_offset + 1) % 100
    
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
        
        # 提示词模板数据
        self.prompt_templates = [
            {
                "category": "科技论文",
                "description": "科技论文风格，注重数据分析和逻辑推理",
                "content": "请以科技论文风格重写文档，注重数据分析和逻辑推理，使用专业术语，结构清晰，论证严谨。"
            },
            {
                "category": "商业报告",
                "description": "商业报告风格，突出结论和行动建议",
                "content": "请以商业报告风格重写文档，突出结论和行动建议，语言简洁明了，重点突出，具有说服力。"
            },
            {
                "category": "创意写作",
                "description": "创意写作风格，使用生动的描述和比喻",
                "content": "请以创意写作风格重写文档，使用生动的描述和比喻，语言富有表现力，情节引人入胜。"
            },
            {
                "category": "学术论文",
                "description": "学术论文风格，严谨规范，引用准确",
                "content": "请以学术论文风格重写文档，严谨规范，引用准确，结构完整，论点明确，论据充分。"
            },
            {
                "category": "新闻报道",
                "description": "新闻报道风格，客观公正，时效性强",
                "content": "请以新闻报道风格重写文档，客观公正，时效性强，语言简洁，信息量大，结构清晰。"
            },
            {
                "category": "产品描述",
                "description": "产品描述风格，突出产品特点和优势",
                "content": "请以产品描述风格重写文档，突出产品特点和优势，语言生动，具有吸引力，能够激发购买欲望。"
            },
            {
                "category": "技术文档",
                "description": "技术文档风格，准确详细，易于理解",
                "content": "请以技术文档风格重写文档，准确详细，易于理解，结构清晰，步骤明确，便于操作。"
            },
            {
                "category": "营销文案",
                "description": "营销文案风格，富有感染力，促进转化",
                "content": "请以营销文案风格重写文档，富有感染力，语言生动，能够吸引目标受众，促进转化。"
            }
        ]
        
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

1. 在API设置中输入AI服务API密钥并验证
2. 在文档设置中选择目标文档和写入模式
3. 在主题提示词中设置AI补写的方向和风格
4. 保存配置后，在任意应用中选中文本并按下Enter键
5. AI会自动生成补写内容并写入到目标文档中

写入模式说明：
- 增量写入：生成的内容会追加到文档末尾
- 全量重写：生成的内容会替换整个文档
- 光标补写：在文档中标记的光标位置插入内容，不改变其他内容
  使用方法：在文档中需要插入内容的位置添加 [CURSOR] 标记
  例如："这是一个测试[CURSOR]文档"
  AI会在[CURSOR]标记处插入生成的内容，并移除该标记
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
    
    def show_prompt_templates(self):
        """显示提示词模板弹窗"""
        # 创建弹窗
        dialog = QDialog(self)
        dialog.setWindowTitle("提示词模板")
        dialog.setGeometry(200, 200, 500, 400)
        dialog.setMinimumSize(450, 350)
        
        # 主布局
        main_layout = QVBoxLayout(dialog)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # 创建滚动区域
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        
        # 模板容器
        template_container = QWidget()
        template_container_layout = QVBoxLayout(template_container)
        template_container_layout.setSpacing(5)
        template_container_layout.setContentsMargins(0, 0, 0, 0)
        
        # 添加模板列表
        for template in self.prompt_templates:
            # 模板项
            template_item = QWidget()
            template_item_layout = QVBoxLayout(template_item)
            template_item_layout.setSpacing(2)
            template_item_layout.setContentsMargins(5, 5, 5, 5)
            
            # 分类和描述
            category_desc = QLabel(f"<b>{template['category']}</b>: {template['description']}")
            category_desc.setStyleSheet("font-size: 10px;")
            category_desc.setWordWrap(True)
            template_item_layout.addWidget(category_desc)
            
            # 提示词内容
            content_label = QLabel(template['content'])
            content_label.setStyleSheet("font-size: 10px; background-color: #f5f5f5; padding: 5px; border-radius: 3px;")
            content_label.setWordWrap(True)
            template_item_layout.addWidget(content_label)
            
            # 复制按钮
            copy_button = QPushButton("复制")
            copy_button.setFixedHeight(20)
            copy_button.setStyleSheet("font-size: 9px; background-color: #2196F3; color: white; border: none; border-radius: 3px;")
            copy_button.clicked.connect(lambda checked, c=template['content'], d=dialog: self.copy_to_clipboard(c, d))
            template_item_layout.addWidget(copy_button)
            
            # 添加到容器
            template_container_layout.addWidget(template_item)
        
        # 添加占位符
        template_container_layout.addStretch()
        
        # 设置滚动区域内容
        scroll_area.setWidget(template_container)
        main_layout.addWidget(scroll_area)
        
        # 显示弹窗
        dialog.exec()
    
    def copy_to_clipboard(self, text, dialog=None):
        """复制文本到剪贴板
        
        Args:
            text: 要复制的文本
            dialog: 弹窗对象，用于显示提示
        """
        from PyQt6.QtGui import QGuiApplication
        
        # 复制到剪贴板
        clipboard = QGuiApplication.clipboard()
        clipboard.setText(text)
        
        # 显示复制成功提示
        if dialog:
            # 如果有弹窗，在弹窗状态栏显示提示
            status_bar = dialog.statusBar() if hasattr(dialog, 'statusBar') else self.statusBar()
            status_bar.showMessage("提示词已复制到剪贴板")
            QTimer.singleShot(1000, lambda: status_bar.showMessage(""))
        else:
            # 否则在主窗口状态栏显示提示
            self.statusBar().showMessage("提示词已复制到剪贴板")
            QTimer.singleShot(1000, lambda: self.statusBar().showMessage("就绪"))
    
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
        
        # AI服务选择器
        service_layout = QHBoxLayout()
        service_label = QLabel("AI服务:")
        service_label.setFixedWidth(60)
        service_label.setStyleSheet("font-size: 11px;")
        service_layout.addWidget(service_label)
        self.ai_service_combo = QComboBox()
        self.ai_service_combo.addItem("DeepSeek", "deepseek")
        self.ai_service_combo.addItem("豆包", "doubao")
        self.ai_service_combo.addItem("Kimi", "kimi")
        self.ai_service_combo.addItem("通义千问", "qianwen")
        self.ai_service_combo.setFixedHeight(25)
        self.ai_service_combo.setStyleSheet("font-size: 11px;")
        self.ai_service_combo.currentIndexChanged.connect(self.on_ai_service_changed)
        service_layout.addWidget(self.ai_service_combo)
        service_layout.addStretch()
        
        api_layout.addLayout(service_layout)
        
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
        self.api_status_label = QLabel("请选择AI服务并输入API密钥")
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
        self.write_mode_combo.addItem("光标补写", "cursor")
        self.write_mode_combo.setFixedHeight(25)
        self.write_mode_combo.setStyleSheet("font-size: 11px;")
        write_mode_layout.addWidget(self.write_mode_combo)
        write_mode_layout.addStretch()
        
        doc_layout.addLayout(write_mode_layout)
        
        # 动态效果开关
        effect_layout = QHBoxLayout()
        effect_label = QLabel("动态效果:")
        effect_label.setFixedWidth(70)
        effect_label.setStyleSheet("font-size: 11px;")
        effect_layout.addWidget(effect_label)
        self.dynamic_effects_checkbox = QCheckBox()
        self.dynamic_effects_checkbox.setChecked(True)  # 默认开启
        self.dynamic_effects_checkbox.setStyleSheet("font-size: 11px;")
        effect_layout.addWidget(self.dynamic_effects_checkbox)
        effect_layout.addStretch()
        
        doc_layout.addLayout(effect_layout)
        

        
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
        
        # 提示词模板按钮
        template_button = QPushButton("提示词模板")
        template_button.clicked.connect(self.show_prompt_templates)
        template_button.setFixedHeight(30)
        template_button.setStyleSheet("font-size: 12px;")
        help_layout.addWidget(template_button)
        
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
        # 加载AI服务类型
        ai_service = self.config.get('ai_service', 'deepseek')
        index = self.ai_service_combo.findData(ai_service)
        if index >= 0:
            self.ai_service_combo.setCurrentIndex(index)
        
        # 加载对应服务的API密钥
        api_key = self.config.get(f"{ai_service}_api_key", "")
        self.api_key_input.setText(api_key)
        
        # 加载文档路径
        if 'document_path' in self.config:
            self.doc_path_input.setText(self.config['document_path'])
        
        # 加载写入模式
        if 'write_mode' in self.config:
            write_mode = self.config['write_mode']
            index = self.write_mode_combo.findData(write_mode)
            if index >= 0:
                self.write_mode_combo.setCurrentIndex(index)
        
        # 加载动态效果开关
        if 'dynamic_effects_enabled' in self.config:
            self.dynamic_effects_checkbox.setChecked(self.config['dynamic_effects_enabled'])
            self.minimize_ball.set_dynamic_effects(self.config['dynamic_effects_enabled'])
        else:
            self.dynamic_effects_checkbox.setChecked(True)  # 默认开启
            self.minimize_ball.set_dynamic_effects(True)
        
        # 加载主题提示词
        if 'templates' in self.config and 'default' in self.config['templates']:
            self.template_editor.setPlainText(self.config['templates']['default'])
    
    def on_ai_service_changed(self):
        """AI服务选择改变时的处理"""
        # 获取当前选择的AI服务
        ai_service = self.ai_service_combo.currentData()
        
        # 加载对应服务的API密钥
        api_key = self.config.get(f"{ai_service}_api_key", "")
        self.api_key_input.setText(api_key)
        
        # 更新状态标签
        self.api_status_label.setText(f"请输入并验证{ai_service} API密钥")
    
    def validate_api_key(self):
        """验证API密钥"""
        # 获取当前选择的AI服务
        ai_service = self.ai_service_combo.currentData()
        api_key = self.api_key_input.text().strip()
        
        if not api_key:
            QMessageBox.warning(self, "警告", "请输入API密钥")
            return
        
        # 调用API服务验证密钥
        try:
            is_valid = self.api_service.validate_key(api_key, ai_service)
            if is_valid:
                self.api_status_label.setText(f"✓ {ai_service} API密钥有效")
                self.api_status_label.setStyleSheet("color: green")
                QMessageBox.information(self, "成功", f"{ai_service} API密钥验证成功")
            else:
                self.api_status_label.setText(f"✗ {ai_service} API密钥无效")
                self.api_status_label.setStyleSheet("color: red")
                QMessageBox.critical(self, "错误", f"{ai_service} API密钥验证失败")
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
            # 获取当前选择的AI服务
            ai_service = self.ai_service_combo.currentData()
            
            # 获取API密钥
            api_key = self.api_key_input.text().strip()
            if not api_key:
                QMessageBox.warning(self, "警告", "请输入API密钥")
                return
            
            # 保存AI服务类型和API密钥
            self.config['ai_service'] = ai_service
            self.config[f"{ai_service}_api_key"] = api_key
            
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
            
            # 获取动态效果开关状态
            dynamic_effects_enabled = self.dynamic_effects_checkbox.isChecked()
            self.config['dynamic_effects_enabled'] = dynamic_effects_enabled
            
            # 更新最小化球的动态效果设置
            self.minimize_ball.set_dynamic_effects(dynamic_effects_enabled)
            
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
        
        # 根据进度文本设置状态
        if "处理中" in progress_text or "生成中" in progress_text or "写入中" in progress_text:
            self.minimize_ball.set_status(self.minimize_ball.STATUS_PROCESSING)
        elif "已完成" in progress_text or "成功" in progress_text:
            self.minimize_ball.set_status(self.minimize_ball.STATUS_COMPLETED)
        elif "已失败" in progress_text or "错误" in progress_text:
            self.minimize_ball.set_status(self.minimize_ball.STATUS_ERROR)
        else:
            self.minimize_ball.set_status(self.minimize_ball.STATUS_STANDBY)
    
    def closeEvent(self, event):
        """窗口关闭事件
        
        由于移除了托盘功能，现在窗口关闭时应该正常退出应用
        """
        # 正常接受关闭事件，允许窗口关闭
        event.accept()
        # 通知应用退出
        from PyQt6.QtCore import QCoreApplication
        QCoreApplication.quit()