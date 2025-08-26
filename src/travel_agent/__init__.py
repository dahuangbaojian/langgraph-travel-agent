"""Travel Agent - 智能旅行规划助手"""

__version__ = "1.0.0"
__author__ = "Travel Agent Team"

from .config.settings import config
from .core.models import *
from .core.llm_factory import get_llm

# 导入图创建函数
from .graph import create_graph, create_travel_agent

__all__ = [
    "config",
    "get_llm",
    "create_graph",
    "create_travel_agent",
]
