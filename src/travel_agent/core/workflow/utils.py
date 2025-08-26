"""工具函数模块"""

import os
import json
import logging
from typing import Dict, Any, List
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage

from ..prompts.travel_extraction import TRAVEL_EXTRACTION_PROMPT

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
        # 智能系统依赖LLM，直接抛出异常
        raise Exception(f"无法提取旅行信息：{e}")
