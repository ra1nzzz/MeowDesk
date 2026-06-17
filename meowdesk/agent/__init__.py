"""
AI Agent 集成模块
"""

from .gateway import AgentGateway
from .commands import CommandRegistry
from .detector import (
    AgentDetector,
    DetectionResult,
    detect_and_configure,
    HEALTH_PATHS,
    AGENT_SIGNATURES,
)

__all__ = [
    'AgentGateway',
    'CommandRegistry',
    'AgentDetector',
    'DetectionResult',
    'detect_and_configure',
    'HEALTH_PATHS',
    'AGENT_SIGNATURES',
]
