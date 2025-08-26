"""Travel Agent - 智能旅行规划助手"""

__version__ = "1.0.0"
__author__ = "Travel Agent Team"

from .config.settings import config
from .core.models import *

# 数据管理器已移除，使用LLM + Tools方式
from .tools.planner import travel_planning_data_provider
from .graph import graph

__all__ = [
    "config",
    # "travel_data_manager",  # 已移除
    "travel_planning_data_provider",
    "graph",
]
