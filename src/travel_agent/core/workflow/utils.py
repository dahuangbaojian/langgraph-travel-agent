"""工具函数模块"""

import json
import logging
from typing import Dict, Any, List
from langchain_core.messages import HumanMessage

from ..prompts.travel_extraction import TRAVEL_EXTRACTION_PROMPT
from ..llm_factory import get_llm

logger = logging.getLogger(__name__)


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
        # 使用TravelInfo模型的默认值
        from ..models import TravelInfo

        default_info = TravelInfo.create_default()
        return default_info.to_dict()
