"""旅行代理主图定义"""

import logging
from typing import Dict, Any
from langgraph.graph import StateGraph, END

from .core.workflow.nodes import message_processor, travel_planner, response_generator
from .core.workflow.state import TravelState

logger = logging.getLogger(__name__)


def create_graph() -> StateGraph:
    """创建旅行代理工作流图"""

    # 创建状态图
    workflow = StateGraph(TravelState)

    # 添加节点
    workflow.add_node("message_processor", message_processor)
    workflow.add_node("travel_planner", travel_planner)
    workflow.add_node("response_generator", response_generator)

    # 设置入口点
    workflow.set_entry_point("message_processor")

    # 添加边
    workflow.add_edge("message_processor", "travel_planner")
    workflow.add_edge("travel_planner", "response_generator")
    workflow.add_edge("response_generator", END)

    logger.info("旅行代理工作流图创建成功")
    return workflow


def create_travel_agent():
    """创建编译后的旅行代理实例，供应用使用"""
    graph = create_graph()
    compiled_graph = graph.compile()
    logger.info("旅行代理实例创建成功")
    return compiled_graph
