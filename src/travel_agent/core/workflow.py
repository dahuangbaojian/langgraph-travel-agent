"""旅游规划工作流节点"""

import re
import json
import logging
from typing import Dict, Any, List
from langchain_core.messages import HumanMessage

from .prompts import (
    FALLBACK_TRAVEL_PROMPT,
    TRAVEL_PLAN_TIP,
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
    intent_prompt = f"""
你是一个智能旅行助手，请分析以下用户消息的意图和类型：

用户消息：{user_message}

请分析：
1. 用户的主要意图（旅行规划、咨询、修改等）
2. 消息的复杂度（简单查询、复杂规划等）
3. 是否需要调用外部工具（天气、汇率、航班等）
4. 建议的下一步处理方式

请用JSON格式回答：
{{
    "intent": "旅行规划/咨询/修改",
    "complexity": "简单/中等/复杂",
    "needs_tools": true/false,
    "suggested_tools": ["天气", "汇率", "航班"],
    "next_step": "extract_info/validate/plan"
}}
"""

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
        validation_prompt = f"""
你是一个地理专家，请验证和增强以下目的地信息：

目的地：{destination}

请分析：
1. 目的地是否有效（城市、国家、地区等）
2. 目的地的地理位置和特征
3. 建议的最佳旅行时间
4. 当地特色和注意事项

请用JSON格式回答：
{{
    "is_valid": true/false,
    "destination_type": "城市/国家/地区/岛屿",
    "geographic_info": "地理位置描述",
    "best_time": "最佳旅行时间",
    "local_features": ["特色1", "特色2"],
    "travel_tips": "旅行建议"
}}
"""

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
    budget_prompt = f"""
你是一个旅行预算专家，请分析以下旅行预算的合理性：

预算信息：
- 总预算：{budget} {currency}
- 旅行天数：{duration} 天
- 货币：{currency}

请分析：
1. 预算是否合理（考虑目的地、天数、人数等因素）
2. 建议的预算分配方案
3. 预算等级评估
4. 省钱建议

请用JSON格式回答：
{{
    "budget_analysis": {{
        "is_reasonable": true/false,
        "budget_level": "经济/中等/豪华",
        "daily_budget": 每日预算,
        "budget_rating": "1-10评分",
        "suggestions": ["建议1", "建议2"]
    }},
    "budget_allocation": {{
        "hotel": "住宿比例",
        "food": "餐饮比例",
        "transport": "交通比例",
        "attractions": "景点比例",
        "other": "其他比例"
    }}
}}
"""

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
        state["budget_analysis"] = {
            "total_budget": budget,
            "daily_budget": daily_budget,
            "budget_level": _get_budget_level(daily_budget),
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
    duration_prompt = f"""
你是一个旅行时长规划专家，请为以下旅行制定最优时长：

旅行信息：
- 目的地：{destination}
- 当前计划天数：{current_duration} 天
- 每日预算：{daily_budget} 元
- 目的地特征：{destination_validation.get('local_features', [])}
- 最佳旅行时间：{destination_validation.get('best_time', '未知')}

请分析：
1. 建议的最优旅行天数
2. 每天的活动安排建议
3. 时长调整的原因
4. 时间利用效率评估

请用JSON格式回答：
{{
    "duration_planning": {{
        "original_duration": {current_duration},
        "optimized_duration": 建议天数,
        "reason": "调整原因",
        "efficiency_score": "1-10评分",
        "daily_schedule": {{
            "day1": "第一天安排",
            "day2": "第二天安排",
            "day3": "第三天安排"
        }}
    }},
    "time_optimization": {{
        "morning_activities": ["建议的上午活动"],
        "afternoon_activities": ["建议的下午活动"],
        "evening_activities": ["建议的晚上活动"]
    }}
}}
"""

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
        optimized_duration = _optimize_duration(
            destination, current_duration, daily_budget
        )
        state["duration_plan"] = {
            "original_duration": current_duration,
            "optimized_duration": optimized_duration,
            "reason": _get_duration_reason(
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


async def fallback_handler(state: Dict[str, Any]) -> Dict[str, Any]:
    """备用处理器 - 处理无法提取旅行信息的情况"""
    user_message = state["parsed_message"]

    try:
        # 使用fallback prompt生成回复
        fallback_prompt = FALLBACK_TRAVEL_PROMPT.format(user_message=user_message)
        response = llm.invoke([HumanMessage(content=fallback_prompt)])
        response_content = response.content

        state["fallback_response"] = response_content
        state["current_step"] = "fallback_handled"

        logger.info("备用处理完成")

    except Exception as e:
        logger.error(f"备用处理失败: {e}")
        state["fallback_response"] = (
            f"收到您的旅行需求：{user_message}\n\n我正在为您规划完美的旅程，请稍候..."
        )
        state["current_step"] = "fallback_failed"

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

    elif current_step in ["fallback_handled", "fallback_failed"]:
        # 使用备用响应
        response_content = state.get("fallback_response", "抱歉，我无法理解您的需求。")

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
    prompt = f"""
你是一个专业的旅行信息提取助手。请从以下用户消息中提取旅行信息，并严格按照JSON格式输出。

要求：
1. 目的地：提取具体的城市、国家或地区名称
2. 天数：提取具体的旅行天数，如果没有明确提到，根据上下文推断（如"一周"=7天，"周末"=2天）
3. 预算：提取具体的预算金额和货币单位（如"5000欧元"、"2万日元"、"3000美元"）
4. 人数：提取具体的旅行人数
5. 货币：提取预算的货币单位，如果没有明确提到，默认为"CNY"（人民币）

请严格按照以下JSON格式输出，不要包含任何其他文字、解释或格式：

{{
    "destination": "提取到的目的地名称",
    "duration_days": 提取到的天数,
    "budget": 提取到的预算金额（数字）,
    "currency": "提取到的货币单位（如CNY、EUR、USD、JPY等）",
    "people_count": 提取到的人数
}}

用户消息：{message}

请直接输出JSON，不要有任何前缀或后缀：
"""

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
        # 如果LLM完全失败，使用最基本的默认值
        return {
            "destination": None,
            "duration_days": 4,
            "budget": 10000,
            "currency": "CNY",
            "people_count": 1,
        }

    except Exception as e:
        logger.error(f"LLM提取旅行信息失败: {e}")
        # 如果LLM完全失败，使用最基本的默认值
        return {
            "destination": None,
            "duration_days": 4,
            "budget": 10000,
            "currency": "CNY",
            "people_count": 1,
        }


def _optimize_duration(
    destination: str, current_duration: int, daily_budget: float
) -> int:
    """优化行程时长"""
    # 根据目的地类型和预算优化时长
    if "岛" in destination or "海" in destination:
        # 海岛游建议至少5天
        return max(current_duration, 5)
    elif "山" in destination or "自然" in destination:
        # 自然风光建议至少4天
        return max(current_duration, 4)
    elif daily_budget < 1000:
        # 经济型旅行，适当缩短时长
        return min(current_duration, 5)
    elif daily_budget > 5000:
        # 豪华型旅行，可以延长时长
        return current_duration + 2
    else:
        return current_duration


def _get_duration_reason(
    destination: str, optimized_duration: int, daily_budget: float
) -> str:
    """获取时长优化的原因"""
    if "岛" in destination or "海" in destination:
        return (
            f"{destination}是海岛/海滨城市，建议至少{optimized_duration}天才能充分体验"
        )
    elif "山" in destination or "自然" in destination:
        return f"{destination}有丰富的自然景观，建议{optimized_duration}天深度游览"
    elif daily_budget < 1000:
        return f"考虑到预算限制，建议{optimized_duration}天经济型旅行"
    elif daily_budget > 5000:
        return f"预算充足，建议{optimized_duration}天豪华深度游"
    else:
        return f"根据您的需求，建议{optimized_duration}天行程"


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

    response += f"\n{TRAVEL_PLAN_TIP}"

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
    prompt = f"""
你是一个旅行行程分析专家，请分析以下旅行活动描述，提取城市和交通信息：

活动描述：{activity}

请分析：
1. 是否涉及城市间移动
2. 出发城市和目的地城市
3. 交通方式
4. 建议的住宿类型

请用JSON格式回答：
{{
    "from_city": "出发城市（如果没有城市间移动，返回null）",
    "to_city": "目的地城市",
    "transport": "交通方式（高铁/飞机/汽车/当地游览等）",
    "hotel_type": "住宿类型（当地特色酒店/市中心酒店/景区附近酒店等）"
}}

请直接输出JSON，不要有任何解释：
"""

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


def _get_budget_level(daily_budget: float) -> str:
    """智能判断预算等级"""
    if daily_budget < 500:
        return "经济"
    elif daily_budget < 1500:
        return "中等"
    elif daily_budget < 5000:
        return "中高端"
    else:
        return "豪华"


async def _get_smart_defaults() -> Dict[str, Any]:
    """使用LLM智能判断所有默认值"""
    import datetime

    current_date = datetime.datetime.now()

    prompt = f"""
你是一个旅行规划专家，请根据当前时间和旅行特点，智能推荐默认的旅行参数。

当前信息：
- 当前日期：{current_date.strftime('%Y年%m月%d日')}
- 当前月份：{current_date.month}
- 当前星期：{current_date.strftime('%A')}
- 是否工作日：{'否' if current_date.weekday() in [5, 6] else '是'}

请考虑以下因素：
1. 时间特点（工作日通常单人短途、周末通常结伴中长途）
2. 季节特点（春季赏花、夏季避暑、秋季观景、冬季滑雪等）
3. 节假日安排
4. 旅行类型（商务、休闲、家庭等）
5. 目的地特点

请推荐合理的默认值，用JSON格式回答：
{{
    "duration_days": 默认旅行天数（1-14天）,
    "people_count": 默认旅行人数（1-6人）,
    "budget_level": "经济/中等/中高端/豪华",
    "reason": "推荐理由"
}}

请直接输出JSON，不要有任何解释：
"""

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
    prompt = f"""
你是一个专业的城市识别助手。请从以下用户消息中识别出所有可能的城市、国家或地区名称。

要求：
1. 只返回城市、国家或地区名称
2. 每个名称占一行
3. 不要包含任何解释、标点或其他文字
4. 如果消息中没有城市信息，返回空

用户消息：{message}

请直接输出城市名称，每行一个：
"""

    try:
        # 调用LLM识别城市
        response = llm.invoke([HumanMessage(content=prompt)])
        response_content = response.content.strip()

        # 解析响应，提取城市名
        cities = []
        for line in response_content.split("\n"):
            city = line.strip()
            if city and len(city) >= 2:  # 过滤掉空行和太短的名称
                cities.append(city)

        # 按长度排序，优先返回较长的城市名
        cities.sort(key=len, reverse=True)

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
    prompt = f"""
你是一个旅行信息验证专家，请验证和清理以下旅行信息：

原始信息：{travel_info}

请验证和清理：
1. 目的地：确保是有效的城市、国家或地区名称
2. 天数：将文本描述转换为具体天数（如"一周"→7天，"周末"→2天）
3. 预算：提取数字金额，处理"万"、"W"等单位
4. 人数：提取具体人数，处理"一家3口"等表达
5. 货币：确保货币代码有效

请用JSON格式回答，保持原有结构：
{{
    "destination": "清理后的目的地",
    "duration_days": 清理后的天数（数字）,
    "budget": 清理后的预算（数字）,
    "currency": "清理后的货币代码",
    "people_count": 清理后的人数（数字）
}}

请直接输出JSON，不要有任何解释：
"""

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
    """使用LLM进行回退验证和清理"""
    cleaned_info = {}

    # 使用LLM进行智能验证和清理
    prompt = f"""
你是一个旅行信息验证专家，请验证和清理以下旅行信息：

原始信息：{travel_info}

请验证和清理：
1. 目的地：确保是有效的城市、国家或地区名称
2. 天数：将文本描述转换为具体天数（如"一周"→7天，"周末"→2天）
3. 预算：提取数字金额，处理"万"、"W"等单位
4. 人数：提取具体人数，处理"一家3口"等表达
5. 货币：确保货币代码有效

请用JSON格式回答，保持原有结构：
{{
    "destination": "清理后的目的地",
    "duration_days": 清理后的天数（数字）,
    "budget": 清理后的预算（数字）,
    "currency": "清理后的货币代码",
    "people_count": 清理后的人数（数字）
}}

请直接输出JSON，不要有任何解释：
"""

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

        logger.info(f"LLM回退验证和清理完成: {cleaned_info}")

    except Exception as e:
        logger.error(f"LLM回退验证和清理失败: {e}")
        # 如果LLM完全失败，使用最基本的默认值
        cleaned_info = {
            "destination": travel_info.get("destination"),
            "duration_days": 4,
            "budget": 10000,
            "currency": "CNY",
            "people_count": 1,
        }

    return cleaned_info
