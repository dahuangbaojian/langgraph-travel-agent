"""旅行代理主图定义"""

import logging
from typing import Dict, Any
from langgraph.graph import StateGraph, END

from .core.workflow.nodes import (
    message_processor,
    travel_planner,
    route_generator,
    response_generator,
)
from .core.workflow.state import TravelState

logger = logging.getLogger(__name__)


def create_graph() -> StateGraph:
    """创建旅行代理工作流图"""

    # 创建状态图
    workflow = StateGraph(TravelState)

    # 添加节点
    workflow.add_node("message_processor", message_processor)  # 处理用户输入
    workflow.add_node("travel_planner", travel_planner)  # 规划旅行计划
    workflow.add_node("route_generator", route_generator)  # 生成具体路线
    workflow.add_node("response_generator", response_generator)  # 格式化响应输出

    # 设置入口点
    workflow.set_entry_point("message_processor")

    # 添加边 - 清晰的数据流
    workflow.add_edge("message_processor", "travel_planner")  # 输入 → 规划
    workflow.add_edge("travel_planner", "route_generator")  # 规划 → 路线生成
    workflow.add_edge("route_generator", "response_generator")  # 路线 → 响应格式化
    workflow.add_edge("response_generator", END)  # 输出 → 结束

    logger.info("旅行代理工作流图创建成功")
    return workflow


def create_travel_agent():
    """创建编译后的旅行代理实例，供应用使用"""
    graph = create_graph()
    compiled_graph = graph.compile()
    logger.info("旅行代理实例创建成功")
    return compiled_graph
