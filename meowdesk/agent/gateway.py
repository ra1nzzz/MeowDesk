"""
Agent Gateway - 连接本地 AI Agent (OpenClaw, Hermes 等)
兼容 macOS / Windows
支持 HTTP API 和 CLI 调用方式
"""

import json
import subprocess
from typing import Dict, Any, Optional, List

from ..core.types import AgentConfig, AgentType
from .detector import HEALTH_PATHS

# 跨平台 HTTP 请求
try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False
    import urllib.request
    import urllib.error


class AgentGateway:
    """Agent 网关 - 统一接口连接不同的本地 Agent"""

    def __init__(self, config: AgentConfig):
        self.config = config
        self.agent_type = config.agent_type
        self.endpoint = config.endpoint
        self.api_key = config.api_key
        self.timeout = config.timeout
        self.enabled = config.enabled
        self.mode = getattr(config, 'mode', 'llm')
        self.model = getattr(config, 'model', '')

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

            if resp.status_code == 200:
                try:
                    json_data = resp.json()
                    return {'success': True, 'status': resp.status_code, 'data': json_data, 'error': None}
                except ValueError:
                    return {'success': True, 'status': resp.status_code, 'data': {'response': resp.text} if resp.text else {}, 'error': None}
            else:
                return {'success': False, 'status': resp.status_code, 'data': None, 'error': resp.text or f'HTTP {resp.status_code}'}
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
                return {'success': True, 'status': resp.status, 'data': json.loads(resp.read().decode('utf-8')), 'error': None}
        except urllib.error.HTTPError as e:
            return {'success': False, 'status': e.code, 'error': str(e)}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def is_available(self) -> bool:
        """检查 Agent 是否可用"""
        if not self.enabled:
            return False

        # LLM 直通模式: 只要有端点就认为可用
        if self.mode == 'llm':
            return bool(self.endpoint)

        # 尝试 HTTP 健康检查
        for path in HEALTH_PATHS:
            result = self._request('GET', path)
            if result.get('success'):
                return True

        # 尝试 CLI 检查（OpenClaw）
        if self.agent_type == AgentType.OPENCLAW:
            try:
                result = subprocess.run(
                    ['openclaw', 'agents', 'list'],
                    capture_output=True, text=True, timeout=5,
                    encoding='utf-8', errors='replace'
                )
                if result.returncode == 0 and 'main' in result.stdout:
                    return True
            except (OSError, subprocess.SubprocessError):
                pass

        return False

    def chat(self, message: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """发送对话消息"""
        if not self.enabled:
            return {'success': False, 'error': 'Agent 未启用'}

        # 直通 LLM API 模式 (OpenAI-compatible)
        if self.mode == 'llm':
            return self._chat_llm(message, context)

        # 本地 Agent 模式 (OpenClaw / Hermes)
        result = self._request('POST', '/v1/chat/completions', {
            'message': message,
            'messages': [{'role': 'user', 'content': message}],
            'context': context or {}
        })

        if result.get('success') and result.get('data'):
            data = result['data']
            if 'choices' in data:
                content = data['choices'][0].get('message', {}).get('content', '')
                return {'success': True, 'response': content}
            if 'response' in data:
                return {'success': True, 'response': data['response']}

        # 尝试 CLI 调用（OpenClaw）
        if self.agent_type == AgentType.OPENCLAW:
            return self._chat_via_cli(message)

        return {'success': False, 'error': result.get('error', '请求失败')}

    def _chat_llm(self, message: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """Direct LLM API call — OpenAI-compatible /v1/chat/completions."""
        # Build messages array with history
        messages = []

        # System prompt
        sys_prompt = "你是妙喵桌宠的 AI 助手，用中文友好、简洁地回答用户问题。"
        messages.append({'role': 'system', 'content': sys_prompt})

        # Conversation history from context
        if context and 'history' in context:
            for msg in context['history']:
                role = msg.get('role', 'user')
                content = msg.get('content', '')
                if role in ('user', 'assistant') and content:
                    messages.append({'role': role, 'content': content})

        # Current message
        messages.append({'role': 'user', 'content': message})

        # Build request body
        body = {
            'model': self.model or 'deepseek-chat',
            'messages': messages,
        }

        # Endpoint: ensure it ends with /v1/chat/completions
        endpoint = self.endpoint.rstrip('/')
        if not endpoint.endswith('/v1/chat/completions'):
            # If user provided base URL like https://api.deepseek.com, append the path
            url = f"{endpoint}/v1/chat/completions"
        else:
            url = endpoint

        # Send request
        result = self._request_raw('POST', url, body)

        if result.get('success') and result.get('data'):
            data = result['data']
            # OpenAI format
            if 'choices' in data and data['choices']:
                content = data['choices'][0].get('message', {}).get('content', '')
                return {'success': True, 'response': content}
            # Simple fallback
            if 'response' in data:
                return {'success': True, 'response': data['response']}

        return {'success': False, 'error': result.get('error', '请求失败')}

    def _request_raw(self, method: str, url: str, data: Optional[Dict] = None) -> Dict[str, Any]:
        """Send HTTP request to an absolute URL (not using self.endpoint + path)."""
        if HAS_REQUESTS:
            return self._request_with_requests(method, url, data)
        return self._request_with_urllib(method, url, data)

    def _chat_via_cli(self, message: str) -> Dict[str, Any]:
        """通过 CLI 调用 OpenClaw"""
        try:
            # 构建命令
            cmd = ['openclaw', 'agent', '--agent', 'main', '--message', message]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60,
                encoding='utf-8',
                errors='replace'
            )

            if result.returncode == 0:
                # 解析输出
                output = result.stdout.strip()
                # 提取 AI 回复（跳过日志行）
                lines = output.split('\n')
                response_lines = []
                for line in lines:
                    # 跳过日志/调试行
                    if line.startswith('[') or line.startswith('Gateway') or line.startswith('Source') or line.startswith('Config') or line.startswith('Bind') or line.startswith('EMBEDDED'):
                        continue
                    if line.strip():
                        response_lines.append(line.strip())

                response = '\n'.join(response_lines) if response_lines else output
                return {'success': True, 'response': response}
            else:
                error = result.stderr or result.stdout
                return {'success': False, 'error': error[:200]}

        except subprocess.TimeoutExpired:
            return {'success': False, 'error': '请求超时'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def execute_command(self, command: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """执行命令"""
        if not self.enabled:
            return {'success': False, 'error': 'Agent 未启用'}

        result = self._request('POST', '/execute', {
            'command': command,
            'params': params or {}
        })

        if result.get('success'):
            data = result.get('data')
            if isinstance(data, dict):
                return {'success': True, **data}
            return {'success': False, 'error': f'Agent 返回了非预期格式: {type(data).__name__}'}
        return {'success': False, 'error': result.get('error', '未知错误')}

    def get_suggestions(self, context: Dict[str, Any]) -> List[str]:
        """获取智能建议"""
        if not self.enabled or not self.is_available():
            return []

        result = self._request('POST', '/suggestions', {'context': context})
        if result['success'] and result.get('data'):
            return result['data'].get('suggestions', [])
        return []
