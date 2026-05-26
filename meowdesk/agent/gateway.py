"""
Agent Gateway - 连接本地 AI Agent (OpenClaw, Hermes 等)
"""

import json
import requests
from typing import Dict, Any, Optional, List
from enum import Enum


class AgentType(Enum):
    """支持的 Agent 类型"""
    OPENCLAW = "openclaw"
    HERMES = "hermes"
    CUSTOM = "custom"


class AgentGateway:
    """Agent 网关 - 统一接口连接不同的本地 Agent"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化 Agent 网关
        
        Args:
            config: 配置字典，包含：
                - agent_type: Agent 类型 (openclaw/hermes/custom)
                - endpoint: Agent API 地址
                - api_key: API 密钥（如需要）
                - timeout: 请求超时时间
        """
        self.agent_type = AgentType(config.get('agent_type', 'openclaw'))
        self.endpoint = config.get('endpoint', 'http://localhost:8080')
        self.api_key = config.get('api_key')
        self.timeout = config.get('timeout', 30)
        self.enabled = config.get('enabled', False)
    
    def is_available(self) -> bool:
        """检查 Agent 是否可用"""
        if not self.enabled:
            return False
        
        try:
            response = requests.get(
                f"{self.endpoint}/health",
                timeout=3
            )
            return response.status_code == 200
        except Exception:
            return False
    
    def chat(self, message: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """
        发送对话消息
        
        Args:
            message: 用户消息
            context: 上下文信息（可选）
            
        Returns:
            Agent 响应字典：
                - success: 是否成功
                - response: Agent 回复
                - actions: 建议的操作列表
                - error: 错误信息（如有）
        """
        if not self.enabled:
            return {
                'success': False,
                'error': 'Agent 未启用'
            }
        
        try:
            payload = {
                'message': message,
                'context': context or {}
            }
            
            headers = {}
            if self.api_key:
                headers['Authorization'] = f'Bearer {self.api_key}'
            
            response = requests.post(
                f"{self.endpoint}/chat",
                json=payload,
                headers=headers,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                return {
                    'success': True,
                    **response.json()
                }
            else:
                return {
                    'success': False,
                    'error': f'HTTP {response.status_code}: {response.text}'
                }
                
        except requests.Timeout:
            return {
                'success': False,
                'error': 'Agent 响应超时'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def execute_command(self, command: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """
        执行命令
        
        Args:
            command: 命令名称（如 'clean_disk', 'check_date'）
            params: 命令参数
            
        Returns:
            执行结果字典
        """
        if not self.enabled:
            return {
                'success': False,
                'error': 'Agent 未启用'
            }
        
        try:
            payload = {
                'command': command,
                'params': params or {}
            }
            
            headers = {}
            if self.api_key:
                headers['Authorization'] = f'Bearer {self.api_key}'
            
            response = requests.post(
                f"{self.endpoint}/execute",
                json=payload,
                headers=headers,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                return {
                    'success': True,
                    **response.json()
                }
            else:
                return {
                    'success': False,
                    'error': f'HTTP {response.status_code}: {response.text}'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_suggestions(self, context: Dict[str, Any]) -> List[str]:
        """
        获取智能建议
        
        Args:
            context: 当前上下文（文件统计、用户习惯等）
            
        Returns:
            建议列表
        """
        if not self.enabled or not self.is_available():
            return []
        
        try:
            response = requests.post(
                f"{self.endpoint}/suggestions",
                json={'context': context},
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get('suggestions', [])
            
        except Exception:
            pass
        
        return []
