"""简化的核心节点模块 - 整合复杂业务逻辑"""

import json
import logging
from typing import Dict, Any
from langchain_core.messages import HumanMessage
from langgraph.graph.message import add_messages

from .utils import get_llm, _extract_travel_info_with_llm
from ..prompts.intent_analysis import INTENT_ANALYSIS_PROMPT
from ..prompts.budget_analysis import BUDGET_ANALYSIS_PROMPT
from ..prompts.duration_planning import DURATION_PLANNING_PROMPT

logger = logging.getLogger(__name__)


async def message_processor(state: Dict[str, Any]) -> Dict[str, Any]:
    """消息处理和信息提取 - 整合多个节点的功能"""
    try:
        # 1. 获取用户消息
        messages = state["messages"]
        user_message = ""

        if isinstance(messages[-1], dict):
            user_message = messages[-1].get("content", "")
        else:
            user_message = messages[-1].content

        logger.info(f"处理用户消息: {user_message}")

        # 2. 意图分析
        try:
            intent_prompt = INTENT_ANALYSIS_PROMPT.format(message=user_message)
            llm = get_llm()
            if llm:
                response = llm.invoke([HumanMessage(content=intent_prompt)])
                intent_analysis = json.loads(response.content.strip())
            else:
                intent_analysis = {
                    "intent": "旅行规划",
                    "complexity": "中等",
                    "suggested_tools": ["航班", "酒店", "景点", "汇率", "天气"],
                }
        except Exception as e:
            logger.warning(f"意图分析失败，使用默认值: {e}")
            intent_analysis = {
                "intent": "旅行规划",
                "complexity": "中等",
                "suggested_tools": ["航班", "酒店", "景点", "汇率", "天气"],
            }

        # 3. 旅行信息提取
        travel_info = await _extract_travel_info_with_llm(user_message)

        # 4. 存储处理结果
        state["user_input"] = user_message
        state["intent_analysis"] = intent_analysis
        state["travel_info"] = travel_info
        state["current_step"] = "message_processed"

        logger.info(f"消息处理完成: {travel_info}")

    except Exception as e:
        logger.error(f"消息处理失败: {e}")
        # 使用基本默认值
        state["user_input"] = user_message
        state["travel_info"] = {
            "destination": "未知目的地",
            "duration_days": 3,
            "budget": 5000,
            "people_count": 2,
        }
        state["current_step"] = "message_processed"

    return state


async def travel_planner(state: Dict[str, Any]) -> Dict[str, Any]:
    """旅行规划核心逻辑 - 整合预算分析、时长规划等功能"""
    try:
        travel_info = state.get("travel_info", {})
        intent_analysis = state.get("intent_analysis", {})

        destination = travel_info.get("destination", "")
        duration_days = travel_info.get("duration_days", 3)
        budget = travel_info.get("budget", 5000)
        people_count = travel_info.get("people_count", 2)

        logger.info(f"开始规划旅行: {destination}, {duration_days}天, {budget}元")

        # 1. 预算分析
        try:
            budget_prompt = BUDGET_ANALYSIS_PROMPT.format(
                destination=destination,
                budget_level=travel_info.get("budget_level", "中等"),
                duration_days=duration_days,
                people_count=people_count,
            )

            llm = get_llm()
            if llm:
                response = llm.invoke([HumanMessage(content=budget_prompt)])
                budget_analysis = json.loads(response.content.strip())
            else:
                budget_analysis = {
                    "total_budget": budget,
                    "daily_budget": budget // duration_days,
                    "budget_breakdown": {
                        "hotel": 0.4,
                        "restaurant": 0.25,
                        "attractions": 0.15,
                        "transport": 0.15,
                        "other": 0.05,
                    },
                }
        except Exception as e:
            logger.warning(f"预算分析失败，使用默认值: {e}")
            budget_analysis = {
                "total_budget": budget,
                "daily_budget": budget // duration_days,
                "budget_breakdown": {
                    "hotel": 0.4,
                    "restaurant": 0.25,
                    "attractions": 0.15,
                    "transport": 0.15,
                    "other": 0.05,
                },
            }

        # 2. 时长规划
        try:
            duration_prompt = DURATION_PLANNING_PROMPT.format(
                destination=destination,
                budget=budget,
                preferences=", ".join(travel_info.get("preferences", [])),
            )

            llm = get_llm()
            if llm:
                response = llm.invoke([HumanMessage(content=duration_prompt)])
                duration_plan = json.loads(response.content.strip())
            else:
                duration_plan = {
                    "recommended_duration": duration_days,
                    "reason": f"基于您的要求，建议{duration_days}天行程",
                    "time_optimization": {},
                }
        except Exception as e:
            logger.warning(f"时长规划失败，使用默认值: {e}")
            duration_plan = {
                "recommended_duration": duration_days,
                "reason": f"基于您的要求，建议{duration_days}天行程",
                "time_optimization": {},
            }

        # 3. 生成旅行计划
        travel_plan = {
            "destination": destination,
            "duration": duration_plan.get("recommended_duration", duration_days),
            "budget": budget_analysis.get("total_budget", budget),
            "daily_budget": budget_analysis.get(
                "daily_budget", budget // duration_days
            ),
            "budget_breakdown": budget_analysis.get("budget_breakdown", {}),
            "duration_reason": duration_plan.get(
                "reason", f"基于您的要求，建议{duration_days}天行程"
            ),
            "suggested_tools": intent_analysis.get("suggested_tools", []),
            "next_step": intent_analysis.get(
                "next_step", "请告诉我您的具体需求，我将为您定制详细行程"
            ),
        }

        # 4. 存储规划结果
        state["travel_plan"] = travel_plan
        state["budget_analysis"] = budget_analysis
        state["duration_plan"] = duration_plan
        state["current_step"] = "travel_planned"

        logger.info(f"旅行规划完成: {travel_plan}")

    except Exception as e:
        logger.error(f"旅行规划失败: {e}")
        # 使用基本计划
        duration_days = travel_info.get("duration_days", 3)
        destination = travel_info.get("destination", "未知目的地")
        state["travel_plan"] = {
            "destination": destination,
            "duration": duration_days,
            "budget": travel_info.get("budget", 5000),
            "daily_budget": travel_info.get("budget", 5000) // duration_days,
            "budget_breakdown": {},
            "duration_reason": f"基于基本需求，建议{duration_days}天行程",
            "suggested_tools": ["航班", "酒店", "景点"],
            "next_step": "请告诉我您的具体需求",
        }
        state["current_step"] = "travel_planned"

    return state


async def response_generator(state: Dict[str, Any]) -> Dict[str, Any]:
    """响应生成器 - 整合所有信息生成最终响应"""
    try:
        travel_plan = state.get("travel_plan", {})
        travel_info = state.get("travel_info", {})

        destination = travel_plan.get("destination", "旅行目的地")
        duration = travel_plan.get("duration", "未知")
        budget = travel_plan.get("budget", "未知")
        daily_budget = travel_plan.get("daily_budget", "未知")
        suggested_tools = travel_plan.get("suggested_tools", [])
        next_step = travel_plan.get("next_step", "请告诉我您的具体需求")

        # 生成工具服务列表
        tool_list = ""
        if suggested_tools:
            tool_list = "\n".join(
                [f"• {tool}: 已为您准备相关服务" for tool in suggested_tools]
            )
        else:
            tool_list = "• 基础旅行服务: 已为您准备"

        # 生成详细响应
        response_content = f"""🎯 **您的{destination}旅行计划已生成！**

📅 **行程概览**
• 目的地：{destination}
• 建议天数：{duration}天
• 总预算：{budget}元
• 日均预算：{daily_budget}元

🔧 **已为您准备了以下工具服务**
{tool_list}

💡 **下一步建议**
{next_step}

🌟 **个性化定制**
如果您有特殊偏好（如美食、购物、文化体验等），请告诉我，我会为您调整行程安排。

📋 **预算分配建议**
• 住宿：{travel_plan.get('budget_breakdown', {}).get('hotel', 0.4) * 100:.0f}%
• 餐饮：{travel_plan.get('budget_breakdown', {}).get('restaurant', 0.25) * 100:.0f}%
• 景点：{travel_plan.get('budget_breakdown', {}).get('attractions', 0.15) * 100:.0f}%
• 交通：{travel_plan.get('budget_breakdown', {}).get('transport', 0.15) * 100:.0f}%
• 其他：{travel_plan.get('budget_breakdown', {}).get('other', 0.05) * 100:.0f}%"""

        # 添加AI响应到状态
        from langgraph.graph.message import add_messages

        state = add_messages(
            state, [{"role": "assistant", "content": response_content}]
        )
        state["response"] = response_content
        state["current_step"] = "response_generated"

        logger.info("响应生成完成")

    except Exception as e:
        logger.error(f"响应生成失败: {e}")
        # 生成错误响应
        error_response = "抱歉，我在生成响应时遇到了一些问题。请重新描述您的旅行需求。"
        from langgraph.graph.message import add_messages

        state = add_messages(state, [{"role": "assistant", "content": error_response}])
        state["response"] = error_response
        state["current_step"] = "response_generation_failed"

    return state
