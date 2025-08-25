"""LangGraph旅游规划图定义"""

import os
from typing import TypedDict, List, Dict, Any, Optional
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
import logging

# 导入业务逻辑层
from .core.workflow import (
    message_parser,
    travel_info_extractor,
    destination_validator,
    budget_analyzer,
    duration_planner,
    travel_planner_node,
    plan_optimizer,
    fallback_handler,
    response_formatter,
)

logger = logging.getLogger(__name__)


# 定义旅行状态类型
class TravelAgentState(TypedDict):
    """旅行代理状态"""

    messages: List
    current_plan: Dict[str, Any]
    user_preferences: Dict[str, Any]
    extracted_info: Dict[str, Any]
    travel_request: Any
    # 新增字段用于新的流程
    parsed_message: Optional[str]
    current_step: Optional[str]
    destination_valid: Optional[bool]
    budget_analysis: Optional[Dict[str, Any]]
    duration_plan: Optional[Dict[str, Any]]
    travel_plan: Optional[Any]
    plan_error: Optional[str]
    optimized_plan: Optional[Any]
    fallback_response: Optional[str]


# 创建LLM实例
llm = ChatOpenAI(
    model=os.getenv("OPENAI_MODEL", "gpt-4.1"),
    temperature=float(os.getenv("OPENAI_TEMPERATURE", "0.7")),
    max_tokens=int(os.getenv("OPENAI_MAX_TOKENS", "4000")),
    openai_api_base=os.getenv("OPENAI_BASE_URL"),
)

# 构建图
graph = StateGraph(TravelAgentState)

# 添加节点
graph.add_node("message_parser", message_parser)  # 消息解析器
graph.add_node("travel_info_extractor", travel_info_extractor)  # 旅行信息提取器
graph.add_node("destination_validator", destination_validator)  # 目的地验证器
graph.add_node("budget_analyzer", budget_analyzer)  # 预算分析器
graph.add_node("duration_planner", duration_planner)  # 行程时长规划器
graph.add_node("travel_planner", travel_planner_node)  # 旅行规划器
graph.add_node("plan_optimizer", plan_optimizer)  # 计划优化器
graph.add_node("fallback_handler", fallback_handler)  # 备用处理器
graph.add_node("response_formatter", response_formatter)  # 响应格式化器

# 设置入口点
graph.set_entry_point("message_parser")

# 添加边和条件分支
graph.add_edge("message_parser", "travel_info_extractor")

# 从信息提取器到目的地验证器
graph.add_edge("travel_info_extractor", "destination_validator")

# 目的地验证后的分支
graph.add_conditional_edges(
    "destination_validator",
    lambda state: (
        "budget_analyzer"
        if state.get("destination_valid", False)
        else "fallback_handler"
    ),
)

# 预算分析器到时长规划器
graph.add_edge("budget_analyzer", "duration_planner")

# 时长规划器到旅行规划器
graph.add_edge("duration_planner", "travel_planner")

# 旅行规划器到计划优化器
graph.add_edge("travel_planner", "plan_optimizer")

# 计划优化器到响应格式化器
graph.add_edge("plan_optimizer", "response_formatter")

# 从备用处理器到响应格式化器
graph.add_edge("fallback_handler", "response_formatter")

# 响应格式化器到结束
graph.add_edge("response_formatter", END)

# 编译图
graph = graph.compile()


def create_travel_agent():
    """创建旅行代理实例"""
    return graph
