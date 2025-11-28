#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""API服务模块

该模块实现与DeepSeek API的通信功能，包括密钥验证、请求构造、响应解析等。
"""

import logging
import requests
import time
import json
from threading import RLock
from typing import Dict, Any, Optional

# 内置提示词模板（不体现在UI）
# 全量重写模式提示词
REWRITE_PROMPT_TEMPLATE = """
你是一个专业的文本优化助手。请根据用户提供的选中文本和文档内容，结合指定的主题要求，对整个文档进行全面重写和优化。

## 要求：
1. **综合分析**：仔细分析选中文本和整个文档的内容，理解上下文和逻辑关系
2. **主题一致**：确保生成的内容与用户指定的主题提示词保持一致
3. **内容完整**：重写后的文档应包含原文档的核心信息，并根据选中文本进行深入扩展
4. **格式规范**：保持文档格式整洁规范，段落清晰，易于阅读
5. **语言流畅**：确保语言表达自然流畅，逻辑连贯
6. **重写范围**：必须对整个文档进行重写，而不是仅修改选中文本部分

## 用户输入信息：

### 选中文本（需要重点关注）：
{selected_text}

### 文档内容（需要整体考虑）：
{document_content}

### 主题要求（如有）：
{theme_prompt}

请生成完整的重写后文档内容，确保内容全面、专业且符合上述所有要求。不要输出任何多余的解释说明，只返回最终的重写文档内容。
"""

# 增量写入模式提示词
INCREMENTAL_PROMPT_TEMPLATE = """
你是一个专业的文本补写助手。请根据用户提供的选中文本和文档内容，结合指定的主题要求，生成增量补写内容。

## 要求：
1. **上下文关联**：仔细分析选中文本和文档内容，理解上下文和逻辑关系
2. **主题一致**：确保生成的内容与用户指定的主题提示词保持一致
3. **增量补写**：仅生成补写内容，不要重复原文档内容
4. **自然衔接**：生成的内容应与原文档自然衔接，保持逻辑连贯
5. **语言流畅**：确保语言表达自然流畅
6. **内容扩展**：根据选中文本和主题要求进行合理扩展

## 用户输入信息：

### 选中文本（需要重点关注）：
{selected_text}

### 文档内容（需要关联上下文）：
{document_content}

### 主题要求（如有）：
{theme_prompt}

请生成增量补写内容，确保内容与原文档自然衔接，符合上述所有要求。不要输出任何多余的解释说明，只返回最终的补写内容。
"""

# 光标补写模式提示词
CURSOR_PROMPT_TEMPLATE = """
你是一个专业的文本补写助手。请根据用户提供的选中文本和文档内容，结合指定的主题要求，生成光标处的补写内容。

## 要求：
1. **上下文关联**：仔细分析选中文本和文档内容，理解上下文和逻辑关系
2. **主题一致**：确保生成的内容与用户指定的主题提示词保持一致
3. **精准补写**：仅生成光标处的补写内容，不要重复原文档内容
4. **自然衔接**：生成的内容应与原文档自然衔接，保持逻辑连贯
5. **语言流畅**：确保语言表达自然流畅
6. **内容扩展**：根据选中文本和主题要求进行合理扩展
7. **不改变上下文**：绝对不能修改或重写原文档的上下文内容

## 用户输入信息：

### 选中文本（需要重点关注）：
{selected_text}

### 文档内容（需要关联上下文）：
{document_content}

### 主题要求（如有）：
{theme_prompt}

请生成光标处的补写内容，确保内容与原文档自然衔接，符合上述所有要求。不要输出任何多余的解释说明，只返回最终的补写内容。
"""


class APIService:
    """API服务类，负责与各种AI服务进行通信"""
    
    # AI服务类型常量
    SERVICE_DEEPSEEK = "deepseek"
    SERVICE_DOUBAO = "doubao"
    SERVICE_KIMI = "kimi"
    SERVICE_QIANWEN = "qianwen"
    
    # API端点配置
    API_CONFIGS = {
        SERVICE_DEEPSEEK: {
            "base_url": "https://api.deepseek.com",
            "completion_endpoint": "/v1/chat/completions",
            "default_model": "deepseek-chat",
            "auth_header": "Authorization",
            "auth_prefix": "Bearer "
        },
        SERVICE_DOUBAO: {
            "base_url": "https://api.doubao.com",
            "completion_endpoint": "/api/v1/chat/completions",
            "default_model": "doubao-pro-4k",
            "auth_header": "Authorization",
            "auth_prefix": "Bearer "
        },
        SERVICE_KIMI: {
            "base_url": "https://api.moonshot.cn",
            "completion_endpoint": "/v1/chat/completions",
            "default_model": "moonshot-v1-8k",
            "auth_header": "Authorization",
            "auth_prefix": "Bearer "
        },
        SERVICE_QIANWEN: {
            "base_url": "https://dashscope.aliyuncs.com",
            "completion_endpoint": "/api/v1/services/aigc/text-generation/generation",
            "default_model": "qwen-turbo",
            "auth_header": "Authorization",
            "auth_prefix": "Bearer "
        }
    }
    
    # 默认模型参数
    DEFAULT_MAX_TOKENS = 2000
    DEFAULT_TEMPERATURE = 0.7
    
    # 重试配置
    MAX_RETRIES = 3
    RETRY_DELAY = 2  # 初始重试延迟（秒）
    RETRY_BACKOFF = 1.5  # 退避因子
    
    def __init__(self, config_manager):
        """初始化API服务
        
        Args:
            config_manager: 配置管理器实例
        """
        self.logger = logging.getLogger("ai_write_helper.api")
        self.config_manager = config_manager
        self.lock = RLock()
        
        # 会话对象，用于复用连接
        self.session = requests.Session()
        # 设置默认请求头
        self.session.headers.update({
            "Content-Type": "application/json",
            "Accept": "application/json"
        })
    
    def validate_key(self, api_key: str, ai_service: str = SERVICE_DEEPSEEK) -> bool:
        """验证API密钥是否有效
        
        Args:
            api_key: API密钥
            ai_service: AI服务类型
            
        Returns:
            bool: 如果密钥有效返回True，否则返回False
        """
        self.logger.info(f"开始验证{ai_service} API密钥")
        
        try:
            # 构造一个简单的验证请求
            test_prompt = "请验证此API密钥是否有效"
            response = self._send_request(
                ai_service=ai_service,
                api_key=api_key,
                prompt=test_prompt,
                max_tokens=1
            )
            
            # 检查响应是否成功
            if ai_service == self.SERVICE_QIANWEN:
                # 通义千问的响应格式
                if response and "output" in response:
                    self.logger.info(f"{ai_service} API密钥验证成功")
                    return True
            else:
                # 通用响应格式
                if response and "choices" in response and len(response["choices"]) > 0:
                    self.logger.info(f"{ai_service} API密钥验证成功")
                    return True
            
            self.logger.warning(f"{ai_service} API密钥验证失败：无效的响应")
            return False
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"{ai_service} API密钥验证时发生网络错误: {str(e)}")
            # 如果是401错误，说明密钥无效
            if hasattr(e, 'response') and e.response and e.response.status_code == 401:
                return False
            # 其他网络错误可能是临时问题
            raise
        except Exception as e:
            self.logger.error(f"{ai_service} API密钥验证时发生未知错误: {str(e)}")
            raise
    
    def generate_content(self, selected_text: str, document_content: str, theme_prompt: str = "", write_mode: str = "incremental", **kwargs) -> str:
        """生成内容
        
        Args:
            selected_text: 用户选中的文本
            document_content: 文档内容
            theme_prompt: 用户自定义的主题提示词
            write_mode: 写入模式，可选值：incremental, overwrite, cursor
            **kwargs: 额外参数
            
        Returns:
            str: 生成的内容
        """
        self.logger.info(f"开始生成AI内容，写入模式: {write_mode}")
        
        # 从配置中获取API密钥和AI服务类型
        config = self.config_manager.load_config()
        ai_service = config.get("ai_service", self.SERVICE_DEEPSEEK)
        api_key = config.get(f"{ai_service}_api_key")
        
        if not api_key:
            raise ValueError(f"{ai_service} API密钥未配置")
        
        try:
            # 构造完整提示词
            prompt = self._construct_prompt(selected_text, document_content, theme_prompt, write_mode)
            
            # 发送请求
            response = self._send_request(
                ai_service=ai_service,
                api_key=api_key,
                prompt=prompt,
                **kwargs
            )
            
            # 解析响应
            content = self._parse_response(response, ai_service)
            
            # 清理生成的内容
            cleaned_content = self._clean_generated_content(content)
            
            self.logger.info(f"AI内容生成成功，生成长度: {len(cleaned_content)} 字符")
            return cleaned_content
            
        except Exception as e:
            self.logger.error(f"生成AI内容时出错: {str(e)}")
            raise
            
    def _construct_prompt(self, selected_text: str, document_content: str, theme_prompt: str, write_mode: str) -> str:
        """构造提示词
        
        Args:
            selected_text: 用户选中的文本
            document_content: 文档内容
            theme_prompt: 用户自定义的主题提示词
            write_mode: 写入模式
            
        Returns:
            str: 构造好的提示词
        """
        # 智能管理上下文长度
        max_doc_length = 4000  # 根据API限制调整
        if len(document_content) > max_doc_length:
            # 保留文档的开头和结尾，确保上下文连贯
            half_max = max_doc_length // 2
            document_content = (
                document_content[:half_max] + 
                "\n...[内容过长，已省略部分]...\n" + 
                document_content[-half_max:]
            )
            self.logger.warning(f"文档内容过长，已截断至 {max_doc_length} 字符")
        
        # 处理主题提示词，如果为空则提供默认值
        if not theme_prompt.strip():
            theme_prompt = "无特定主题要求，请保持原文档的专业风格和内容方向"
        
        # 根据写入模式选择不同的提示词模板
        if write_mode == "overwrite":
            template = REWRITE_PROMPT_TEMPLATE
        elif write_mode == "cursor":
            template = CURSOR_PROMPT_TEMPLATE
        else:  # incremental
            template = INCREMENTAL_PROMPT_TEMPLATE
        
        # 替换模板变量
        prompt = template.replace(
            "{selected_text}", 
            selected_text
        ).replace(
            "{document_content}", 
            document_content
        ).replace(
            "{theme_prompt}", 
            theme_prompt
        )
        
        self.logger.debug(f"构造完成的提示词长度: {len(prompt)} 字符")
        return prompt
    
    def _clean_generated_content(self, content: str) -> str:
        """清理生成的内容，移除可能的标记和额外信息
        
        Args:
            content: 生成的内容
            
        Returns:
            str: 清理后的内容
        """
        # 移除可能的Markdown代码块标记
        lines = content.strip().split('\n')
        cleaned_lines = []
        
        # 需要移除的标记文本
        remove_patterns = [
            "### 选中文本",
            "### 文档内容",
            "### 主题要求",
            "选中文本（需要重点关注）",
            "文档内容（需要整体考虑）",
            "主题要求（如有）",
            "你是一个专业的文本优化助手",
            "请生成完整的重写后文档内容",
            "不要输出任何多余的解释说明"
        ]
        
        # 标记是否处于需要跳过的文本块
        skip_block = False
        
        for line in lines:
            # 跳过空行（保留实际内容的空行）
            stripped_line = line.strip()
            
            # 跳过代码块标记
            if stripped_line.startswith('```'):
                continue
            
            # 检查是否包含需要移除的标记
            skip_this_line = False
            for pattern in remove_patterns:
                if pattern in stripped_line:
                    skip_this_line = True
                    break
            
            # 跳过以 ## 开头的标题行（提示词中的要求列表）
            if stripped_line.startswith('## '):
                skip_this_line = True
            
            # 跳过以数字+点开头的列表项（提示词中的要求项）
            if stripped_line and stripped_line[0].isdigit() and '.' in stripped_line:
                parts = stripped_line.split('.', 1)
                if len(parts) > 0 and parts[0].isdigit():
                    skip_this_line = True
            
            # 跳过提示词模板中的特殊标记行
            if not skip_this_line:
                cleaned_lines.append(line)
        
        # 重新组合内容
        cleaned_content = '\n'.join(cleaned_lines).strip()
        
        # 移除连续的空行
        while '\n\n\n' in cleaned_content:
            cleaned_content = cleaned_content.replace('\n\n\n', '\n\n')
        
        return cleaned_content
    
    def _send_request(self, ai_service: str, api_key: str, prompt: str, **kwargs) -> Dict[str, Any]:
        """发送API请求
        
        Args:
            ai_service: AI服务类型
            api_key: API密钥
            prompt: 提示词
            **kwargs: 额外参数
            
        Returns:
            Dict[str, Any]: API响应
        """
        # 获取API配置
        api_config = self.API_CONFIGS.get(ai_service, self.API_CONFIGS[self.SERVICE_DEEPSEEK])
        
        # 构造请求参数
        request_data = self._build_request_data(prompt, ai_service, **kwargs)
        
        # 设置认证头
        headers = {
            api_config["auth_header"]: f"{api_config['auth_prefix']}{api_key}"
        }
        
        # 重试逻辑
        retry_count = 0
        delay = self.RETRY_DELAY
        
        while retry_count < self.MAX_RETRIES:
            try:
                with self.lock:
                    # 发送请求
                    self.logger.debug(f"发送{ai_service} API请求，尝试 {retry_count + 1}/{self.MAX_RETRIES}")
                    response = self.session.post(
                        api_config["base_url"] + api_config["completion_endpoint"],
                        json=request_data,
                        headers=headers,
                        timeout=30  # 30秒超时
                    )
                
                # 检查响应状态
                response.raise_for_status()
                
                # 返回JSON响应
                return response.json()
                
            except requests.exceptions.HTTPError as e:
                # 处理HTTP错误
                if hasattr(e, 'response'):
                    status_code = e.response.status_code
                    
                    # 401: 认证错误，不重试
                    if status_code == 401:
                        self.logger.error(f"{ai_service} API认证失败，请检查API密钥")
                        raise ValueError(f"{ai_service} API密钥无效")
                    
                    # 429: 请求频率限制，需要重试
                    elif status_code == 429:
                        retry_count += 1
                        wait_time = delay * (self.RETRY_BACKOFF ** (retry_count - 1))
                        self.logger.warning(
                            f"{ai_service} 请求频率限制，{wait_time:.2f}秒后重试..."
                        )
                        time.sleep(wait_time)
                        continue
                    
                    # 其他HTTP错误
                    self.logger.error(
                        f"{ai_service} HTTP错误: {status_code} - {e.response.text}"
                    )
                    raise
                
            except requests.exceptions.Timeout as e:
                # 超时错误，重试
                retry_count += 1
                wait_time = delay * (self.RETRY_BACKOFF ** (retry_count - 1))
                self.logger.warning(f"{ai_service} 请求超时，{wait_time:.2f}秒后重试...")
                time.sleep(wait_time)
                continue
                
            except requests.exceptions.RequestException as e:
                # 其他网络错误，重试
                retry_count += 1
                wait_time = delay * (self.RETRY_BACKOFF ** (retry_count - 1))
                self.logger.warning(
                    f"{ai_service} 网络错误: {str(e)}，{wait_time:.2f}秒后重试..."
                )
                time.sleep(wait_time)
                continue
        
        # 达到最大重试次数
        raise Exception(f"{ai_service} 达到最大重试次数 ({self.MAX_RETRIES})，请求失败")
    
    def _build_request_data(self, prompt: str, ai_service: str = SERVICE_DEEPSEEK, **kwargs) -> Dict[str, Any]:
        """构建请求数据
        
        Args:
            prompt: 提示词
            ai_service: AI服务类型
            **kwargs: 额外参数
            
        Returns:
            Dict[str, Any]: 请求数据字典
        """
        # 获取API配置
        api_config = self.API_CONFIGS.get(ai_service, self.API_CONFIGS[self.SERVICE_DEEPSEEK])
        
        # 基础请求数据
        request_data = {
            "model": kwargs.get("model", api_config["default_model"]),
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "max_tokens": kwargs.get("max_tokens", self.DEFAULT_MAX_TOKENS),
            "temperature": kwargs.get("temperature", self.DEFAULT_TEMPERATURE),
            "top_p": kwargs.get("top_p", 0.95),
            "n": kwargs.get("n", 1),
            "stream": kwargs.get("stream", False)
        }
        
        # 添加可选参数
        if "stop" in kwargs:
            request_data["stop"] = kwargs["stop"]
        
        if "presence_penalty" in kwargs:
            request_data["presence_penalty"] = kwargs["presence_penalty"]
        
        if "frequency_penalty" in kwargs:
            request_data["frequency_penalty"] = kwargs["frequency_penalty"]
        
        # 针对不同AI服务的特殊处理
        if ai_service == self.SERVICE_QIANWEN:
            # 通义千问的请求格式略有不同
            request_data = {
                "model": request_data["model"],
                "input": {
                    "messages": request_data["messages"]
                },
                "parameters": {
                    "max_tokens": request_data["max_tokens"],
                    "temperature": request_data["temperature"],
                    "top_p": request_data["top_p"]
                }
            }
        
        return request_data
    
    def _parse_response(self, response: Dict[str, Any], ai_service: str = SERVICE_DEEPSEEK) -> str:
        """解析API响应
        
        Args:
            response: API响应字典
            ai_service: AI服务类型
            
        Returns:
            str: 解析后的内容
        """
        try:
            # 针对不同AI服务的响应格式进行解析
            if ai_service == self.SERVICE_QIANWEN:
                # 通义千问的响应格式
                if "output" not in response:
                    raise ValueError("响应中没有生成的内容")
                return response["output"]["text"].strip()
            else:
                # 通用响应格式（DeepSeek、Doubao、Kimi等）
                # 检查响应结构
                if "choices" not in response or not response["choices"]:
                    raise ValueError("响应中没有生成的内容")
                
                # 获取生成的内容
                choice = response["choices"][0]
                
                # 检查响应格式
                if "message" in choice and "content" in choice["message"]:
                    content = choice["message"]["content"]
                elif "text" in choice:
                    content = choice["text"]
                else:
                    raise ValueError("无法从响应中提取内容")
                
                # 去除首尾空白
                return content.strip()
            
        except (KeyError, IndexError, ValueError) as e:
            self.logger.error(f"解析{ai_service} API响应时出错: {str(e)}")
            raise ValueError(f"无效的{ai_service} API响应格式: {str(e)}")
    
    def close(self):
        """关闭会话，释放资源"""
        if hasattr(self, 'session'):
            self.session.close()
            self.logger.info("API服务会话已关闭")
    
    def __del__(self):
        """析构函数，确保会话被关闭"""
        self.close()