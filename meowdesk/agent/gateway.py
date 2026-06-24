"""
Agent Gateway - 连接本地 AI Agent (OpenClaw, Hermes 等)

通信模式（参考 Aion ACP 架构）：
  - agent 模式: 通过 HTTP API 或 CLI 与本地 Agent 通信
  - llm 模式:   直通 LLM API (OpenAI-compatible)

会话管理：
  - 每个 AgentGateway 实例绑定一个 session_id
  - 对话历史通过 messages 列表维护，发送时携带上下文
  - 支持 Hermes 的 actor 绑定（session.actor = "hermes"）
"""

import json
import subprocess
from typing import Dict, Any, Optional, List

from ..core.types import AgentConfig, AgentType
from .detector import HEALTH_PATHS, AGENT_SIGNATURES

# 跨平台 HTTP 请求
try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False
    import urllib.request
    import urllib.error


class AgentGateway:
    """Agent 网关 - 统一接口连接不同的本地 Agent

    支持三种通信路径：
    1. HTTP API (agent 模式) — 通过 endpoint + path 发送请求
    2. CLI 调用 (agent 模式) — 通过 subprocess 调用 openclaw CLI
    3. 直通 LLM (llm 模式) — 直接调用 OpenAI-compatible API

    会话绑定：
    - session_id: 当前会话标识，首次使用时生成
    - actor: 绑定的 Agent 角色名（如 "hermes"），参考 Aion 的 actor 绑定机制
    """

    def __init__(self, config: AgentConfig):
        self.config = config
        self.agent_type = config.agent_type
        self.endpoint = config.endpoint
        self.api_key = config.api_key
        self.timeout = config.timeout
        self.enabled = config.enabled
        self.mode = getattr(config, 'mode', 'agent')
        self.model = getattr(config, 'model', '')

        # Session / actor binding (Aion-style)
        self.session_id: Optional[str] = None
        self.actor: str = self.agent_type.value if self.agent_type else ""

    @property
    def headers(self) -> Dict[str, str]:
        """获取请求头"""
        h = {'Content-Type': 'application/json'}
        if self.api_key:
            h['Authorization'] = f'Bearer {self.api_key}'
        return h

    def _ensure_session(self) -> str:
        """确保会话已绑定，返回 session_id。

        参考 Aion 的 acp_sessions 表：首次调用时创建会话，
        后续调用复用同一会话，保持对话连续性。
        """
        if self.session_id is None:
            from datetime import datetime
            self.session_id = f"meowdesk_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        return self.session_id

    def _request(self, method: str, path: str, data: Optional[Dict] = None) -> Dict[str, Any]:
        """发送 HTTP 请求（跨平台）"""
        url = f"{self.endpoint}{path}"

        if HAS_REQUESTS:
            return self._request_with_requests(method, url, data)
        return self._request_with_urllib(method, url, data)

    def _request_raw(self, method: str, url: str, data: Optional[Dict] = None) -> Dict[str, Any]:
        """Send HTTP request to an absolute URL (not using self.endpoint + path)."""
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

        # Agent 模式: 尝试 HTTP 健康检查
        # 使用 agent-specific health paths if available
        sig = AGENT_SIGNATURES.get(self.agent_type.value, {})
        health_paths = sig.get("health_paths", HEALTH_PATHS)
        for path in health_paths:
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

        # 尝试 CLI 检查（Hermes）
        if self.agent_type == AgentType.HERMES:
            try:
                result = subprocess.run(
                    ['hermes', '--version'],
                    capture_output=True, text=True, timeout=5,
                    encoding='utf-8', errors='replace'
                )
                if result.returncode == 0:
                    return True
            except (OSError, subprocess.SubprocessError):
                pass

        return False

    def chat(self, message: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """发送对话消息

        根据 self.mode 选择通信路径：
        - llm 模式: 直通 LLM API（OpenAI-compatible）
        - agent 模式: 先尝试 HTTP，失败后降级到 CLI

        会话管理：
        - 自动绑定 session_id 和 actor
        - 对话历史通过 context['history'] 传递
        """
        if not self.enabled:
            return {'success': False, 'error': 'Agent 未启用'}

        self._ensure_session()

        # 直通 LLM API 模式 (OpenAI-compatible)
        if self.mode == 'llm':
            return self._chat_llm(message, context)

        # 本地 Agent 模式 (OpenClaw / Hermes)
        result = self._request('POST', '/v1/chat/completions', {
            'message': message,
            'messages': [{'role': 'user', 'content': message}],
            'context': context or {},
            'session_id': self.session_id,
            'actor': self.actor,
        })

        if result.get('success') and result.get('data'):
            data = result['data']
            if 'choices' in data:
                content = data['choices'][0].get('message', {}).get('content', '')
                return {'success': True, 'response': content, 'session_id': self.session_id}
            if 'response' in data:
                return {'success': True, 'response': data['response'], 'session_id': self.session_id}

        # 尝试 CLI 调用（OpenClaw）
        if self.agent_type == AgentType.OPENCLAW:
            return self._chat_via_cli(message)

        return {'success': False, 'error': result.get('error', '请求失败')}

    def _chat_llm(self, message: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """Direct LLM API call — OpenAI-compatible /v1/chat/completions."""
        messages = []

        # System prompt with actor awareness
        sys_prompt = "你是妙喵桌宠的 AI 助手，用中文友好、简洁地回答用户问题。"
        if self.actor:
            sys_prompt += f" 当前绑定角色: {self.actor}。"
        messages.append({'role': 'system', 'content': sys_prompt})

        # Conversation history from context
        if context and 'history' in context:
            for msg in context['history']:
                role = msg.get('role', 'user')
                content = msg.get('content', '')
                if role in ('user', 'assistant') and content:
                    messages.append({'role': role, 'content': content})

        messages.append({'role': 'user', 'content': message})

        body = {
            'model': self.model or 'deepseek-chat',
            'messages': messages,
        }

        # Endpoint: ensure it ends with /v1/chat/completions
        endpoint = self.endpoint.rstrip('/')
        if not endpoint.endswith('/v1/chat/completions'):
            url = f"{endpoint}/v1/chat/completions"
        else:
            url = endpoint

        result = self._request_raw('POST', url, body)

        if result.get('success') and result.get('data'):
            data = result['data']
            if 'choices' in data and data['choices']:
                content = data['choices'][0].get('message', {}).get('content', '')
                return {'success': True, 'response': content, 'session_id': self.session_id}
            if 'response' in data:
                return {'success': True, 'response': data['response'], 'session_id': self.session_id}

        return {'success': False, 'error': result.get('error', '请求失败')}

    def _chat_via_cli(self, message: str) -> Dict[str, Any]:
        """通过 CLI 调用 OpenClaw"""
        try:
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
                output = result.stdout.strip()
                lines = output.split('\n')
                response_lines = []
                for line in lines:
                    if line.startswith('[') or line.startswith('Gateway') or line.startswith('Source') or line.startswith('Config') or line.startswith('Bind') or line.startswith('EMBEDDED'):
                        continue
                    if line.strip():
                        response_lines.append(line.strip())

                response = '\n'.join(response_lines) if response_lines else output
                return {'success': True, 'response': response, 'session_id': self.session_id}
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
            'params': params or {},
            'session_id': self.session_id,
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

        result = self._request('POST', '/suggestions', {
            'context': context,
            'session_id': self.session_id,
        })
        if result['success'] and result.get('data'):
            return result['data'].get('suggestions', [])
        return []

    def reset_session(self) -> None:
        """重置当前会话（创建新的 session_id）。

        参考 Aion 的 conversations 表：每次重置等同于创建新会话，
        旧会话历史不再携带。
        """
        self.session_id = None
