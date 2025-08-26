"""智能路由函数模块"""

from typing import Dict, Any


def route_by_intent(state: Dict[str, Any]) -> str:
    """根据意图类型智能路由"""
    intent_type = state.get("intent_type", "travel_planning")

    if intent_type == "travel_planning":
        return "message_parser"
    elif intent_type == "travel_modification":
        return "plan_validator"
    elif intent_type == "travel_consultation":
        return "tool_orchestrator"
    elif intent_type == "error_recovery":
        return "error_recovery"
    else:
        return "message_parser"


def route_by_complexity(state: Dict[str, Any]) -> str:
    """根据复杂度智能路由"""
    complexity = state.get("complexity_level", "medium")

    if complexity == "simple":
        return "travel_planner"  # 简单需求直接规划
    elif complexity == "medium":
        return "destination_validator"  # 中等复杂度需要验证
    else:  # complex
        return "tool_orchestrator"  # 复杂需求需要工具支持


def route_by_validation(state: Dict[str, Any]) -> str:
    """根据验证结果智能路由"""
    destination_valid = state.get("destination_valid", False)
    extracted_info = state.get("extracted_info", {})

    # 如果目的地验证失败，但我们已经提取了信息，尝试继续
    if destination_valid:
        return "budget_analyzer"
    elif extracted_info and extracted_info.get("destination"):
        # 有目的地信息但验证失败，可能是LLM验证问题，继续流程
        return "budget_analyzer"
    else:
        return "error_recovery"


def route_by_quality(state: Dict[str, Any]) -> str:
    """根据质量评分智能路由"""
    quality_score = state.get("plan_quality_score", 0.0)

    if quality_score >= 8.0:
        return "response_formatter"  # 高质量计划直接输出
    elif quality_score >= 6.0:
        return "plan_optimizer"  # 中等质量需要优化
    else:
        return "dynamic_planner"  # 低质量需要重新规划


def route_by_error(state: Dict[str, Any]) -> str:
    """根据错误类型智能路由"""
    error_type = state.get("error_type", "unknown")
    recovery_attempts = state.get("recovery_attempts", 0)

    if recovery_attempts >= 3:
        return "response_formatter"  # 超过重试次数，直接输出
    elif error_type == "validation_error":
        return "destination_validator"  # 验证错误，重新验证
    elif error_type == "planning_error":
        return "dynamic_planner"  # 重新规划
    else:
        return "tool_orchestrator"  # 其他错误，尝试工具解决
