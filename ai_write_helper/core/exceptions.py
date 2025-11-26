#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""自定义异常模块

该模块定义应用中使用的自定义异常类，提供统一的错误处理机制。
"""


class AIWriteHelperError(Exception):
    """应用程序基础异常类"""
    
    def __init__(self, message: str, error_code: str = "UNKNOWN_ERROR", **kwargs):
        """初始化异常
        
        Args:
            message: 错误消息
            error_code: 错误代码
            **kwargs: 其他附加信息
        """
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = kwargs
    
    def __str__(self) -> str:
        """返回异常的字符串表示"""
        details_str = ", ".join([f"{k}={v}" for k, v in self.details.items()])
        if details_str:
            return f"[{self.error_code}] {self.message} ({details_str})"
        return f"[{self.error_code}] {self.message}"


class APIError(AIWriteHelperError):
    """API相关异常"""
    
    def __init__(self, message: str, error_code: str = "API_ERROR", **kwargs):
        super().__init__(message, error_code, **kwargs)


class AuthenticationError(APIError):
    """认证相关异常"""
    
    def __init__(self, message: str = "认证失败", error_code: str = "AUTH_ERROR", **kwargs):
        super().__init__(message, error_code, **kwargs)


class ConfigurationError(AIWriteHelperError):
    """配置相关异常"""
    
    def __init__(self, message: str, error_code: str = "CONFIG_ERROR", **kwargs):
        super().__init__(message, error_code, **kwargs)


class DocumentError(AIWriteHelperError):
    """文档操作相关异常"""
    
    def __init__(self, message: str, error_code: str = "DOCUMENT_ERROR", **kwargs):
        super().__init__(message, error_code, **kwargs)


class EncryptionError(AIWriteHelperError):
    """加密相关异常"""
    
    def __init__(self, message: str, error_code: str = "ENCRYPTION_ERROR", **kwargs):
        super().__init__(message, error_code, **kwargs)


class ListenerError(AIWriteHelperError):
    """监听器相关异常"""
    
    def __init__(self, message: str, error_code: str = "LISTENER_ERROR", **kwargs):
        super().__init__(message, error_code, **kwargs)


class UIError(AIWriteHelperError):
    """UI相关异常"""
    
    def __init__(self, message: str, error_code: str = "UI_ERROR", **kwargs):
        super().__init__(message, error_code, **kwargs)


class ValidationError(AIWriteHelperError):
    """数据验证相关异常"""
    
    def __init__(self, message: str, error_code: str = "VALIDATION_ERROR", **kwargs):
        super().__init__(message, error_code, **kwargs)


class TimeoutError(AIWriteHelperError):
    """超时相关异常"""
    
    def __init__(self, message: str = "操作超时", error_code: str = "TIMEOUT_ERROR", **kwargs):
        super().__init__(message, error_code, **kwargs)


class ResourceNotFoundError(AIWriteHelperError):
    """资源未找到异常"""
    
    def __init__(self, message: str, error_code: str = "RESOURCE_NOT_FOUND", **kwargs):
        super().__init__(message, error_code, **kwargs)


class PermissionError(AIWriteHelperError):
    """权限相关异常"""
    
    def __init__(self, message: str, error_code: str = "PERMISSION_ERROR", **kwargs):
        super().__init__(message, error_code, **kwargs)


class SystemError(AIWriteHelperError):
    """系统相关异常"""
    
    def __init__(self, message: str, error_code: str = "SYSTEM_ERROR", **kwargs):
        super().__init__(message, error_code, **kwargs)