"""Travel Agent Prompts Package"""

from .travel_planner import TRAVEL_SYSTEM_PROMPT
from .travel_advisor import TRAVEL_ADVISOR_PROMPT
from .fallback import FALLBACK_TRAVEL_PROMPT, TRAVEL_PLAN_TIP
from .config import (
    PROMPT_CONFIG,
    get_prompt_config,
    get_prompt,
    get_prompt_parameters,
    list_available_prompts,
)

__all__ = [
    "TRAVEL_SYSTEM_PROMPT",
    "TRAVEL_ADVISOR_PROMPT",
    "FALLBACK_TRAVEL_PROMPT",
    "TRAVEL_PLAN_TIP",
    "PROMPT_CONFIG",
    "get_prompt_config",
    "get_prompt",
    "get_prompt_parameters",
    "list_available_prompts",
]
