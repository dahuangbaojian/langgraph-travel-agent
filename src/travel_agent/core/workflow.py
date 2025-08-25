"""旅游规划工作流节点"""

import re
import json
import logging
from typing import Dict, Any, List
from langchain_core.messages import HumanMessage

from .prompts import (
    INTENT_ANALYSIS_PROMPT,
    TRAVEL_VALIDATION_PROMPT,
    BUDGET_ANALYSIS_PROMPT,
    DURATION_PLANNING_PROMPT,
    CITY_EXTRACTION_PROMPT,
    ACTIVITY_PARSING_PROMPT,
    SMART_DEFAULTS_PROMPT,
    TRAVEL_EXTRACTION_PROMPT,
    INTENT_CLASSIFICATION_PROMPT,
    PLAN_VALIDATION_PROMPT,
    DYNAMIC_PLANNING_PROMPT,
)
from ..tools.planner import travel_planner

logger = logging.getLogger(__name__)

# 创建LLM实例
from langchain_openai import ChatOpenAI
import os

llm = ChatOpenAI(
    model=os.getenv("OPENAI_MODEL", "gpt-4.1"),
    temperature=float(os.getenv("OPENAI_TEMPERATURE", "0.7")),
    max_tokens=int(os.getenv("OPENAI_MAX_TOKENS", "4000")),
    openai_api_base=os.getenv("OPENAI_BASE_URL"),
)


async def message_parser(state: Dict[str, Any]) -> Dict[str, Any]:
    """智能消息解析器 - 使用LLM分析用户意图"""
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
        response = llm.invoke([HumanMessage(content=intent_prompt)])
        intent_analysis = json.loads(response.content.strip())

        # 存储解析结果
        state["parsed_message"] = user_message
        state["intent_analysis"] = intent_analysis
        state["current_step"] = "message_analyzed"

        logger.info(f"消息意图分析完成: {intent_analysis}")

    except Exception as e:
        logger.error(f"意图分析失败: {e}")
        # 回退到简单解析
        state["parsed_message"] = user_message
        state["intent_analysis"] = {
            "intent": "旅行规划",
            "complexity": "中等",
            "needs_tools": True,
            "suggested_tools": ["天气", "汇率"],
            "next_step": "extract_info",
        }
        state["current_step"] = "message_parsed"

    # 初始化其他字段
    state.setdefault("extracted_info", {})
    state.setdefault("destination_valid", False)
    state.setdefault("budget_analysis", {})
    state.setdefault("duration_plan", {})
    state.setdefault("travel_plan", None)
    state.setdefault("plan_error", None)
    state.setdefault("optimized_plan", None)
    state.setdefault("fallback_response", None)

    logger.info(f"消息解析完成: {user_message[:50]}...")
    return state


async def travel_info_extractor(state: Dict[str, Any]) -> Dict[str, Any]:
    """智能旅行信息提取器 - LLM + Tools 结合"""
    try:
        user_message = state["parsed_message"]
        intent_analysis = state.get("intent_analysis", {})
        logger.info(f"开始智能提取旅行信息: {user_message}")

        # 使用LLM智能提取旅行信息
        travel_info = await _extract_travel_info_with_llm(user_message)

        # 根据意图分析，智能调用相关工具
        if intent_analysis.get("needs_tools", False):
            suggested_tools = intent_analysis.get("suggested_tools", [])

            # 智能工具调用
            enhanced_info = await _enhance_info_with_tools(travel_info, suggested_tools)
            travel_info.update(enhanced_info)

            logger.info(f"工具增强完成: {enhanced_info}")

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
    """智能目的地验证器 - LLM + 地理工具"""
    extracted_info = state["extracted_info"]
    destination = extracted_info.get("destination", "")

    if destination:
        # 使用LLM智能验证和增强目的地信息
        validation_prompt = TRAVEL_VALIDATION_PROMPT.format(
            travel_info={"destination": destination}
        )

        try:
            response = llm.invoke([HumanMessage(content=validation_prompt)])
            validation_result = json.loads(response.content.strip())

            # 存储验证结果
            state["destination_validation"] = validation_result
            state["destination_valid"] = validation_result.get("is_valid", True)
            state["current_step"] = "destination_validated"

            logger.info(f"目的地智能验证完成: {validation_result}")

        except Exception as e:
            logger.error(f"目的地验证失败: {e}")
            # 回退到简单验证
            state["destination_valid"] = True
            state["current_step"] = "destination_validated"

    else:
        state["destination_valid"] = False
        state["current_step"] = "destination_missing"
        logger.warning("未找到有效目的地")

    return state


async def budget_analyzer(state: Dict[str, Any]) -> Dict[str, Any]:
    """智能预算分析器 - LLM + 汇率工具"""
    extracted_info = state["extracted_info"]
    budget = extracted_info.get("budget", 0)
    duration = extracted_info.get("duration_days", 1)
    currency = extracted_info.get("currency", "CNY")  # 从配置获取默认货币

    # 使用LLM智能分析预算
    budget_prompt = BUDGET_ANALYSIS_PROMPT.format(
        travel_info={"budget": budget, "duration_days": duration, "currency": currency}
    )

    try:
        response = llm.invoke([HumanMessage(content=budget_prompt)])
        budget_analysis = json.loads(response.content.strip())

        # 如果预算不是人民币，调用汇率工具
        if currency != "CNY" and budget > 0:
            try:
                from ..tools.currency import get_exchange_rate

                exchange_rate_info = await get_exchange_rate(currency, "CNY")
                if exchange_rate_info:
                    budget_analysis["exchange_rate"] = exchange_rate_info
                    # 计算人民币预算
                    rate_match = re.search(
                        r"1 {currency} = ([\d.]+) CNY", exchange_rate_info
                    )
                    if rate_match:
                        rate = float(rate_match.group(1))
                        budget_cny = budget * rate
                        budget_analysis["budget_cny"] = budget_cny
                        logger.info(
                            f"汇率转换完成: {budget} {currency} = {budget_cny:.2f} CNY"
                        )
            except Exception as e:
                logger.warning(f"汇率工具调用失败: {e}")

        # 存储分析结果
        state["budget_analysis"] = budget_analysis
        state["current_step"] = "budget_analyzed"

        logger.info(f"智能预算分析完成: {budget_analysis}")

    except Exception as e:
        logger.error(f"预算分析失败: {e}")
        # 回退到简单分析
        daily_budget = budget / duration if duration > 0 else 0

        # 智能预算等级判断
        budget_level = "中等"  # 默认中等预算

        state["budget_analysis"] = {
            "total_budget": budget,
            "daily_budget": daily_budget,
            "budget_level": budget_level,
            "is_reasonable": daily_budget >= 500,
        }
        state["current_step"] = "budget_analyzed"

    return state


async def duration_planner(state: Dict[str, Any]) -> Dict[str, Any]:
    """智能时长规划器 - LLM + 目的地分析"""
    extracted_info = state["extracted_info"]
    budget_analysis = state.get("budget_analysis", {})
    destination_validation = state.get("destination_validation", {})

    destination = extracted_info.get("destination", "")
    current_duration = extracted_info.get("duration_days", 1)
    daily_budget = budget_analysis.get("budget_analysis", {}).get("daily_budget", 0)

    # 使用LLM智能规划时长
    duration_prompt = DURATION_PLANNING_PROMPT.format(
        travel_info={
            "destination": destination,
            "duration_days": current_duration,
            "daily_budget": daily_budget,
            "local_features": destination_validation.get("local_features", []),
            "best_time": destination_validation.get("best_time", "未知"),
        }
    )

    try:
        response = llm.invoke([HumanMessage(content=duration_prompt)])
        duration_plan = json.loads(response.content.strip())

        # 存储规划结果
        state["duration_plan"] = duration_plan
        state["current_step"] = "duration_planned"

        logger.info(f"智能时长规划完成: {duration_plan}")

    except Exception as e:
        logger.error(f"时长规划失败: {e}")
        # 回退到简单规划
        optimized_duration = await _optimize_duration(
            destination, current_duration, daily_budget
        )
        state["duration_plan"] = {
            "original_duration": current_duration,
            "optimized_duration": optimized_duration,
            "reason": await _get_duration_reason(
                destination, optimized_duration, daily_budget
            ),
        }
        state["current_step"] = "duration_planned"

    return state


async def travel_planner_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """旅行规划器 - 创建详细的旅行计划，集成天气等实时数据"""
    extracted_info = state["extracted_info"]
    duration_plan = state["duration_plan"]

    # 使用优化后的时长
    duration_days = duration_plan.get(
        "optimized_duration", extracted_info.get("duration_days", 1)
    )

    try:
        # 创建旅行请求
        from ..core.models import TravelRequest

        travel_request = TravelRequest(
            destination=extracted_info["destination"],
            duration_days=duration_days,
            budget=extracted_info.get("budget", 0),
            people_count=extracted_info.get("people_count", 1),
        )

        # 调用旅行规划工具
        plan_result = travel_planner.create_travel_plan(travel_request)

        # 尝试获取目的地天气信息（如果天气工具可用）
        try:
            from ..tools.weather import get_weather_info

            weather_info = await get_weather_info(extracted_info["destination"])
            if weather_info:
                # 将天气信息添加到旅行计划中
                plan_result.weather_info = weather_info
                logger.info(f"获取到天气信息: {weather_info}")
        except Exception as e:
            logger.warning(f"获取天气信息失败: {e}")

        # 尝试获取汇率信息（如果汇率工具可用）
        try:
            from ..tools.currency import get_exchange_rate

            currency = extracted_info.get("currency", "CNY")
            if currency != "CNY":
                exchange_rate = await get_exchange_rate(currency, "CNY")
                if exchange_rate:
                    plan_result.exchange_rate = exchange_rate
                    logger.info(f"获取到汇率信息: {currency} -> CNY: {exchange_rate}")
        except Exception as e:
            logger.warning(f"获取汇率信息失败: {e}")

        state["travel_plan"] = plan_result
        state["travel_request"] = travel_request
        state["current_step"] = "plan_created"

        logger.info(f"旅行计划创建成功: {travel_request.destination} {duration_days}天")

    except Exception as e:
        logger.error(f"创建旅行计划失败: {e}")
        state["plan_error"] = str(e)
        state["current_step"] = "plan_failed"

    return state


async def plan_optimizer(state: Dict[str, Any]) -> Dict[str, Any]:
    """计划优化器 - 优化旅行计划"""
    travel_plan = state.get("travel_plan")
    budget_analysis = state.get("budget_analysis", {})

    if travel_plan and not state.get("plan_error"):
        # 优化计划
        optimized_plan = _optimize_travel_plan(travel_plan, budget_analysis)

        state["optimized_plan"] = optimized_plan
        state["current_step"] = "plan_optimized"

        logger.info("旅行计划优化完成")
    else:
        state["current_step"] = "optimization_skipped"
        logger.info("跳过计划优化")

    return state


async def response_formatter(state: Dict[str, Any]) -> Dict[str, Any]:
    """响应格式化器 - 格式化最终响应"""
    current_step = state.get("current_step", "")

    logger.info(f"响应格式化器开始，当前步骤: {current_step}")
    logger.info(f"状态内容: {state}")

    if current_step == "plan_optimized":
        # 格式化优化后的旅行计划
        travel_plan = state.get("optimized_plan", state.get("travel_plan"))
        travel_request = state.get("travel_request")

        if travel_plan and travel_request:
            # 基础旅行计划
            response_content = _format_travel_plan_response(travel_plan)

            # 添加天气信息（如果可用）
            if hasattr(travel_plan, "weather_info") and travel_plan.weather_info:
                weather_section = f"\n\n🌤️ **实时天气信息**\n{travel_plan.weather_info}"
                response_content += weather_section

            # 添加汇率信息（如果可用）
            if hasattr(travel_plan, "exchange_rate") and travel_plan.exchange_rate:
                currency = state.get("extracted_info", {}).get("currency", "未知")
                exchange_section = f"\n\n💱 **汇率信息**\n{currency} → CNY: {travel_plan.exchange_rate}"
                response_content += exchange_section

            # 添加预算分析（如果可用）
            budget_analysis = state.get("budget_analysis", {})
            if budget_analysis:
                budget_section = f"\n\n💰 **预算分析**\n"

                # 处理新的预算分析结构
                if "budget_analysis" in budget_analysis:
                    # 新结构：budget_analysis.budget_analysis
                    budget_info = budget_analysis["budget_analysis"]
                    budget_section += (
                        f"• 预算等级: {budget_info.get('budget_level', '未知')}\n"
                    )
                    daily_budget = budget_info.get("daily_budget")
                    if daily_budget is not None:
                        # 检查是否为数字类型
                        if isinstance(daily_budget, (int, float)):
                            budget_section += f"• 每日预算: {daily_budget:.0f} 元\n"
                        else:
                            budget_section += f"• 每日预算: {daily_budget}\n"
                    else:
                        budget_section += "• 每日预算: 未设置\n"
                    budget_section += (
                        f"• 预算评分: {budget_info.get('budget_rating', '未知')}/10\n"
                    )

                    # 添加预算分配
                    if "budget_allocation" in budget_analysis:
                        allocation = budget_analysis["budget_allocation"]
                        budget_section += f"• 预算分配: 住宿{allocation.get('hotel', '0%')}, 餐饮{allocation.get('food', '0%')}, 交通{allocation.get('transport', '0%')}, 景点{allocation.get('attractions', '0%')}\n"

                    # 添加建议
                    if "suggestions" in budget_info:
                        suggestions = budget_info["suggestions"]
                        if suggestions and isinstance(suggestions, list):
                            budget_section += (
                                f"• 省钱建议: {'; '.join(suggestions[:2])}\n"
                            )
                        else:
                            budget_section += "• 省钱建议: 暂无\n"

                else:
                    # 旧结构：直接访问
                    budget_section += (
                        f"• 总预算: {budget_analysis.get('total_budget', 0):.0f} 元\n"
                    )
                    budget_section += (
                        f"• 每日预算: {budget_analysis.get('daily_budget', 0):.0f} 元\n"
                    )
                    budget_section += (
                        f"• 预算等级: {budget_analysis.get('budget_level', '未知')}\n"
                    )

                # 添加汇率信息
                if "exchange_rate" in budget_analysis:
                    budget_section += (
                        f"• 汇率信息: {budget_analysis['exchange_rate']}\n"
                    )

                response_content += budget_section

            # 添加时长规划信息（如果可用）
            duration_plan = state.get("duration_plan", {})
            if duration_plan and "duration_planning" in duration_plan:
                duration_info = duration_plan["duration_planning"]
                duration_section = f"\n\n⏰ **时长优化建议**\n"
                duration_section += f"• 建议天数: {duration_info.get('optimized_duration', '未知')} 天\n"
                duration_section += f"• 调整原因: {duration_info.get('reason', '无')}\n"
                duration_section += (
                    f"• 效率评分: {duration_info.get('efficiency_score', '未知')}/10\n"
                )

                # 移除重复的每日安排，只保留详细行程部分

                # 添加时间优化建议
                if "time_optimization" in duration_plan:
                    time_opt = duration_plan["time_optimization"]
                    if time_opt and isinstance(time_opt, dict):
                        morning = time_opt.get("morning_activities", ["无"])
                        afternoon = time_opt.get("afternoon_activities", ["无"])
                        evening = time_opt.get("evening_activities", ["无"])

                        morning_act = (
                            morning[0]
                            if morning and isinstance(morning, list)
                            else "无"
                        )
                        afternoon_act = (
                            afternoon[0]
                            if afternoon and isinstance(afternoon, list)
                            else "无"
                        )
                        evening_act = (
                            evening[0]
                            if evening and isinstance(evening, list)
                            else "无"
                        )

                        duration_section += f"• 时间安排: 上午{morning_act}, 下午{afternoon_act}, 晚上{evening_act}\n"
                    else:
                        duration_section += "• 时间安排: 待规划\n"

                response_content += duration_section

            # 添加详细每日行程（包含出行方式和住宿）
            if "daily_schedule" in duration_info:
                detailed_section = f"\n\n🗺️ **详细每日行程**\n"
                schedule = duration_info["daily_schedule"]

                for day, activity in list(schedule.items())[:6]:  # 显示前6天
                    if activity:
                        # 解析活动内容，提取城市和交通信息
                        city_info = await _extract_city_and_transport_from_activity(
                            activity
                        )

                        detailed_section += f"\n**第{day}天**:\n"
                        if city_info.get("from_city"):
                            detailed_section += f"• 🚄 出发: {city_info['from_city']} → {city_info['to_city']}\n"
                            detailed_section += f"• 🚗 交通: {city_info['transport']}\n"
                        else:
                            detailed_section += f"• 📍 活动: {activity}\n"

                        # 添加住宿建议
                        if city_info.get("to_city"):
                            detailed_section += f"• 🏨 住宿: {city_info['to_city']} ({city_info['hotel_type']})\n"
                        else:
                            detailed_section += f"• 🏨 住宿: 当地特色酒店\n"

                response_content += detailed_section
        else:
            response_content = "抱歉，无法生成旅行计划。"

    else:
        # 其他情况
        response_content = f"抱歉，处理过程中遇到问题。当前步骤: {current_step}"

    # 添加AI回复到消息列表
    state["messages"].append({"role": "assistant", "content": response_content})

    # 清理临时状态
    state.pop("parsed_message", None)
    state.pop("extracted_info", None)
    state.pop("current_step", None)

    logger.info("响应格式化完成")
    return state


# 辅助函数
async def _extract_travel_info_with_llm(message: str) -> Dict[str, Any]:
    """使用LLM智能提取旅行信息"""
    prompt = TRAVEL_EXTRACTION_PROMPT.format(message=message)

    try:
        # 调用LLM提取信息
        response = llm.invoke([HumanMessage(content=prompt)])
        response_content = response.content.strip()

        # 清理响应内容，提取JSON部分
        if response_content.startswith("```json"):
            response_content = response_content[7:]
        if response_content.endswith("```"):
            response_content = response_content[:-3]
        response_content = response_content.strip()

        # 解析JSON
        travel_info = json.loads(response_content)

        # 验证和清理数据
        travel_info = await _validate_and_clean_travel_info(travel_info)

        logger.info(f"LLM提取的旅行信息: {travel_info}")
        return travel_info

    except json.JSONDecodeError as e:
        logger.error(f"LLM返回的JSON格式错误: {e}")
        logger.error(f"LLM原始响应: {response_content}")
        # 如果LLM完全失败，使用智能默认值
        return await _get_smart_defaults()

    except Exception as e:
        logger.error(f"LLM提取旅行信息失败: {e}")
        # 如果LLM完全失败，使用智能默认值
        return await _get_smart_defaults()


async def _optimize_duration(
    destination: str, current_duration: int, daily_budget: float
) -> int:
    """智能优化行程时长"""
    # 直接返回原计划天数，不再调用LLM
    return current_duration


async def _get_duration_reason(
    destination: str, optimized_duration: int, daily_budget: float
) -> str:
    """生成时长优化原因"""
    # 直接返回默认说明，不再调用LLM
    return f"根据您的旅行需求，建议{optimized_duration}天行程"


def _optimize_travel_plan(travel_plan, budget_analysis: dict):
    """优化旅行计划"""
    # 这里可以添加更多的优化逻辑
    # 比如根据预算调整住宿等级、餐厅选择等
    return travel_plan


def _format_travel_plan_response(plan) -> str:
    """格式化旅行计划回复"""
    if not plan:
        return "抱歉，无法生成旅行计划。"

    response = f"""🎉 为您制定了详细的旅行计划！

📍 **目的地**: {plan.destination}
📅 **行程天数**: {plan.duration_days}天
💰 **总预算**: {plan.total_budget}元
👥 **人数**: {plan.people_count}人

📊 **预算分配**:
• 住宿: {plan.budget_breakdown.hotel:.0f}元 ({plan.budget_breakdown.hotel/plan.total_budget*100:.0f}%)
• 餐饮: {plan.budget_breakdown.restaurant:.0f}元 ({plan.budget_breakdown.restaurant/plan.total_budget*100:.0f}%)
• 景点: {plan.budget_breakdown.attractions:.0f}元 ({plan.budget_breakdown.attractions/plan.total_budget*100:.0f}%)
• 交通: {plan.budget_breakdown.transport:.0f}元 ({plan.budget_breakdown.transport/plan.total_budget*100:.0f}%)
• 其他: {plan.budget_breakdown.other:.0f}元 ({plan.budget_breakdown.other/plan.total_budget*100:.0f}%)

🚄 **交通建议**:
"""

    for transport in plan.transport_suggestions[:2]:
        if isinstance(transport, dict):
            # 处理新的数据结构
            transport_type = transport.get("type", "未知")
            duration = transport.get("duration", "未知")
            price_range = transport.get("price_range", "未知")
            recommendation = transport.get("recommendation", "")
        else:
            # 处理旧的数据结构
            transport_type = (
                getattr(transport, "transport_type", {}).value
                if hasattr(transport, "transport_type")
                else "未知"
            )
            duration = getattr(transport, "duration_hours", "未知")
            price_range = f"{getattr(transport, 'price', 0)}元"
            recommendation = ""

        response += f"• {transport_type}: {duration}, {price_range}"
        if recommendation:
            response += f" ({recommendation})"
        response += "\n"

        # 移除简单的每日行程，只保留详细的行程部分

    return response


async def _extract_city_and_transport_from_activity(activity: str) -> Dict[str, str]:
    """使用LLM智能提取城市和交通信息"""
    city_info = {
        "from_city": None,
        "to_city": None,
        "transport": "当地游览",
        "hotel_type": "当地特色酒店",
    }

    # 使用LLM智能解析活动内容
    prompt = ACTIVITY_PARSING_PROMPT.format(activity=activity)

    try:
        response = llm.invoke([HumanMessage(content=prompt)])
        response_content = response.content.strip()

        # 清理响应内容，提取JSON部分
        if response_content.startswith("```json"):
            response_content = response_content[7:]
        if response_content.endswith("```"):
            response_content = response_content[:-3]
        response_content = response_content.strip()

        # 解析JSON
        parsed_info = json.loads(response_content)

        # 更新城市信息
        city_info.update(parsed_info)

        logger.info(f"LLM解析活动信息: {parsed_info}")

    except Exception as e:
        logger.error(f"LLM解析活动信息失败: {e}")
        # 如果LLM完全失败，使用最基本的默认值
        city_info = {
            "from_city": None,
            "to_city": None,
            "transport": "当地游览",
            "hotel_type": "当地特色酒店",
        }

    return city_info


async def _get_smart_defaults() -> Dict[str, Any]:
    """使用LLM智能判断所有默认值"""
    import datetime

    current_date = datetime.datetime.now()

    prompt = SMART_DEFAULTS_PROMPT.format(
        current_date=current_date.strftime("%Y年%m月%d日"),
        current_month=current_date.month,
        current_week=current_date.strftime("%A"),
        is_weekend="否" if current_date.weekday() in [5, 6] else "是",
    )

    response = llm.invoke([HumanMessage(content=prompt)])
    response_content = response.content.strip()

    # 清理响应内容，提取JSON部分
    if response_content.startswith("```json"):
        response_content = response_content[7:]
    if response_content.endswith("```"):
        response_content = response_content[:-3]
    response_content = response_content.strip()

    # 解析JSON
    defaults = json.loads(response_content)

    logger.info(f"LLM智能默认值: {defaults}")
    return defaults


async def _enhance_info_with_tools(
    travel_info: Dict[str, Any], suggested_tools: List[str]
) -> Dict[str, Any]:
    """使用工具增强旅行信息"""
    enhanced_info = {}

    for tool in suggested_tools:
        try:
            if tool == "天气" and travel_info.get("destination"):
                from ..tools.weather import get_weather_info

                weather_info = await get_weather_info(travel_info["destination"])
                if weather_info:
                    enhanced_info["weather_info"] = weather_info
                    logger.info(f"天气信息增强完成: {weather_info[:50]}...")

            elif (
                tool == "汇率"
                and travel_info.get("currency")
                and travel_info["currency"] != "CNY"
            ):
                from ..tools.currency import get_exchange_rate

                exchange_rate = await get_exchange_rate(travel_info["currency"], "CNY")
                if exchange_rate:
                    enhanced_info["exchange_rate"] = exchange_rate
                    logger.info(f"汇率信息增强完成: {exchange_rate}")

            elif tool == "航班" and travel_info.get("destination"):
                # 这里可以集成航班工具
                enhanced_info["flight_info"] = "航班信息待集成"
                logger.info("航班信息增强完成")

        except Exception as e:
            logger.warning(f"工具 {tool} 增强失败: {e}")

    return enhanced_info


async def _find_potential_cities(message: str) -> List[str]:
    """使用LLM智能识别消息中的潜在城市名"""
    prompt = CITY_EXTRACTION_PROMPT.format(message=message)

    try:
        # 调用LLM识别城市
        response = llm.invoke([HumanMessage(content=prompt)])
        response_content = response.content.strip()

        # 解析响应，提取城市名
        cities = []
        for line in response_content.split("\n"):
            city = line.strip()
            if city:  # 过滤掉空行
                cities.append(city)

        logger.info(f"LLM识别的城市: {cities}")
        return cities

    except Exception as e:
        logger.error(f"LLM城市识别失败: {e}")
        # 如果LLM失败，返回空列表
        return []


async def _validate_and_clean_travel_info(
    travel_info: Dict[str, Any],
) -> Dict[str, Any]:
    """使用LLM智能验证和清理旅行信息"""
    cleaned_info = {}

    # 使用LLM智能验证和清理
    prompt = TRAVEL_VALIDATION_PROMPT.format(travel_info=travel_info)

    try:
        response = llm.invoke([HumanMessage(content=prompt)])
        response_content = response.content.strip()

        # 清理响应内容，提取JSON部分
        if response_content.startswith("```json"):
            response_content = response_content[7:]
        if response_content.endswith("```"):
            response_content = response_content[:-3]
        response_content = response_content.strip()

        # 解析JSON
        cleaned_info = json.loads(response_content)

        logger.info(f"LLM验证和清理完成: {cleaned_info}")

    except Exception as e:
        logger.warning(f"LLM验证和清理失败: {e}，使用简单规则")
        # 回退到简单规则
        cleaned_info = _fallback_validate_travel_info(travel_info)

        # 如果缺少默认值，使用LLM智能判断
    if not cleaned_info.get("duration_days") or not cleaned_info.get("people_count"):
        smart_defaults = await _get_smart_defaults()

        if not cleaned_info.get("duration_days"):
            cleaned_info["duration_days"] = smart_defaults["duration_days"]
            logger.info(f"使用LLM智能默认天数: {smart_defaults['duration_days']}")

        if not cleaned_info.get("people_count"):
            cleaned_info["people_count"] = smart_defaults["people_count"]
            logger.info(f"使用LLM智能默认人数: {smart_defaults['people_count']}")

    return cleaned_info


async def _fallback_validate_travel_info(travel_info: Dict[str, Any]) -> Dict[str, Any]:
    """简单的回退验证和清理"""
    # 直接返回基本信息，不再调用LLM
    cleaned_info = {
        "destination": travel_info.get("destination"),
        "duration_days": 3,  # 默认3天
        "budget": 8000,  # 默认8000元
        "currency": "CNY",  # 默认人民币
        "people_count": 2,  # 默认2人
    }

    logger.info(f"使用简单回退验证: {cleaned_info}")
    return cleaned_info


# ==================== 专业化智能节点 ====================


async def intent_classifier(state: Dict[str, Any]) -> Dict[str, Any]:
    """智能意图分类器 - 专业化的意图识别和分类"""
    messages = state["messages"]
    user_message = ""

    # 处理消息格式
    if isinstance(messages[-1], dict):
        user_message = messages[-1].get("content", "")
    else:
        user_message = messages[-1].content

    # 使用LLM进行专业化意图分类
    intent_prompt = INTENT_CLASSIFICATION_PROMPT.format(message=user_message)

    try:
        response = llm.invoke([HumanMessage(content=intent_prompt)])
        intent_analysis = json.loads(response.content.strip())

        # 更新状态
        state["intent_analysis"] = intent_analysis
        state["intent_type"] = intent_analysis.get("intent_type", "travel_planning")
        state["complexity_level"] = intent_analysis.get("complexity_level", "medium")
        state["current_step"] = "intent_classified"

        logger.info(f"专业化意图分类完成: {intent_analysis}")

    except Exception as e:
        logger.error(f"意图分类失败: {e}")
        # 回退到默认分类
        state["intent_type"] = "travel_planning"
        state["complexity_level"] = "medium"
        state["current_step"] = "intent_classified"

    return state


async def tool_orchestrator(state: Dict[str, Any]) -> Dict[str, Any]:
    """工具编排器 - 智能选择和编排专业工具"""
    intent_analysis = state.get("intent_analysis", {})
    extracted_info = state.get("extracted_info", {})

    # 根据意图和复杂度智能选择工具
    selected_tools = []

    if intent_analysis.get("requires_specialization", False):
        specialization_areas = intent_analysis.get("specialization_areas", [])

        for area in specialization_areas:
            if "weather" in area.lower():
                selected_tools.append("weather")
            if "currency" in area.lower():
                selected_tools.append("currency")
            if "transport" in area.lower():
                selected_tools.append("transport")
            if "accommodation" in area.lower():
                selected_tools.append("accommodation")
            if "attractions" in area.lower():
                selected_tools.append("attractions")

    # 执行工具调用
    tool_results = {}
    for tool in selected_tools:
        try:
            if tool == "weather" and extracted_info.get("destination"):
                from ..tools.weather import get_weather_info

                weather_info = await get_weather_info(extracted_info["destination"])
                if weather_info:
                    tool_results["weather"] = weather_info

            elif tool == "currency" and extracted_info.get("currency") != "CNY":
                from ..tools.currency import get_exchange_rate

                exchange_rate = await get_exchange_rate(
                    extracted_info["currency"], "CNY"
                )
                if exchange_rate:
                    tool_results["currency"] = exchange_rate

            elif tool == "transport":
                # 集成交通工具
                tool_results["transport"] = "交通信息已获取"

            elif tool == "accommodation":
                # 集成住宿工具
                tool_results["accommodation"] = "住宿信息已获取"

            elif tool == "attractions":
                # 集成景点工具
                tool_results["attractions"] = "景点信息已获取"

        except Exception as e:
            logger.warning(f"工具 {tool} 执行失败: {e}")
            tool_results[tool] = f"执行失败: {e}"

    # 更新状态
    state["active_tools"] = selected_tools
    state["tool_results"] = tool_results
    state["current_step"] = "tools_orchestrated"

    logger.info(f"工具编排完成: {selected_tools}, 结果: {tool_results}")
    return state


async def plan_validator(state: Dict[str, Any]) -> Dict[str, Any]:
    """计划验证器 - 专业化的计划质量验证"""
    travel_plan = state.get("travel_plan")
    extracted_info = state.get("extracted_info", {})

    if not travel_plan:
        state["error_type"] = "missing_plan"
        state["current_step"] = "validation_failed"
        return state

    # 使用LLM进行专业化验证
    validation_prompt = PLAN_VALIDATION_PROMPT.format(
        travel_plan=travel_plan, extracted_info=extracted_info
    )

    try:
        response = llm.invoke([HumanMessage(content=validation_prompt)])
        validation_result = json.loads(response.content.strip())

        # 更新状态
        state["plan_validation"] = validation_result
        state["current_step"] = "plan_validated"

        logger.info(
            f"计划验证完成: 评分 {validation_result.get('validation_score', 0)}"
        )

    except Exception as e:
        logger.error(f"计划验证失败: {e}")
        state["error_type"] = "validation_error"
        state["current_step"] = "validation_failed"

    return state


async def dynamic_planner(state: Dict[str, Any]) -> Dict[str, Any]:
    """动态规划器 - 根据反馈动态调整计划"""
    extracted_info = state.get("extracted_info", {})
    plan_validation = state.get("plan_validation", {})
    tool_results = state.get("tool_results", {})

    # 使用LLM进行动态规划
    planning_prompt = DYNAMIC_PLANNING_PROMPT.format(
        extracted_info=extracted_info,
        plan_validation=plan_validation,
        tool_results=tool_results,
    )

    try:
        response = llm.invoke([HumanMessage(content=planning_prompt)])
        dynamic_plan = json.loads(response.content.strip())

        # 更新状态
        state["dynamic_plan"] = dynamic_plan
        state["current_step"] = "dynamically_planned"

        logger.info(f"动态规划完成: {dynamic_plan}")

    except Exception as e:
        logger.error(f"动态规划失败: {e}")
        state["error_type"] = "planning_error"
        state["current_step"] = "planning_failed"

    return state


async def quality_assessor(state: Dict[str, Any]) -> Dict[str, Any]:
    """质量评估器 - 专业化的计划质量评估"""
    travel_plan = state.get("travel_plan")
    plan_validation = state.get("plan_validation", {})
    dynamic_plan = state.get("dynamic_plan")

    # 综合评估计划质量
    quality_score = 0.0

    if plan_validation:
        quality_score += plan_validation.get("validation_score", 0) * 0.6
        quality_score += plan_validation.get("feasibility_score", 0) * 0.3
        quality_score += plan_validation.get("cost_effectiveness", 0) * 0.1

    if dynamic_plan:
        quality_score += dynamic_plan.get("estimated_quality", 0) * 0.4

    # 标准化到0-10分
    quality_score = min(10.0, max(0.0, quality_score))

    # 更新状态
    state["plan_quality_score"] = quality_score
    state["current_step"] = "quality_assessed"

    logger.info(f"质量评估完成: {quality_score}/10")
    return state


async def error_recovery(state: Dict[str, Any]) -> Dict[str, Any]:
    """错误恢复器 - 智能错误处理和恢复"""
    error_type = state.get("error_type", "unknown")
    recovery_attempts = state.get("recovery_attempts", 0)

    # 增加恢复尝试次数
    state["recovery_attempts"] = recovery_attempts + 1

    # 根据错误类型智能恢复
    if error_type == "validation_error":
        state["next_steps"] = ["destination_validator"]
        state["should_continue"] = True
    elif error_type == "planning_error":
        state["next_steps"] = ["dynamic_planner"]
        state["should_continue"] = True
    elif error_type == "tool_error":
        state["next_steps"] = ["tool_orchestrator"]
        state["should_continue"] = True
    else:
        state["next_steps"] = ["response_formatter"]
        state["should_continue"] = False

    state["current_step"] = "error_recovered"

    logger.info(f"错误恢复完成: 类型={error_type}, 尝试次数={recovery_attempts + 1}")
    return state
