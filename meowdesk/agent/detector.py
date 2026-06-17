"""
Agent Detector - 自动检测本机运行的 AI Agent (OpenClaw, Hermes 等)

三层探测策略（从快到慢）：
1. HTTP 端口扫描 — 并行扫描常见端口，socket 预检 + 健康端点
2. CLI 探活 — 检查 openclaw/hermes 命令是否在 PATH
3. 进程名检测 — 扫描进程列表匹配已知进程名

整个检测过程有总超时上限，避免阻塞启动。

探测策略通过 _PROBE_STRATEGIES 列表注册，新增检测方式只需
追加函数到该列表，无需修改 detect() 本身（开闭原则）。
"""

import shutil
import socket
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed, TimeoutError
from dataclasses import dataclass
from typing import Callable, List, Optional, Tuple
from urllib.request import urlopen
from urllib.error import URLError

from ..core.types import AgentType
from ..utils import get_logger

_log = get_logger(__name__)

# ---------------------------------------------------------------------------
# Shared constants — single source of truth for agent signatures.
# gateway.py imports from here to avoid duplication.
# ---------------------------------------------------------------------------

# Agent 签名：name → (AgentType, default_port, default_endpoint, cli_probe_args)
# cli_probe_args 为 None 表示仅检查命令存在，不执行子命令验证
AGENT_SIGNATURES: dict = {
    "openclaw": {
        "agent_type": AgentType.OPENCLAW,
        "default_port": 8080,
        "default_endpoint": "http://localhost:8080",
        "cli_probe_args": ["agents", "list"],
    },
    "hermes": {
        "agent_type": AgentType.HERMES,
        "default_port": 3000,
        "default_endpoint": "http://localhost:3000",
        "cli_probe_args": ["--version"],
    },
}

# 健康检查路径（与 gateway.py 共享）
HEALTH_PATHS: List[str] = ["/health", "/api/health", "/v1/health", "/status", "/"]

# 常见 Agent 端口（按优先级排列，从 AGENT_SIGNATURES 派生 + 其他常见端口）
_COMMON_PORTS: List[int] = [
    sig["default_port"] for sig in AGENT_SIGNATURES.values()
] + [11434, 5000, 8000, 9000, 7860, 6000]
# 去重保序
_seen = set()
_COMMON_PORTS = [p for p in _COMMON_PORTS if not (p in _seen or _seen.add(p))]

# 单端口 HTTP 请求超时（秒）
_PER_PORT_TIMEOUT = 0.8

# socket 预检超时（秒）— 端口未开放时快速跳过
_SOCKET_PRECHECK_TIMEOUT = 0.3

# 总超时上限（秒）
_MAX_TIMEOUT = 5.0


@dataclass
class DetectionResult:
    """检测结果"""
    found: bool
    agent_type: AgentType = AgentType.CUSTOM
    endpoint: str = ""
    source: str = ""              # "http" / "cli" / "process"
    confidence: float = 0.0       # 0.0 - 1.0
    endpoint_verified: bool = False  # endpoint 是否经 HTTP 实测验证


def _port_to_agent_type(port: int) -> Tuple[AgentType, bool]:
    """端口 → (AgentType, is_known_port)。
    返回 is_known_port=False 时表示端口不在签名表中。
    """
    for sig in AGENT_SIGNATURES.values():
        if sig["default_port"] == port:
            return sig["agent_type"], True
    return AgentType.CUSTOM, False


def _probe_http(timeout: float) -> DetectionResult:
    """并行扫描常见端口，尝试健康检查端点。

    使用 socket.connect_ex 预检跳过未开放端口，
    仅对开放端口执行 HTTP 健康检查。
    """
    start = time.monotonic()

    def _check_port(port: int) -> Optional[DetectionResult]:
        remaining = timeout - (time.monotonic() - start)
        if remaining <= 0:
            return None

        # socket 预检：快速判断端口是否开放
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(_SOCKET_PRECHECK_TIMEOUT)
            result = sock.connect_ex(("localhost", port))
            sock.close()
            if result != 0:
                return None  # 端口未开放，跳过
        except OSError:
            return None

        # 端口开放，尝试健康检查路径
        endpoint = f"http://localhost:{port}"
        for path in HEALTH_PATHS:
            remaining = timeout - (time.monotonic() - start)
            if remaining <= 0:
                break
            per_timeout = min(_PER_PORT_TIMEOUT, remaining)
            url = f"{endpoint}{path}"
            try:
                resp = urlopen(url, timeout=per_timeout)
                body = resp.read(4096).decode("utf-8", errors="replace")
                status = resp.status

                if 200 <= status < 300:
                    body_lower = body.lower()
                    # 先尝试 body 内容匹配（高置信度）
                    for name, sig in AGENT_SIGNATURES.items():
                        if name in body_lower:
                            return DetectionResult(
                                found=True,
                                agent_type=sig["agent_type"],
                                endpoint=endpoint,
                                source="http",
                                confidence=0.9,
                                endpoint_verified=True,
                            )
                    # body 无标识，靠端口推断（降低置信度）
                    agent_type, is_known = _port_to_agent_type(port)
                    return DetectionResult(
                        found=True,
                        agent_type=agent_type,
                        endpoint=endpoint,
                        source="http",
                        confidence=0.7 if is_known else 0.5,
                        endpoint_verified=True,
                    )
            except URLError:
                continue
            except (OSError, ValueError):
                continue
        return None

    # 并行扫描所有端口
    with ThreadPoolExecutor(max_workers=min(8, len(_COMMON_PORTS))) as pool:
        futures = {pool.submit(_check_port, port): port for port in _COMMON_PORTS}
        try:
            for future in as_completed(futures, timeout=timeout):
                try:
                    result = future.result(timeout=0.1)
                    if result is not None and result.found:
                        return result
                except Exception:
                    continue
        except TimeoutError:
            # 总超时到达，部分 future 未完成 — 已完成的足够判断
            pass

    return DetectionResult(found=False)


def _probe_cli(timeout: float) -> DetectionResult:
    """检查 CLI 命令是否在 PATH 上并验证可用性。

    timeout 为剩余可用时间，subprocess 超时不超过此值。
    如果命令存在（shutil.which 命中）但探测子命令失败，
    仍返回低置信度结果——命令存在本身就是安装证据。
    """
    low_confidence_result: Optional[DetectionResult] = None

    for name, sig in AGENT_SIGNATURES.items():
        remaining = timeout - 0  # timeout 是从 detect() 传入的剩余时间
        if remaining <= 0:
            break

        if not shutil.which(name):
            continue

        # 命令存在 — 记录低置信度结果（安装证据）
        if low_confidence_result is None:
            low_confidence_result = DetectionResult(
                found=True,
                agent_type=sig["agent_type"],
                endpoint=sig["default_endpoint"],
                source="cli",
                confidence=0.5,
                endpoint_verified=False,
            )

        probe_args = sig.get("cli_probe_args")
        sub_timeout = min(2, remaining)
        try:
            result = subprocess.run(
                [name] + (probe_args or []),
                capture_output=True, text=True, timeout=sub_timeout,
                encoding="utf-8", errors="replace",
            )
            if result.returncode == 0:
                return DetectionResult(
                    found=True,
                    agent_type=sig["agent_type"],
                    endpoint=sig["default_endpoint"],
                    source="cli",
                    confidence=0.7,
                    endpoint_verified=False,
                )
        except subprocess.TimeoutExpired:
            continue
        except (OSError, subprocess.SubprocessError):
            continue

    return low_confidence_result or DetectionResult(found=False)


def _probe_process(timeout: float) -> DetectionResult:
    """扫描进程列表匹配已知进程名。"""
    sub_timeout = min(3, timeout)
    try:
        if sys.platform == "win32":
            result = subprocess.run(
                ["tasklist"],
                capture_output=True, text=True, timeout=sub_timeout,
                encoding="utf-8", errors="replace",
            )
        else:
            result = subprocess.run(
                ["ps", "aux"],
                capture_output=True, text=True, timeout=sub_timeout,
                encoding="utf-8", errors="replace",
            )

        if result.returncode != 0:
            return DetectionResult(found=False)

        output_lower = result.stdout.lower()
        for name, sig in AGENT_SIGNATURES.items():
            if name in output_lower:
                return DetectionResult(
                    found=True,
                    agent_type=sig["agent_type"],
                    endpoint=sig["default_endpoint"],
                    source="process",
                    confidence=0.5,
                    endpoint_verified=False,
                )
    except (OSError, subprocess.SubprocessError):
        pass

    return DetectionResult(found=False)


# ---------------------------------------------------------------------------
# Strategy registry — 新增检测方式只需追加到此列表
# ---------------------------------------------------------------------------

ProbeFn = Callable[[float], DetectionResult]
_PROBE_STRATEGIES: List[ProbeFn] = [_probe_http, _probe_cli, _probe_process]


class AgentDetector:
    """自动检测本机 AI Agent。

    探测策略通过 _PROBE_STRATEGIES 列表驱动，新增方式只需
    追加函数到该列表，无需修改 detect()（开闭原则）。
    """

    @staticmethod
    def detect(timeout: float = _MAX_TIMEOUT) -> DetectionResult:
        """执行多层探测，返回第一个命中的结果。

        顺序按 _PROBE_STRATEGIES 列表（HTTP → CLI → 进程名）。
        任何一层命中即返回，不再继续。

        超时公平分配：每层获得 remaining / (剩余策略数) 的预算，
        防止慢策略（如 HTTP 端口扫描）独占全部超时导致后续策略
        无机会执行。每层最低保底 1.0 秒。
        """
        start = time.monotonic()
        n = len(_PROBE_STRATEGIES)

        for i, probe_fn in enumerate(_PROBE_STRATEGIES):
            remaining = timeout - (time.monotonic() - start)
            if remaining < 0.5:
                break
            budget = max(remaining / (n - i), 1.0)

            result = probe_fn(budget)
            if result.found:
                _log.info("agent detected via %s: %s at %s (confidence=%.2f)",
                          result.source, result.agent_type.value,
                          result.endpoint, result.confidence)
                return result

        _log.info("no agent detected")
        return DetectionResult(found=False)


def detect_and_configure(config_manager, timeout: float = _MAX_TIMEOUT) -> DetectionResult:
    """执行检测并根据结果自动配置 agent。

    供 window.py 和 settings.py 复用，避免检测逻辑重复。
    检测成功则更新配置并保存，检测后标记首次运行完成。

    Args:
        config_manager: ConfigManager 实例
        timeout: 检测总超时（秒）

    Returns:
        DetectionResult 检测结果
    """
    from ..core.types import AgentConfig

    result = AgentDetector.detect(timeout=timeout)

    if result.found:
        new_config = AgentConfig(
            enabled=True,
            agent_type=result.agent_type,
            endpoint=result.endpoint,
            api_key="",
            timeout=30,
        )
        config_manager.config.agent = new_config
        config_manager.config.agent_auto_detected = True
        config_manager.save()
        _log.info("auto-detected %s at %s, agent enabled",
                  result.agent_type.value, result.endpoint)
    else:
        _log.info("no local agent detected, AI features will be hidden")

    config_manager.mark_first_run_completed()
    return result
