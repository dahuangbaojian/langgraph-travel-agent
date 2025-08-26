"""工具函数模块"""

import os
import json
import logging
from typing import Dict, Any, List
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage

from ..prompts.intent_analysis import INTENT_ANALYSIS_PROMPT
from ..prompts.travel_extraction import TRAVEL_EXTRACTION_PROMPT
from ..prompts.smart_defaults import SMART_DEFAULTS_PROMPT
from ..prompts.duration_planning import DURATION_PLANNING_PROMPT

logger = logging.getLogger(__name__)


def get_llm():
    """延迟创建LLM实例"""
    try:
        return ChatOpenAI(
            model=os.getenv("OPENAI_MODEL", "gpt-4.1"),
            temperature=float(os.getenv("OPENAI_TEMPERATURE", "0.7")),
            max_tokens=int(os.getenv("OPENAI_MAX_TOKENS", "4000")),
            openai_api_base=os.getenv("OPENAI_BASE_URL"),
        )
    except Exception as e:
        logger.warning(f"创建LLM实例失败: {e}")
        return None


async def _extract_travel_info_with_llm(user_message: str) -> Dict[str, Any]:
    """使用LLM智能提取旅行信息"""
    try:
        prompt = TRAVEL_EXTRACTION_PROMPT.format(message=user_message)

        llm = get_llm()
        if llm is None:
            raise Exception("LLM实例不可用")

        response = llm.invoke([HumanMessage(content=prompt)])
        travel_info = json.loads(response.content.strip())

        logger.info(f"LLM提取旅行信息: {travel_info}")
        return travel_info

    except Exception as e:
        logger.error(f"LLM提取旅行信息失败: {e}")
        # 返回基本默认值
        return {
            "destination": "",
            "duration_days": 3,
            "people_count": 2,
            "budget_level": "中等",
            "travel_type": "休闲",
            "preferences": [],
        }


async def _enhance_info_with_tools(
    travel_info: Dict[str, Any], suggested_tools: List[str]
) -> Dict[str, Any]:
    """使用工具增强旅行信息"""
    enhanced_info = {}

    try:
        # 这里可以集成各种工具来增强信息
        # 比如天气、汇率、交通等
        logger.info(f"使用工具增强信息: {suggested_tools}")

        # 暂时返回空字典，后续可以扩展
        return enhanced_info

    except Exception as e:
        logger.error(f"工具增强信息失败: {e}")
        return enhanced_info


async def _get_smart_defaults() -> Dict[str, Any]:
    """获取智能默认值"""
    try:
        prompt = SMART_DEFAULTS_PROMPT.format(
            current_time="当前时间", user_context="用户上下文"
        )

        llm = get_llm()
        if llm is None:
            raise Exception("LLM实例不可用")

        response = llm.invoke([HumanMessage(content=prompt)])
        defaults = json.loads(response.content.strip())

        logger.info(f"智能生成默认值: {defaults}")
        return defaults

    except Exception as e:
        logger.error(f"智能生成默认值失败: {e}")
        # 返回基本默认值
        return {"duration_days": 3, "people_count": 2, "budget_level": "中等"}


async def _optimize_duration(
    destination: str, budget: float, preferences: List[str]
) -> Dict[str, Any]:
    """智能优化行程时长"""
    try:
        prompt = DURATION_PLANNING_PROMPT.format(
            destination=destination, budget=budget, preferences=", ".join(preferences)
        )

        llm = get_llm()
        if llm is None:
            raise Exception("LLM实例不可用")

        response = llm.invoke([HumanMessage(content=prompt)])
        optimization = json.loads(response.content.strip())

        logger.info(f"智能优化行程时长: {optimization}")
        return optimization

    except Exception as e:
        logger.error(f"智能优化行程时长失败: {e}")
        # 返回基本建议
        return {
            "recommended_duration": 3,
            "reason": "基于预算和偏好的基本建议",
            "time_optimization": {},
        }


async def _get_duration_reason(duration: int, destination: str) -> str:
    """获取行程时长的理由"""
    try:
        # 这里可以使用LLM生成更智能的理由
        # 暂时返回简单理由
        reasons = {
            1: f"{destination}一日游，适合周末短途旅行",
            2: f"{destination}两日游，可以体验主要景点",
            3: f"{destination}三日游，深度体验当地文化",
            4: f"{destination}四日游，从容游览所有景点",
            5: f"{destination}五日游，充分享受假期时光",
            6: f"{destination}六日游，深度探索周边地区",
            7: f"{destination}七日游，完整的周游体验",
        }

        return reasons.get(duration, f"{destination}{duration}日游，根据您的需求定制")

    except Exception as e:
        logger.error(f"获取行程时长理由失败: {e}")
        return f"{destination}{duration}日游"
