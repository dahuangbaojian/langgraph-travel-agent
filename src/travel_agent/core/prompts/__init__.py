"""
旅行代理的Prompt管理模块
包含所有LLM使用的prompt模板
"""

from .intent_analysis import INTENT_ANALYSIS_PROMPT
from .budget_analysis import BUDGET_ANALYSIS_PROMPT
from .duration_planning import DURATION_PLANNING_PROMPT
from .travel_extraction import TRAVEL_EXTRACTION_PROMPT


__all__ = [
    # 核心功能prompt
    "INTENT_ANALYSIS_PROMPT",
    "BUDGET_ANALYSIS_PROMPT",
    "DURATION_PLANNING_PROMPT",
    "TRAVEL_EXTRACTION_PROMPT",
]
