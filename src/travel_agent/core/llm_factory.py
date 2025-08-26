"""LLM工厂模块 - 统一管理ChatOpenAI实例"""

import os
import logging
from typing import Optional
from langchain_openai import ChatOpenAI

logger = logging.getLogger(__name__)

# 全局LLM实例缓存
_llm_instance: Optional[ChatOpenAI] = None


def get_llm() -> Optional[ChatOpenAI]:
    """
    获取LLM实例（延迟初始化）

    Returns:
        ChatOpenAI实例或None（如果初始化失败）
    """
    global _llm_instance

    if _llm_instance is None:
        try:
            _llm_instance = _create_llm_instance()
            logger.info("LLM实例创建成功")
        except Exception as e:
            logger.error(f"LLM实例创建失败: {e}")
            return None

    return _llm_instance


def _create_llm_instance() -> ChatOpenAI:
    """
    创建新的LLM实例

    Returns:
        ChatOpenAI实例
    """
    return ChatOpenAI(
        model=os.getenv("OPENAI_MODEL", "gpt-4.1"),
        temperature=float(os.getenv("OPENAI_TEMPERATURE", "0.7")),
        max_tokens=int(os.getenv("OPENAI_MAX_TOKENS", "4000")),
        openai_api_base=os.getenv("OPENAI_BASE_URL"),
        openai_api_key=os.getenv("OPENAI_API_KEY"),
    )


def reset_llm_instance():
    """重置LLM实例（用于测试或重新配置）"""
    global _llm_instance
    _llm_instance = None
    logger.info("LLM实例已重置")


def get_llm_config() -> dict:
    """获取LLM配置信息"""
    return {
        "model": os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        "temperature": float(os.getenv("OPENAI_TEMPERATURE", "0.7")),
        "max_tokens": int(os.getenv("OPENAI_MAX_TOKENS", "4000")),
        "base_url": os.getenv("OPENAI_BASE_URL"),
        "has_api_key": bool(os.getenv("OPENAI_API_KEY")),
    }
