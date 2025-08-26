"""旅行代理图结构 - 专业化智能版本"""

import os
import logging
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI

# 导入状态和节点
from .core.workflow.state import TravelState
from .core.workflow import (
    message_processor,
    travel_planner,
    response_generator,
)

logger = logging.getLogger(__name__)


# 创建LLM实例（延迟创建）
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


# 构建智能图
def create_graph():
    """创建旅行代理图"""
    graph = StateGraph(TravelState)

    # 添加核心节点
    graph.add_node("message_processor", message_processor)  # 消息处理和信息提取
    graph.add_node("travel_planner", travel_planner)  # 旅行规划核心逻辑
    graph.add_node("response_generator", response_generator)  # 响应生成

    # 设置入口点
    graph.set_entry_point("message_processor")

    # 线性流程
    graph.add_edge("message_processor", "travel_planner")
    graph.add_edge("travel_planner", "response_generator")
    graph.add_edge("response_generator", END)

    # 编译图
    compiled_graph = graph.compile()

    logger.info("旅行代理图构建完成")
    return compiled_graph


# 创建旅行代理实例
graph = create_graph()


def create_travel_agent():
    """创建旅行代理实例"""
    return graph
