#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""文本监听服务模块

该模块实现全局文本划选和Enter键组合触发监听系统，支持跨应用程序环境下的响应。
"""

import logging
import threading
import time
from pynput import keyboard, mouse
from pynput.keyboard import Key
from pynput.mouse import Button
from PyQt6.QtCore import pyqtSignal, QObject


class TextMonitorService(QObject):
    """文本监听服务，负责监听全局文本划选和Enter键组合触发"""
    
    # 信号定义
    processing_started = pyqtSignal()
    processing_completed = pyqtSignal(str)
    processing_failed = pyqtSignal(str)
    progress_updated = pyqtSignal(str)  # 进度更新信号
    minimize_signal = pyqtSignal()  # 最小化信号
    restore_signal = pyqtSignal()  # 恢复信号
    
    def __init__(self, config_manager, api_service, document_service):
        """初始化文本监听服务
        
        Args:
            config_manager: 配置管理器实例
            api_service: API服务实例
            document_service: 文档服务实例
        """
        super().__init__()
        self.logger = logging.getLogger("ai_write_helper.text_monitor")
        self.config_manager = config_manager
        self.api_service = api_service
        self.document_service = document_service
        
        # 状态变量
        self.running = False
        self.is_selecting = False
        self.last_select_time = 0
        self.is_processing = False  # 防抖标志，避免并发处理
        self.lock = threading.RLock()
        
        # 监听器
        self.keyboard_listener = None
        self.mouse_listener = None
        
        # 主窗口引用
        self.main_window = None
    
    def start(self):
        """启动监听服务"""
        self.logger.info("启动文本监听服务")
        
        with self.lock:
            if self.running:
                self.logger.warning("监听服务已经在运行")
                return
            
            self.running = True
        
        try:
            # 启动鼠标监听
            self.mouse_listener = mouse.Listener(
                on_click=self._on_mouse_click,
                on_scroll=self._on_mouse_scroll
            )
            self.mouse_listener.daemon = True
            self.mouse_listener.start()
            
            # 启动键盘监听
            self.keyboard_listener = keyboard.Listener(
                on_press=self._on_key_press,
                on_release=self._on_key_release
            )
            self.keyboard_listener.daemon = True
            self.keyboard_listener.start()
            
            self.logger.info("文本监听服务启动成功")
            
            # 移除阻塞循环，监听器已经在后台线程运行
            # 不需要while循环来保持线程运行，因为监听器本身就是线程
        
        except Exception as e:
            try:
                # 确保使用类的logger属性而不是局部变量
                if hasattr(self, 'logger'):
                    self.logger.error(f"监听服务运行出错: {str(e)}")
                else:
                    # 如果logger未初始化，使用全局logging
                    import logging
                    logging.error(f"监听服务运行出错: {str(e)}")
            except Exception:
                # 如果日志记录也失败了，使用简单的print
                print(f"监听服务运行出错: {str(e)}")
            
            # 安全地停止服务
            try:
                self.stop()
            except Exception:
                pass
    
    def stop(self):
        """停止监听服务"""
        self.logger.info("停止文本监听服务")
        
        with self.lock:
            self.running = False
        
        # 停止监听器
        if self.mouse_listener:
            self.mouse_listener.stop()
            self.mouse_listener.join(timeout=1)
        
        if self.keyboard_listener:
            self.keyboard_listener.stop()
            self.keyboard_listener.join(timeout=1)
        
        self.logger.info("文本监听服务已停止")
    
    def _on_mouse_click(self, x, y, button, pressed):
        """鼠标点击事件处理
        
        Args:
            x, y: 鼠标位置
            button: 鼠标按钮
            pressed: 是否按下
        """
        # 只有左键点击才考虑文本选择
        if button != Button.left:
            return
        
        if pressed:
            # 按下左键，可能开始选择
            self.is_selecting = True
        else:
            # 释放左键，可能结束选择
            self.is_selecting = False
            self.last_select_time = time.time()
    
    def _on_mouse_scroll(self, x, y, dx, dy):
        """鼠标滚轮事件处理
        
        Args:
            x, y: 鼠标位置
            dx: 水平滚动距离
            dy: 垂直滚动距离
        """
        # 滚动时取消选择状态
        with self.lock:
            self.is_selecting = False
    
    def _on_key_press(self, key):
        """键盘按下事件处理
        
        Args:
            key: 按下的键
        """
        # 只处理Enter键
        if key == Key.enter:
            # 检查是否在文本选择后短时间内按下Enter
            time_diff = time.time() - self.last_select_time
            if time_diff > 0 and time_diff < 2:  # 2秒内的选择
                self._handle_selection_enter()
    
    def _on_key_release(self, key):
        """键盘释放事件处理
        
        Args:
            key: 释放的键
        """
        # 不需要特殊处理
        pass
    
    def _handle_selection_enter(self):
        """处理选中文本后按下Enter的事件"""
        # 防抖处理：如果正在处理中，直接返回
        with self.lock:
            if self.is_processing:
                self.logger.warning("正在处理中，忽略重复请求")
                return
            self.is_processing = True
        
        self.logger.info("检测到文本选择后按下Enter键")
        
        try:
            # 发出开始处理信号
            self.processing_started.emit()
            self.progress_updated.emit("处理中")
            
            # 获取选中的文本
            selected_text = self._get_selected_text()
            if not selected_text:
                self.logger.warning("未检测到选中的文本")
                self.processing_failed.emit("未检测到选中的文本")
                self.progress_updated.emit("已失败")
                return
            
            self.logger.info(f"捕获到选中文本，长度: {len(selected_text)} 字符")
            self.progress_updated.emit("生成中")
            
            # 加载配置
            config = self.config_manager.load_config()
            
            # 检查必要配置
            if 'document_path' not in config or not config['document_path']:
                self.logger.error("未配置目标文档路径")
                self.processing_failed.emit("未配置目标文档路径")
                self.progress_updated.emit("失败")
                return
            
            # 读取文档内容
            document_content = self.document_service.read_document(
                config['document_path']
            )
            
            # 检查文档内容是否有效
            if not document_content:
                self.logger.warning(f"读取文档内容为空，长度: {len(document_content)} 字符")
                # 可以选择继续执行或失败，这里选择继续执行但给出警告
            else:
                self.logger.info(f"成功读取文档内容，长度: {len(document_content)} 字符")
            
            # 获取用户自定义的主题提示词（如果有）
            theme_prompt = self._get_theme_prompt(config)
            
            # 调用API获取补写内容，传入选中文本、文档内容和主题提示词
            response = self.api_service.generate_content(
                selected_text=selected_text,
                document_content=document_content,
                theme_prompt=theme_prompt
            )
            
            self.progress_updated.emit("写入中")
            
            # 根据配置决定写入模式
            write_mode = config.get('write_mode', 'incremental')
            incremental = write_mode == 'incremental'
            
            # 写入文档
            self.document_service.write_document(
                config['document_path'],
                response,
                incremental=incremental
            )
            
            # 根据写入模式记录不同的日志
            if incremental:
                self.logger.info("AI补写成功完成，文档已增量更新")
            else:
                self.logger.info("AI补写成功完成，文档已完整重写")
            
            # 发出处理完成信号和进度更新信号
            self.processing_completed.emit("AI补写成功完成")
            self.progress_updated.emit("已完成")
            
        except Exception as e:
            error_msg = f"处理文本选择时出错: {str(e)}"
            self.logger.error(error_msg)
            # 发出处理失败信号
            self.processing_failed.emit(str(e))
            # 添加错误通知
            import traceback
            self.logger.debug(f"错误详情: {traceback.format_exc()}")
        finally:
            # 无论成功失败，都重置处理状态
            with self.lock:
                self.is_processing = False
    
    def _get_selected_text(self):
        """获取当前系统选中的文本
        
        Returns:
            str: 选中的文本，如果没有则返回空字符串
        """
        try:
            import subprocess
            import platform
            
            system = platform.system()
            
            if system == 'Windows':
                max_retries = 2
                retry_delay = 0.2
                
                for retry in range(max_retries + 1):
                    try:
                        # 使用keyboard.Controller模拟复制操作
                        keyboard_controller = keyboard.Controller()
                        
                        # 模拟Ctrl+C复制选中的文本
                        keyboard_controller.press(Key.ctrl)
                        keyboard_controller.press('c')
                        time.sleep(0.1)
                        keyboard_controller.release('c')
                        keyboard_controller.release(Key.ctrl)
                        
                        # 等待剪贴板更新，重试时增加等待时间
                        time.sleep(retry_delay * (retry + 1))
                        
                        # 使用subprocess调用powershell获取剪贴板
                        try:
                            import subprocess
                            # 添加creationflags=subprocess.CREATE_NO_WINDOW参数，隐藏控制台窗口
                            result = subprocess.run(
                                ['powershell', '-command', 'Get-Clipboard'],
                                capture_output=True,
                                text=True,
                                check=False,
                                creationflags=subprocess.CREATE_NO_WINDOW
                            )
                            
                            if result.returncode == 0:
                                text = result.stdout.strip()
                                if text:
                                    if retry > 0 and hasattr(self, 'logger'):
                                        self.logger.info(f"重试获取选中文本成功，重试次数: {retry}")
                                    return text
                                elif retry < max_retries and hasattr(self, 'logger'):
                                    self.logger.warning(f"第{retry+1}次尝试获取选中文本为空，将重试")
                            elif retry < max_retries and hasattr(self, 'logger'):
                                self.logger.warning(f"第{retry+1}次尝试获取剪贴板失败: {result.stderr}，将重试")
                        except Exception as subprocess_error:
                            if retry < max_retries and hasattr(self, 'logger'):
                                self.logger.warning(f"第{retry+1}次尝试执行剪贴板命令失败: {str(subprocess_error)}，将重试")
                    except Exception as e:
                        if retry < max_retries and hasattr(self, 'logger'):
                            self.logger.warning(f"第{retry+1}次尝试获取选中文本失败: {str(e)}，将重试")
                
                # 所有重试都失败
                if hasattr(self, 'logger'):
                    self.logger.error("所有尝试获取选中文本都失败")
                return ""
                
            elif system == 'Darwin':  # macOS
                # macOS系统使用pbcopy和pbpaste命令
                # 模拟按下Command+C
                with keyboard.Controller() as controller:
                    controller.press(Key.cmd)
                    controller.press('c')
                    time.sleep(0.1)
                    controller.release('c')
                    controller.release(Key.cmd)
                # 读取剪贴板内容
                result = subprocess.run(
                    'pbpaste',
                    shell=True,
                    capture_output=True,
                    text=True,
                    check=True
                )
                return result.stdout.strip()
                
            else:
                self.logger.error(f"不支持的操作系统: {system}")
                return ""
                
        except Exception as e:
            self.logger.error(f"获取选中文本时出错: {str(e)}")
            return ""
    
    def _get_theme_prompt(self, config):
        """获取用户自定义的主题提示词
        
        Args:
            config: 配置字典
            
        Returns:
            str: 主题提示词
        """
        # 从配置中获取用户自定义的主题提示词
        if 'templates' in config and config['templates']:
            # 获取第一个模板或空字符串
            theme_prompt = next(iter(config['templates'].values()), "")
            # 如果主题提示词不为空，添加标识
            if theme_prompt.strip():
                self.logger.info(f"使用用户自定义主题提示词，长度: {len(theme_prompt)} 字符")
                return theme_prompt.strip()
        
        # 如果没有用户自定义主题提示词，返回空字符串
        self.logger.info("未使用用户自定义主题提示词")
        return ""

    def is_running(self):
        """检查服务是否正在运行
        
        Returns:
            bool: 服务是否运行中
        """
        with self.lock:
            return self.running