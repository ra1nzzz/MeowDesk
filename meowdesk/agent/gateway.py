"""
Agent Gateway - 连接本地 AI Agent (OpenClaw, Hermes 等)
兼容 macOS / Windows
"""

import json
import sys
from typing import Dict, Any, Optional, List, Callable
from enum import Enum

# 跨平台 HTTP 请求
try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False
    # 使用 urllib 作为后备
    import urllib.request
    import urllib.error


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
        """
        self.agent_type = AgentType(config.get('agent_type', 'openclaw'))
        self.endpoint = config.get('endpoint', 'http://localhost:8080').rstrip('/')
        self.api_key = config.get('api_key')
        self.timeout = config.get('timeout', 30)
        self.enabled = config.get('enabled', False)
    
    def _get_headers(self) -> Dict[str, str]:
        """获取请求头"""
        headers = {'Content-Type': 'application/json'}
        if self.api_key:
            headers['Authorization'] = f'Bearer {self.api_key}'
        return headers
    
    def _request(self, method: str, path: str, data: Optional[Dict] = None) -> Dict[str, Any]:
        """发送 HTTP 请求（跨平台）"""
        url = f"{self.endpoint}{path}"
        headers = self._get_headers()
        
        if HAS_REQUESTS:
            try:
                if method == 'GET':
                    response = requests.get(url, headers=headers, timeout=self.timeout)
                else:
                    response = requests.post(url, json=data, headers=headers, timeout=self.timeout)
                
                return {
                    'success': response.status_code == 200,
                    'status': response.status_code,
                    'data': response.json() if response.status_code == 200 else None,
                    'error': None if response.status_code == 200 else response.text
                }
            except requests.Timeout:
                return {'success': False, 'error': '请求超时'}
            except Exception as e:
                return {'success': False, 'error': str(e)}
        else:
            # urllib 后备方案
            try:
                body = json.dumps(data).encode('utf-8') if data else None
                req = urllib.request.Request(url, data=body, headers=headers, method=method)
                
                with urllib.request.urlopen(req, timeout=self.timeout) as response:
                    return {
                        'success': True,
                        'status': response.status,
                        'data': json.loads(response.read().decode('utf-8')),
                        'error': None
                    }
            except urllib.error.HTTPError as e:
                return {'success': False, 'status': e.code, 'error': str(e)}
            except Exception as e:
                return {'success': False, 'error': str(e)}
    
    def is_available(self) -> bool:
        """检查 Agent 是否可用"""
        if not self.enabled:
            return False
        
        result = self._request('GET', '/health')
        return result.get('success', False)
    
    def chat(self, message: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """发送对话消息"""
        if not self.enabled:
            return {'success': False, 'error': 'Agent 未启用'}
        
        payload = {
            'message': message,
            'context': context or {}
        }
        
        result = self._request('POST', '/chat', payload)
        
        if result['success']:
            return {
                'success': True,
                **result['data']
            }
        else:
            return {
                'success': False,
                'error': result.get('error', '未知错误')
            }
    
    def chat_stream(self, message: str, context: Optional[Dict] = None, 
                    on_token: Optional[Callable] = None) -> Dict[str, Any]:
        """SSE 流式对话（如支持）"""
        # 先尝试普通请求，SSE 可以后续扩展
        return self.chat(message, context)
    
    def execute_command(self, command: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """执行命令"""
        if not self.enabled:
            return {'success': False, 'error': 'Agent 未启用'}
        
        payload = {
            'command': command,
            'params': params or {}
        }
        
        result = self._request('POST', '/execute', payload)
        
        if result['success']:
            return {'success': True, **result['data']}
        else:
            return {'success': False, 'error': result.get('error', '未知错误')}
    
    def get_suggestions(self, context: Dict[str, Any]) -> List[str]:
        """获取智能建议"""
        if not self.enabled or not self.is_available():
            return []
        
        result = self._request('POST', '/suggestions', {'context': context})
        
        if result['success'] and result.get('data'):
            return result['data'].get('suggestions', [])
        
        return []
