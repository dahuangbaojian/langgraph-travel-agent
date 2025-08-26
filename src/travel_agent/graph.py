"""LangGraph旅游规划图定义 - 专业化智能版本"""

import os
from typing import TypedDict, List, Dict, Any, Optional, Union
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
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
    response_formatter,
    # 新增专业化节点
    intent_classifier,
    tool_orchestrator,
    plan_validator,
    dynamic_planner,
    quality_assessor,
    error_recovery,
    # 智能路由函数
    route_by_intent,
    route_by_complexity,
    route_by_validation,
    route_by_quality,
    route_by_error,
)

logger = logging.getLogger(__name__)


# 定义旅行状态类型 - 专业化扩展
class TravelAgentState(TypedDict):
    """旅行代理状态 - 专业化版本"""

    # 基础消息
    messages: List
    current_plan: Dict[str, Any]
    user_preferences: Dict[str, Any]

    # 智能解析
    parsed_message: Optional[str]
    intent_analysis: Optional[Dict[str, Any]]
    intent_type: Optional[str]  # 新增：意图类型分类
    complexity_level: Optional[str]  # 新增：复杂度等级

    # 信息提取
    extracted_info: Optional[Dict[str, Any]]
    destination_valid: Optional[bool]

    # 专业分析
    budget_analysis: Optional[Dict[str, Any]]
    duration_plan: Optional[Dict[str, Any]]
    travel_plan: Optional[Any]

    # 智能优化
    optimized_plan: Optional[Any]
    plan_quality_score: Optional[float]  # 新增：计划质量评分

    # 工具集成
    active_tools: Optional[List[str]]  # 新增：当前激活的工具
    tool_results: Optional[Dict[str, Any]]  # 新增：工具执行结果

    # 错误处理
    plan_error: Optional[str]
    error_type: Optional[str]  # 新增：错误类型
    recovery_attempts: Optional[int]  # 新增：恢复尝试次数

    # 流程控制
    current_step: Optional[str]
    next_steps: Optional[List[str]]  # 新增：下一步计划
    should_continue: Optional[bool]  # 新增：是否继续执行


# LLM实例将在需要时延迟创建

# 构建专业化智能图
graph = StateGraph(TravelAgentState)

# 添加专业化节点
graph.add_node("intent_classifier", intent_classifier)  # 智能意图分类器
graph.add_node("message_parser", message_parser)  # 消息解析器
graph.add_node("travel_info_extractor", travel_info_extractor)  # 旅行信息提取器
graph.add_node("tool_orchestrator", tool_orchestrator)  # 工具编排器
graph.add_node("destination_validator", destination_validator)  # 目的地验证器
graph.add_node("budget_analyzer", budget_analyzer)  # 预算分析器
graph.add_node("duration_planner", duration_planner)  # 行程时长规划器
graph.add_node("travel_planner", travel_planner_node)  # 旅行规划器
graph.add_node("plan_validator", plan_validator)  # 计划验证器
graph.add_node("dynamic_planner", dynamic_planner)  # 动态规划器
graph.add_node("plan_optimizer", plan_optimizer)  # 计划优化器
graph.add_node("quality_assessor", quality_assessor)  # 质量评估器
graph.add_node("error_recovery", error_recovery)  # 错误恢复器
graph.add_node("response_formatter", response_formatter)  # 响应格式化器

# 设置入口点
graph.set_entry_point("intent_classifier")


# 智能路由函数已移至 workflow.py


# 添加智能条件边
graph.add_conditional_edges(
    "intent_classifier",
    route_by_intent,
    {
        "message_parser": "message_parser",
        "plan_validator": "plan_validator",
        "tool_orchestrator": "tool_orchestrator",
        "error_recovery": "error_recovery",
    },
)

graph.add_conditional_edges(
    "message_parser",
    route_by_complexity,
    {
        "travel_planner": "travel_planner",
        "destination_validator": "destination_validator",
        "tool_orchestrator": "tool_orchestrator",
    },
)

graph.add_conditional_edges(
    "destination_validator",
    route_by_validation,
    {
        "budget_analyzer": "budget_analyzer",
        "error_recovery": "error_recovery",
    },
)

# 预算分析后的智能路由
graph.add_edge("budget_analyzer", "duration_planner")
graph.add_edge("duration_planner", "travel_planner")

# 旅行规划后的质量评估
graph.add_edge("travel_planner", "plan_validator")
graph.add_edge("plan_validator", "quality_assessor")

# 质量评估后的智能路由
graph.add_conditional_edges(
    "quality_assessor",
    route_by_quality,
    {
        "response_formatter": "response_formatter",
        "plan_optimizer": "plan_optimizer",
        "dynamic_planner": "dynamic_planner",
    },
)

# 优化和动态规划后的路由
graph.add_edge("plan_optimizer", "quality_assessor")
graph.add_edge("dynamic_planner", "quality_assessor")

# 错误恢复后的智能路由
graph.add_conditional_edges(
    "error_recovery",
    route_by_error,
    {
        "response_formatter": "response_formatter",
        "destination_validator": "destination_validator",
        "dynamic_planner": "dynamic_planner",
        "tool_orchestrator": "tool_orchestrator",
    },
)

# 工具编排后的路由
graph.add_edge("tool_orchestrator", "destination_validator")

# 响应格式化器到结束
graph.add_edge("response_formatter", END)

# 编译图
compiled_graph = graph.compile()

logger.info("专业化智能旅游规划图构建完成")


def create_travel_agent():
    """创建旅行代理实例"""
    return compiled_graph
