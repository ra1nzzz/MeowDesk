"""AgentGateway 的 mock 单元测试（不发起任何真实网络 / 子进程调用）。

覆盖 ROADMAP 阶段 2 的 "agent/gateway.py mock 测试" 项：

- 禁用态短路
- headers 构造（含 / 不含 api_key）
- chat：OpenAI 格式、简单格式、HTTP 失败、OpenClaw CLI 降级
- execute_command：成功、非 dict 数据安全降级、错误透传
- get_suggestions：成功与不可用短路
- is_available：禁用态与 CLI 探测
"""

import subprocess
from typing import Any, Dict, Optional
from unittest.mock import patch, MagicMock

import pytest

from meowdesk.agent.gateway import AgentGateway
from meowdesk.core.types import AgentConfig, AgentType


def make_gateway(enabled: bool = True,
                 agent_type: AgentType = AgentType.CUSTOM,
                 api_key: str = "") -> AgentGateway:
    return AgentGateway(AgentConfig(
        enabled=enabled,
        agent_type=agent_type,
        endpoint="http://localhost:9999",
        api_key=api_key,
        timeout=1,
    ))


def patch_request(gateway: AgentGateway, response: Dict[str, Any]):
    """把 gateway._request 替换为返回固定响应的 mock。"""
    return patch.object(gateway, "_request", return_value=response)


# ---------- 基础 ----------

class TestHeaders:
    def test_without_api_key(self):
        gw = make_gateway(api_key="")
        assert gw.headers == {"Content-Type": "application/json"}

    def test_with_api_key(self):
        gw = make_gateway(api_key="sk-test")
        assert gw.headers["Authorization"] == "Bearer sk-test"


class TestDisabledShortCircuit:
    def test_chat_disabled(self):
        gw = make_gateway(enabled=False)
        result = gw.chat("hello")
        assert result["success"] is False
        assert "未启用" in result["error"]

    def test_execute_command_disabled(self):
        gw = make_gateway(enabled=False)
        assert gw.execute_command("clean_disk")["success"] is False

    def test_is_available_disabled(self):
        gw = make_gateway(enabled=False)
        assert gw.is_available() is False

    def test_get_suggestions_disabled(self):
        gw = make_gateway(enabled=False)
        assert gw.get_suggestions({}) == []


# ---------- chat ----------

class TestChat:
    def test_openai_format(self):
        gw = make_gateway()
        resp = {"success": True, "data": {
            "choices": [{"message": {"content": "喵~"}}]}}
        with patch_request(gw, resp):
            result = gw.chat("hi")
        assert result["success"] is True
        assert result["response"] == "喵~"

    def test_simple_format(self):
        gw = make_gateway()
        resp = {"success": True, "data": {"response": "ok"}}
        with patch_request(gw, resp):
            result = gw.chat("hi")
        assert result["success"] is True
        assert result["response"] == "ok"

    def test_http_failure_non_openclaw(self):
        gw = make_gateway(agent_type=AgentType.CUSTOM)
        resp = {"success": False, "error": "请求超时"}
        with patch_request(gw, resp):
            result = gw.chat("hi")
        assert result["success"] is False
        assert result["error"] == "请求超时"

    def test_http_failure_falls_back_to_cli_for_openclaw(self):
        gw = make_gateway(agent_type=AgentType.OPENCLAW)
        resp = {"success": False, "error": "connection refused"}
        cli_proc = MagicMock(returncode=0, stdout="[log] boot\n你好喵\n", stderr="")
        with patch_request(gw, resp), \
                patch("meowdesk.agent.gateway.subprocess.run",
                      return_value=cli_proc) as run:
            result = gw.chat("hi")
        assert result["success"] is True
        assert result["response"] == "你好喵"
        assert run.call_args[0][0][0] == "openclaw"

    def test_cli_timeout(self):
        gw = make_gateway(agent_type=AgentType.OPENCLAW)
        resp = {"success": False, "error": "down"}
        with patch_request(gw, resp), \
                patch("meowdesk.agent.gateway.subprocess.run",
                      side_effect=subprocess.TimeoutExpired("openclaw", 60)):
            result = gw.chat("hi")
        assert result["success"] is False
        assert "超时" in result["error"]


# ---------- execute_command ----------

class TestExecuteCommand:
    def test_success_dict_data(self):
        gw = make_gateway()
        resp = {"success": True, "data": {"freed": "1GB"}}
        with patch_request(gw, resp):
            result = gw.execute_command("clean_disk")
        assert result == {"success": True, "freed": "1GB"}

    @pytest.mark.parametrize("bad_data", [None, [1, 2], "oops", 42])
    def test_non_dict_data_degrades_safely(self, bad_data):
        """BUG-06 回归：非 dict data 不得抛 TypeError。"""
        gw = make_gateway()
        resp = {"success": True, "data": bad_data}
        with patch_request(gw, resp):
            result = gw.execute_command("clean_disk")
        assert result["success"] is False
        assert "非预期格式" in result["error"]

    def test_error_passthrough(self):
        gw = make_gateway()
        resp = {"success": False, "error": "boom"}
        with patch_request(gw, resp):
            result = gw.execute_command("clean_disk")
        assert result == {"success": False, "error": "boom"}


# ---------- get_suggestions ----------

class TestGetSuggestions:
    def test_success(self):
        gw = make_gateway()
        resp = {"success": True, "data": {"suggestions": ["a", "b"]}}
        with patch.object(gw, "is_available", return_value=True), \
                patch_request(gw, resp):
            assert gw.get_suggestions({"k": 1}) == ["a", "b"]

    def test_unavailable_returns_empty(self):
        gw = make_gateway()
        with patch.object(gw, "is_available", return_value=False):
            assert gw.get_suggestions({}) == []


# ---------- is_available ----------

class TestIsAvailable:
    def _request_always_fail(self, method: str, path: str,
                             data: Optional[Dict] = None) -> Dict[str, Any]:
        return {"success": False, "error": "refused"}

    def test_http_probe_success(self):
        gw = make_gateway()
        with patch.object(gw, "_request",
                          return_value={"success": True, "data": {}}):
            assert gw.is_available() is True

    def test_cli_probe_success_for_openclaw(self):
        gw = make_gateway(agent_type=AgentType.OPENCLAW)
        cli_proc = MagicMock(returncode=0, stdout="agents:\n  main\n")
        with patch.object(gw, "_request", side_effect=self._request_always_fail), \
                patch("meowdesk.agent.gateway.subprocess.run",
                      return_value=cli_proc):
            assert gw.is_available() is True

    def test_cli_missing_binary_returns_false(self):
        """BUG-05 回归：openclaw 不存在时返回 False 而非裸 except 吞异常后误判。"""
        gw = make_gateway(agent_type=AgentType.OPENCLAW)
        with patch.object(gw, "_request", side_effect=self._request_always_fail), \
                patch("meowdesk.agent.gateway.subprocess.run",
                      side_effect=FileNotFoundError("openclaw")):
            assert gw.is_available() is False



# ---------- Session management ----------

class TestSessionManagement:
    def test_session_created_on_first_chat(self):
        gw = make_gateway()
        assert gw.session_id is None
        with patch.object(gw, "_request", return_value={"success": False, "error": "test"}):
            gw.chat("hi")
        assert gw.session_id is not None
        assert gw.session_id.startswith("meowdesk_")

    def test_reset_session_clears_id(self):
        gw = make_gateway()
        with patch.object(gw, "_request", return_value={"success": False, "error": "test"}):
            gw.chat("hi")
        gw.reset_session()
        assert gw.session_id is None


# ---------- LLM mode ----------

class TestLLMMode:
    def test_llm_mode_uses_request_raw(self):
        gw = make_gateway()
        gw.mode = "llm"
        resp = {
            "success": True,
            "data": {"choices": [{"message": {"content": "hi"}}]},
        }
        with patch.object(gw, "_request_raw", return_value=resp):
            result = gw.chat("hello")
        assert result["success"] is True
        assert result["response"] == "hi"

    def test_llm_mode_error(self):
        gw = make_gateway()
        gw.mode = "llm"
        resp = {"success": False, "error": "timeout"}
        with patch.object(gw, "_request_raw", return_value=resp):
            result = gw.chat("hello")
        assert result["success"] is False
