"""
旅行代理的Prompt管理模块
包含所有LLM使用的prompt模板
"""

from .intent_analysis import INTENT_ANALYSIS_PROMPT
from .travel_validation import TRAVEL_VALIDATION_PROMPT
from .budget_analysis import BUDGET_ANALYSIS_PROMPT
from .duration_planning import DURATION_PLANNING_PROMPT
from .city_extraction import CITY_EXTRACTION_PROMPT
from .activity_parsing import ACTIVITY_PARSING_PROMPT
from .smart_defaults import SMART_DEFAULTS_PROMPT
from .travel_extraction import TRAVEL_EXTRACTION_PROMPT
from .intent_classification import INTENT_CLASSIFICATION_PROMPT
from .plan_validation import PLAN_VALIDATION_PROMPT
from .dynamic_planning import DYNAMIC_PLANNING_PROMPT
from .config_generation import (
    BUDGET_RATIO_PROMPT,
    EXCHANGE_RATE_PROMPT,
    CITY_VALIDATION_PROMPT,
)

__all__ = [
    "INTENT_ANALYSIS_PROMPT",
    "TRAVEL_VALIDATION_PROMPT",
    "BUDGET_ANALYSIS_PROMPT",
    "DURATION_PLANNING_PROMPT",
    "CITY_EXTRACTION_PROMPT",
    "ACTIVITY_PARSING_PROMPT",
    "SMART_DEFAULTS_PROMPT",
    "TRAVEL_EXTRACTION_PROMPT",
    "INTENT_CLASSIFICATION_PROMPT",
    "PLAN_VALIDATION_PROMPT",
    "DYNAMIC_PLANNING_PROMPT",
    "BUDGET_RATIO_PROMPT",
    "EXCHANGE_RATE_PROMPT",
    "CITY_VALIDATION_PROMPT",
]
