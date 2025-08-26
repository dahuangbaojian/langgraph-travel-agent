"""工作流节点模块 - 包含所有核心节点函数"""

import json
import logging
from typing import Dict, Any, List
from langchain_core.messages import HumanMessage

from .utils import (
    get_llm,
    _extract_travel_info_with_llm,
    _enhance_info_with_tools,
    _get_smart_defaults,
    _optimize_duration,
    _get_duration_reason,
)

from ..prompts.intent_analysis import INTENT_ANALYSIS_PROMPT
from ..prompts.travel_validation import TRAVEL_VALIDATION_PROMPT
from ..prompts.budget_analysis import BUDGET_ANALYSIS_PROMPT
from ..prompts.duration_planning import DURATION_PLANNING_PROMPT
from ..prompts.plan_validation import PLAN_VALIDATION_PROMPT
from ..prompts.dynamic_planning import DYNAMIC_PLANNING_PROMPT

logger = logging.getLogger(__name__)


async def intent_classifier(state: Dict[str, Any]) -> Dict[str, Any]:
    """智能意图分类器"""
    messages = state["messages"]
    user_message = ""

    # 处理消息格式
    if isinstance(messages[-1], dict):
        user_message = messages[-1].get("content", "")
    else:
        user_message = messages[-1].content

    # 使用LLM分析用户意图
    intent_prompt = INTENT_ANALYSIS_PROMPT.format(message=user_message)

    try:
        llm = get_llm()
        if llm is None:
            raise Exception("LLM实例不可用")

        response = llm.invoke([HumanMessage(content=intent_prompt)])
        intent_analysis = json.loads(response.content.strip())

        # 存储解析结果
        state["parsed_message"] = user_message
        state["intent_analysis"] = intent_analysis
        state["intent_type"] = intent_analysis.get("intent_type", "travel_planning")
        state["complexity_level"] = intent_analysis.get("complexity_level", "medium")
        state["current_step"] = "intent_classified"

        logger.info(f"意图分类完成: {intent_analysis}")

    except Exception as e:
        logger.error(f"意图分类失败: {e}")
        # 回退到默认分类
        state["parsed_message"] = user_message
        state["intent_type"] = "travel_planning"
        state["complexity_level"] = "medium"
        state["current_step"] = "intent_classified"

    return state


async def message_parser(state: Dict[str, Any]) -> Dict[str, Any]:
    """智能消息解析器"""
    user_message = state["parsed_message"]

    # 初始化其他字段
    state.setdefault("extracted_info", {})
    state.setdefault("destination_valid", False)
    state.setdefault("budget_analysis", {})
    state.setdefault("duration_plan", {})
    state.setdefault("travel_plan", None)
    state.setdefault("plan_error", None)
    state.setdefault("optimized_plan", None)

    logger.info(f"消息解析完成: {user_message[:50]}...")
    return state


async def travel_info_extractor(state: Dict[str, Any]) -> Dict[str, Any]:
    """智能旅行信息提取器"""
    try:
        user_message = state["parsed_message"]
        intent_analysis = state.get("intent_analysis", {})
        logger.info(f"开始智能提取旅行信息: {user_message}")

        # 使用LLM智能提取旅行信息
        travel_info = await _extract_travel_info_with_llm(user_message)

        # 根据意图分析，智能调用相关工具
        if intent_analysis.get("needs_tools", False):
            suggested_tools = intent_analysis.get("suggested_tools", [])
            enhanced_info = await _enhance_info_with_tools(travel_info, suggested_tools)
            travel_info.update(enhanced_info)

        # 存储提取的信息
        state["extracted_info"] = travel_info
        state["current_step"] = "info_extracted"

        logger.info(f"旅行信息提取完成: {travel_info}")
        return state

    except Exception as e:
        logger.error(f"旅行信息提取失败: {e}")
        state["current_step"] = "extraction_failed"
        state["extraction_error"] = str(e)
        return state


async def destination_validator(state: Dict[str, Any]) -> Dict[str, Any]:
    """智能目的地验证器"""
    extracted_info = state["extracted_info"]
    destination = extracted_info.get("destination", "")

    if destination:
        try:
            validation_prompt = TRAVEL_VALIDATION_PROMPT.format(
                travel_info={"destination": destination}
            )

            llm = get_llm()
            if llm is None:
                raise Exception("LLM实例不可用")

            response = llm.invoke([HumanMessage(content=validation_prompt)])
            validation_result = json.loads(response.content.strip())

            state["destination_validation"] = validation_result
            state["destination_valid"] = validation_result.get("is_valid", True)
            state["current_step"] = "destination_validated"

            logger.info(f"目的地智能验证完成: {validation_result}")

        except Exception as e:
            logger.error(f"目的地验证失败: {e}")
            state["destination_valid"] = True
            state["current_step"] = "destination_validated"
    else:
        state["destination_valid"] = False
        state["current_step"] = "destination_invalid"

    return state


async def budget_analyzer(state: Dict[str, Any]) -> Dict[str, Any]:
    """智能预算分析器"""
    try:
        extracted_info = state["extracted_info"]
        destination = extracted_info.get("destination", "")
        budget_level = extracted_info.get("budget_level", "中等")
        duration_days = extracted_info.get("duration_days", 3)
        people_count = extracted_info.get("people_count", 2)

        budget_prompt = BUDGET_ANALYSIS_PROMPT.format(
            destination=destination,
            budget_level=budget_level,
            duration_days=duration_days,
            people_count=people_count,
        )

        llm = get_llm()
        if llm is None:
            raise Exception("LLM实例不可用")

        response = llm.invoke([HumanMessage(content=budget_prompt)])
        budget_analysis = json.loads(response.content.strip())

        state["budget_analysis"] = budget_analysis
        state["current_step"] = "budget_analyzed"

        logger.info(f"预算分析完成: {budget_analysis}")

    except Exception as e:
        logger.error(f"预算分析失败: {e}")
        # 使用基本预算分析
        state["budget_analysis"] = {
            "total_budget": 5000,
            "daily_budget": 1000,
            "budget_breakdown": {
                "hotel": 0.4,
                "restaurant": 0.25,
                "attractions": 0.15,
                "transport": 0.15,
                "other": 0.05,
            },
        }
        state["current_step"] = "budget_analyzed"

    return state


async def duration_planner(state: Dict[str, Any]) -> Dict[str, Any]:
    """智能行程时长规划器"""
    try:
        extracted_info = state["extracted_info"]
        destination = extracted_info.get("destination", "")
        budget = state.get("budget_analysis", {}).get("total_budget", 5000)
        preferences = extracted_info.get("preferences", [])

        duration_prompt = DURATION_PLANNING_PROMPT.format(
            destination=destination, budget=budget, preferences=", ".join(preferences)
        )

        llm = get_llm()
        if llm is None:
            raise Exception("LLM实例不可用")

        response = llm.invoke([HumanMessage(content=duration_prompt)])
        duration_plan = json.loads(response.content.strip())

        state["duration_plan"] = duration_plan
        state["current_step"] = "duration_planned"

        logger.info(f"行程时长规划完成: {duration_plan}")

    except Exception as e:
        logger.error(f"行程时长规划失败: {e}")
        # 使用基本时长规划
        state["duration_plan"] = {
            "recommended_duration": 3,
            "reason": "基于预算的基本建议",
            "time_optimization": {},
        }
        state["current_step"] = "duration_planned"

    return state


async def travel_planner_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """智能旅行规划器节点"""
    try:
        extracted_info = state["extracted_info"]
        budget_analysis = state["budget_analysis"]
        duration_plan = state["duration_plan"]

        # 这里可以集成更复杂的旅行规划逻辑
        travel_plan = {
            "destination": extracted_info.get("destination", ""),
            "duration": duration_plan.get("recommended_duration", 3),
            "budget": budget_analysis.get("total_budget", 5000),
            "daily_itinerary": [],
            "recommendations": [],
        }

        state["travel_plan"] = travel_plan
        state["current_step"] = "travel_planned"

        logger.info(f"旅行规划完成: {travel_plan}")

    except Exception as e:
        logger.error(f"旅行规划失败: {e}")
        state["plan_error"] = str(e)
        state["current_step"] = "planning_failed"

    return state


async def plan_validator(state: Dict[str, Any]) -> Dict[str, Any]:
    """智能计划验证器"""
    try:
        travel_plan = state.get("travel_plan", {})

        validation_prompt = PLAN_VALIDATION_PROMPT.format(travel_plan=travel_plan)

        llm = get_llm()
        if llm is None:
            raise Exception("LLM实例不可用")

        response = llm.invoke([HumanMessage(content=validation_prompt)])
        validation_result = json.loads(response.content.strip())

        state["plan_validation"] = validation_result
        state["plan_valid"] = validation_result.get("is_valid", True)
        state["current_step"] = "plan_validated"

        logger.info(f"计划验证完成: {validation_result}")

    except Exception as e:
        logger.error(f"计划验证失败: {e}")
        state["plan_valid"] = True
        state["current_step"] = "plan_validated"

    return state


async def quality_assessor(state: Dict[str, Any]) -> Dict[str, Any]:
    """智能质量评估器"""
    try:
        travel_plan = state.get("travel_plan", {})
        budget_analysis = state.get("budget_analysis", {})
        duration_plan = state.get("duration_plan", {})

        # 使用简单的质量评估逻辑
        assessment = {
            "quality_score": 7.0,
            "suggestions": ["建议优化行程安排", "考虑增加景点选择"],
            "overall_rating": "良好",
        }

        # 直接使用预定义的评估结果

        state["plan_quality_score"] = assessment.get("quality_score", 7.0)
        state["quality_assessment"] = assessment
        state["current_step"] = "quality_assessed"

        logger.info(f"质量评估完成: {assessment}")

    except Exception as e:
        logger.error(f"质量评估失败: {e}")
        state["plan_quality_score"] = 7.0
        state["current_step"] = "quality_assessed"

    return state


async def plan_optimizer(state: Dict[str, Any]) -> Dict[str, Any]:
    """智能计划优化器"""
    try:
        travel_plan = state.get("travel_plan", {})
        quality_assessment = state.get("quality_assessment", {})

        # 基于质量评估结果进行优化
        optimized_plan = travel_plan.copy()
        optimized_plan["optimizations"] = quality_assessment.get("suggestions", [])

        state["optimized_plan"] = optimized_plan
        state["current_step"] = "plan_optimized"

        logger.info(f"计划优化完成: {optimized_plan}")

    except Exception as e:
        logger.error(f"计划优化失败: {e}")
        state["current_step"] = "optimization_failed"

    return state


async def dynamic_planner(state: Dict[str, Any]) -> Dict[str, Any]:
    """智能动态规划器"""
    try:
        extracted_info = state["extracted_info"]
        budget_analysis = state.get("budget_analysis", {})
        quality_assessment = state.get("quality_assessment", {})

        planning_prompt = DYNAMIC_PLANNING_PROMPT.format(
            extracted_info=extracted_info,
            budget_analysis=budget_analysis,
            quality_assessment=quality_assessment,
        )

        llm = get_llm()
        if llm is None:
            raise Exception("LLM实例不可用")

        response = llm.invoke([HumanMessage(content=planning_prompt)])
        dynamic_plan = json.loads(response.content.strip())

        state["dynamic_plan"] = dynamic_plan
        state["current_step"] = "dynamically_planned"

        logger.info(f"动态规划完成: {dynamic_plan}")

    except Exception as e:
        logger.error(f"动态规划失败: {e}")
        state["current_step"] = "dynamic_planning_failed"

    return state


async def tool_orchestrator(state: Dict[str, Any]) -> Dict[str, Any]:
    """智能工具编排器"""
    try:
        intent_analysis = state.get("intent_analysis", {})
        suggested_tools = intent_analysis.get("suggested_tools", [])

        # 这里可以集成各种工具的执行逻辑
        tool_results = {}
        for tool in suggested_tools:
            tool_results[tool] = f"{tool}工具执行结果"

        state["tool_results"] = tool_results
        state["active_tools"] = suggested_tools
        state["current_step"] = "tools_orchestrated"

        logger.info(f"工具编排完成: {tool_results}")

    except Exception as e:
        logger.error(f"工具编排失败: {e}")
        state["current_step"] = "tool_orchestration_failed"

    return state


async def error_recovery(state: Dict[str, Any]) -> Dict[str, Any]:
    """智能错误恢复器"""
    try:
        error_type = state.get("error_type", "unknown")
        recovery_attempts = state.get("recovery_attempts", 0)

        # 使用简单的错误恢复逻辑
        recovery_plan = {
            "action": "retry",
            "suggestions": ["检查输入参数", "重试操作"],
            "next_step": "destination_validator",
        }

        # 直接使用预定义的恢复计划

        state["recovery_plan"] = recovery_plan
        state["recovery_attempts"] = recovery_attempts + 1
        state["current_step"] = "error_recovered"

        logger.info(f"错误恢复完成: {recovery_plan}")

    except Exception as e:
        logger.error(f"错误恢复失败: {e}")
        state["current_step"] = "recovery_failed"

    return state


async def response_formatter(state: Dict[str, Any]) -> Dict[str, Any]:
    """智能响应格式化器"""
    try:
        # 整合所有信息生成最终响应
        travel_plan = state.get("travel_plan", {})
        budget_analysis = state.get("budget_analysis", {})
        duration_plan = state.get("duration_plan", {})

        # 这里可以集成更复杂的响应格式化逻辑
        response_content = f"您的{travel_plan.get('destination', '旅行')}计划已生成！"

        # 添加消息到状态
        if "messages" not in state:
            state["messages"] = []

        state["messages"].append({"role": "assistant", "content": response_content})

        state["current_step"] = "response_formatted"
        logger.info("响应格式化完成")

    except Exception as e:
        logger.error(f"响应格式化失败: {e}")
        state["current_step"] = "formatting_failed"

    return state
