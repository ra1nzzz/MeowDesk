"""
Agent Gateway - 连接本地 AI Agent (OpenClaw, Hermes 等)
兼容 macOS / Windows
"""

import json
from typing import Dict, Any, Optional, List, Callable
from enum import Enum

# 跨平台 HTTP 请求
try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False
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
        self.agent_type = AgentType(config.get('agent_type', 'openclaw'))
        self.endpoint = config.get('endpoint', 'http://localhost:8080').rstrip('/')
        self.api_key = config.get('api_key')
        self.timeout = config.get('timeout', 30)
        self.enabled = config.get('enabled', False)
    
    @property
    def headers(self) -> Dict[str, str]:
        """获取请求头"""
        h = {'Content-Type': 'application/json'}
        if self.api_key:
            h['Authorization'] = f'Bearer {self.api_key}'
        return h
    
    def _request(self, method: str, path: str, data: Optional[Dict] = None) -> Dict[str, Any]:
        """发送 HTTP 请求（跨平台）"""
        url = f"{self.endpoint}{path}"
        
        if HAS_REQUESTS:
            return self._request_with_requests(method, url, data)
        return self._request_with_urllib(method, url, data)
    
    def _request_with_requests(self, method: str, url: str, data: Optional[Dict]) -> Dict[str, Any]:
        """使用 requests 库发送请求"""
        try:
            if method == 'GET':
                resp = requests.get(url, headers=self.headers, timeout=self.timeout)
            else:
                resp = requests.post(url, json=data, headers=self.headers, timeout=self.timeout)
            
            return {
                'success': resp.status_code == 200,
                'status': resp.status_code,
                'data': resp.json() if resp.status_code == 200 else None,
                'error': None if resp.status_code == 200 else resp.text
            }
        except requests.Timeout:
            return {'success': False, 'error': '请求超时'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _request_with_urllib(self, method: str, url: str, data: Optional[Dict]) -> Dict[str, Any]:
        """使用 urllib 库发送请求（后备方案）"""
        try:
            body = json.dumps(data).encode('utf-8') if data else None
            req = urllib.request.Request(url, data=body, headers=self.headers, method=method)
            
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                return {
                    'success': True,
                    'status': resp.status,
                    'data': json.loads(resp.read().decode('utf-8')),
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
        return self._request('GET', '/health').get('success', False)
    
    def chat(self, message: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """发送对话消息"""
        if not self.enabled:
            return {'success': False, 'error': 'Agent 未启用'}
        
        result = self._request('POST', '/chat', {
            'message': message,
            'context': context or {}
        })
        
        if result['success']:
            return {'success': True, **result['data']}
        return {'success': False, 'error': result.get('error', '未知错误')}
    
    def execute_command(self, command: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """执行命令"""
        if not self.enabled:
            return {'success': False, 'error': 'Agent 未启用'}
        
        result = self._request('POST', '/execute', {
            'command': command,
            'params': params or {}
        })
        
        if result['success']:
            return {'success': True, **result['data']}
        return {'success': False, 'error': result.get('error', '未知错误')}
    
    def get_suggestions(self, context: Dict[str, Any]) -> List[str]:
        """获取智能建议"""
        if not self.enabled or not self.is_available():
            return []
        
        result = self._request('POST', '/suggestions', {'context': context})
        if result['success'] and result.get('data'):
            return result['data'].get('suggestions', [])
        return []
