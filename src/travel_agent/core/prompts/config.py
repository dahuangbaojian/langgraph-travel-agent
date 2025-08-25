"""Prompt Configuration and Management"""

from typing import Dict, Any
from .travel_planner import TRAVEL_SYSTEM_PROMPT

from .travel_advisor import TRAVEL_ADVISOR_PROMPT
from .fallback import FALLBACK_TRAVEL_PROMPT, TRAVEL_PLAN_TIP

# Prompt配置
PROMPT_CONFIG = {
    "travel_planner": {
        "name": "旅行规划师",
        "description": "专业的旅行计划制定专家",
        "prompt": TRAVEL_SYSTEM_PROMPT,
        "temperature": 0.7,
        "max_tokens": 4000,
    },
    "travel_advisor": {
        "name": "旅行顾问",
        "description": "个性化旅行建议专家",
        "prompt": TRAVEL_ADVISOR_PROMPT,
        "temperature": 0.8,
        "max_tokens": 3000,
    },
    "fallback_travel": {
        "name": "旅行规划师(Fallback)",
        "description": "当无法提取旅行信息时的备用回复",
        "prompt": FALLBACK_TRAVEL_PROMPT,
        "temperature": 0.7,
        "max_tokens": 2000,
    },
    "travel_plan_tip": {
        "name": "旅行计划提示",
        "description": "旅行计划完成后的温馨提示",
        "prompt": TRAVEL_PLAN_TIP,
        "temperature": 0.5,
        "max_tokens": 500,
    },
}


def get_prompt_config(prompt_type: str) -> Dict[str, Any]:
    """获取指定类型的prompt配置"""
    return PROMPT_CONFIG.get(prompt_type, {})


def get_prompt(prompt_type: str) -> str:
    """获取指定类型的prompt内容"""
    config = get_prompt_config(prompt_type)
    return config.get("prompt", "")


def get_prompt_parameters(prompt_type: str) -> Dict[str, Any]:
    """获取指定类型的prompt参数"""
    config = get_prompt_config(prompt_type)
    return {
        "temperature": config.get("temperature", 0.7),
        "max_tokens": config.get("max_tokens", 3000),
    }


def list_available_prompts() -> list:
    """列出所有可用的prompt类型"""
    return list(PROMPT_CONFIG.keys())
