"""简化的核心节点模块 - 整合复杂业务逻辑"""

import json
import logging
from typing import Dict, Any, List, Optional
from langchain_core.messages import HumanMessage

from ..llm_factory import get_llm
from ..prompts.intent_analysis import INTENT_ANALYSIS_PROMPT
from ..prompts.budget_analysis import BUDGET_ANALYSIS_PROMPT
from ..prompts.duration_planning import DURATION_PLANNING_PROMPT
from ..prompts.route_generation import ROUTE_GENERATION_PROMPT
from ..models import TravelInfo, BudgetBreakdown

logger = logging.getLogger(__name__)


async def _extract_travel_info_with_llm(user_message: str) -> Dict[str, Any]:
    """使用LLM智能提取旅行信息"""
    try:
        from ..prompts.travel_extraction import TRAVEL_EXTRACTION_PROMPT

        prompt = TRAVEL_EXTRACTION_PROMPT.format(message=user_message)

        llm = get_llm()
        if llm is None:
            raise Exception("LLM实例不可用")

        response = llm.invoke([HumanMessage(content=prompt)])
        travel_info = json.loads(response.content.strip())

        logger.info(f"LLM提取旅行信息: {travel_info}")
        return travel_info

    except Exception as e:
        logger.error(f"LLM提取旅行信息失败: {e}")
        # 使用TravelInfo模型的默认值
        from ..models import TravelInfo

        default_info = TravelInfo.create_default()
        return default_info.to_dict()


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
                # 根据用户消息内容智能推断
                intent_analysis = _generate_smart_intent_analysis()
        except Exception as e:
            logger.warning(f"意图分析失败，使用智能推断: {e}")
            intent_analysis = _generate_smart_intent_analysis()

            # 3. 旅行信息提取
        try:
            travel_info_dict = await _extract_travel_info_with_llm(user_message)
            travel_info = TravelInfo.from_dict(travel_info_dict)
        except Exception as e:
            logger.warning(f"旅行信息提取失败，使用默认值: {e}")
            # 使用TravelInfo模型的默认值
            travel_info = TravelInfo.create_default()

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
        state["intent_analysis"] = intent_analysis
        state["travel_info"] = TravelInfo.create_default()  # 添加这行！
        state["current_step"] = "message_processed"

    return state


async def travel_planner(state: Dict[str, Any]) -> Dict[str, Any]:
    """旅行规划核心逻辑 - 整合预算分析、时长规划等功能"""
    try:
        travel_info = state.get("travel_info", {})
        intent_analysis = state.get("intent_analysis", {})

        # 使用TravelInfo模型的属性
        destination = travel_info.destination
        duration_days = travel_info.duration_days
        budget = travel_info.budget
        people_count = travel_info.people_count

        logger.info(f"开始规划旅行: {destination}, {duration_days}天, {budget}元")

        # 1. 预算分析
        try:
            budget_prompt = BUDGET_ANALYSIS_PROMPT.format(
                destination=destination,
                budget_level=travel_info.budget_level,
                duration_days=duration_days,
                people_count=people_count,
            )

            llm = get_llm()
            if llm:
                response = llm.invoke([HumanMessage(content=budget_prompt)])
                budget_analysis = json.loads(response.content.strip())
            else:
                # 智能生成预算分配比例
                budget_analysis = _generate_smart_budget_analysis(
                    destination, budget, duration_days, people_count
                )
        except Exception as e:
            logger.warning(f"预算分析失败，使用智能生成: {e}")
            budget_analysis = _generate_smart_budget_analysis(
                destination, budget, duration_days, people_count
            )

        # 2. 时长规划
        try:
            duration_prompt = DURATION_PLANNING_PROMPT.format(
                destination=destination,
                budget=budget,
                preferences=", ".join(travel_info.preferences if travel_info else []),
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
                "daily_budget", budget // max(duration_days, 1)
            ),
            "budget_breakdown": budget_analysis.get("budget_breakdown", {}),
            "duration_reason": duration_plan.get(
                "reason", f"基于您的要求，建议{duration_days}天行程"
            ),
            "suggested_tools": (
                intent_analysis.get("suggested_tools", []) if intent_analysis else []
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
        # 使用智能生成的基本计划
        duration_days = travel_info.duration_days if travel_info else 3
        destination = travel_info.destination if travel_info else "未知目的地"
        budget = travel_info.budget if travel_info else 5000

        # 智能生成预算分配
        smart_budget = _generate_smart_budget_analysis(
            destination,
            budget,
            duration_days,
            travel_info.people_count if travel_info else 2,
        )

        state["travel_plan"] = {
            "destination": destination,
            "duration": duration_days,
            "budget": budget,
            "daily_budget": budget // max(duration_days, 1),
            "budget_breakdown": smart_budget.get("budget_breakdown", {}),
            "duration_reason": f"基于基本需求，建议{duration_days}天行程",
            "suggested_tools": ["航班", "酒店", "景点", "天气"],
            "next_step": "请告诉我您的具体需求",
        }
        state["current_step"] = "travel_planned"

    return state


async def route_generator(state: Dict[str, Any]) -> Dict[str, Any]:
    """路线生成器 - 生成具体的旅行路线"""
    try:
        travel_plan = state.get("travel_plan", {})
        travel_info = state.get("travel_info", {})

        destination = travel_plan.get("destination", "旅行目的地")
        duration = travel_plan.get("duration", "未知")
        preferences = travel_info.preferences if travel_info else []

        # 生成具体的旅行路线
        route_content = _generate_travel_route(destination, duration, preferences)

        # 将路线内容存储到状态中
        state["route_content"] = route_content
        state["current_step"] = "route_generated"

        logger.info("旅行路线生成完成")

    except Exception as e:
        logger.error(f"路线生成失败: {e}")
        # 生成错误响应
        error_response = (
            "抱歉，我在生成旅行路线时遇到了一些问题。请重新描述您的旅行需求。"
        )
        state["route_content"] = error_response
        state["current_step"] = "route_generation_failed"

    return state


async def response_generator(state: Dict[str, Any]) -> Dict[str, Any]:
    """响应生成器 - 专门负责格式化最终的旅行路线输出"""
    try:
        # 从状态中获取已生成的数据
        travel_plan = state.get("travel_plan", {})
        travel_info = state.get("travel_info", {})
        route_content = state.get("route_content", "")

        # 检查必要数据是否存在
        if not route_content:
            logger.error("路线内容未找到，无法生成响应")
            raise Exception("路线内容未生成")

        destination = travel_plan.get("destination", "旅行目的地")
        duration = travel_plan.get("duration", "未知")
        budget = travel_plan.get("budget", "未知")
        preferences = travel_info.preferences if travel_info else []

        # 专门负责格式化输出
        formatted_response = _format_travel_response(
            destination, duration, budget, preferences, route_content
        )

        # 添加AI响应到状态
        state["messages"].append({"role": "assistant", "content": formatted_response})
        state["response"] = formatted_response
        state["current_step"] = "response_generated"

        logger.info("旅行路线响应格式化完成")

    except Exception as e:
        logger.error(f"响应格式化失败: {e}")
        # 生成错误响应
        error_response = (
            "抱歉，我在格式化旅行路线时遇到了一些问题。请重新描述您的旅行需求。"
        )
        state["messages"].append({"role": "assistant", "content": error_response})
        state["response"] = error_response
        state["current_step"] = "response_formatting_failed"

    return state


def _generate_smart_intent_analysis() -> Dict[str, Any]:
    """生成意图分析（使用默认值）"""

    # 使用合理的默认值
    return {
        "intent": "旅行规划",
        "complexity": "中等",
        "suggested_tools": ["航班", "酒店", "景点", "天气"],
    }


def _generate_smart_budget_analysis(
    destination: str, budget: int, duration_days: int, people_count: int
) -> Dict[str, Any]:
    """生成预算分配分析（使用默认值）"""

    # 创建预算分析结果
    budget_result = BudgetBreakdown(
        hotel=0.40,  # 住宿
        transport=0.25,  # 交通
        attractions=0.20,  # 景点
        other=0.15,  # 其他
    )

    return {
        "total_budget": budget,
        "daily_budget": budget // max(duration_days, 1),  # 防止除零错误
        "budget_breakdown": budget_result.__dict__,  # 转换为字典
        "people_count": people_count,
        "duration_days": duration_days,
    }


def _generate_travel_route(
    destination: str, duration: int, preferences: List[str]
) -> str:
    """使用LLM生成智能旅行路线"""

    try:
        # 使用LLM生成路线
        route_content = _generate_llm_route(destination, duration, preferences)
        return route_content
    except Exception as e:
        logger.error(f"路线生成失败: {e}")
        # 返回错误信息，让用户知道需要重新生成
        return f"⚠️ 无法生成{destination}的{duration}天旅行路线，请重新尝试。"


def _generate_llm_route(destination: str, duration: int, preferences: List[str]) -> str:
    """使用LLM生成具体旅行路线"""

    # 构建路线生成提示词
    preferences_text = "、".join(preferences) if preferences else "无特殊偏好"

    prompt = ROUTE_GENERATION_PROMPT.format(
        destination=destination, duration=duration, preferences_text=preferences_text
    )

    logger.info(f"路线生成Prompt: {prompt}")

    try:
        llm = get_llm()
        if llm:
            from langchain_core.messages import HumanMessage

            response = llm.invoke([HumanMessage(content=prompt)])
            route_content = response.content.strip()

            logger.info(f"路线生成LLM原始返回: {route_content}")

            # 尝试解析JSON格式
            try:
                import json

                # 直接解析JSON，因为prompt已经要求返回纯JSON格式
                route_data = json.loads(route_content.strip())

                # 转换为Markdown格式
                markdown_content = _convert_json_to_markdown(route_data)
                logger.info("成功转换为Markdown格式")
                return markdown_content

            except json.JSONDecodeError as e:
                logger.error(f"LLM返回不是有效JSON格式: {e}")
                logger.error(f"原始内容: {route_content}")
                return f"⚠️ LLM返回的路线格式不正确，请重新尝试。\n\n错误详情：{e}"
            except Exception as e:
                logger.error(f"处理路线数据时出错: {e}")
                return f"⚠️ 处理路线数据时出错，请重新尝试。\n\n错误详情：{e}"
        else:
            raise Exception("LLM不可用")

    except Exception as e:
        logger.error(f"LLM路线生成失败: {e}")
        raise e


# 这个函数不再需要，已删除


def _convert_json_to_markdown(route_data: dict) -> str:
    """将JSON格式的路线数据转换为Markdown格式，使用Jinja2模板系统"""
    try:
        # 使用模板管理器
        from ...templates.manager import TemplateManager

        template_manager = TemplateManager()

        # 渲染模板
        markdown_content = template_manager.render_template(
            "unified_route_template.j2", format_level="full", **route_data  # 完整格式
        )

        if markdown_content is None:
            logger.error("模板渲染失败，使用备用系统")
            return _convert_json_to_markdown_fallback(route_data)

        # 清理多余的空行
        markdown_content = "\n".join(
            line for line in markdown_content.split("\n") if line.strip() or line == ""
        )

        return markdown_content

    except ImportError:
        logger.error("Jinja2未安装，使用备用模板系统")
        return _convert_json_to_markdown_fallback(route_data)
    except Exception as e:
        logger.error(f"Jinja2模板渲染失败: {e}")
        return _convert_json_to_markdown_fallback(route_data)


def _convert_json_to_markdown_fallback(route_data: dict) -> str:
    """备用模板系统（当主模板不可用时）"""
    try:
        # 创建模板管理器实例
        from ...templates.manager import TemplateManager

        template_manager = TemplateManager()

        # 使用简化格式
        markdown_content = template_manager.render_template(
            "unified_route_template.j2", format_level="simple", **route_data  # 简化格式
        )

        if markdown_content is None:
            logger.error("备用模板渲染失败")
            return f"⚠️ 路线数据转换失败，请重新尝试。"

        return markdown_content

    except Exception as e:
        logger.error(f"备用模板系统失败: {e}")
        return f"⚠️ 路线数据转换失败，请重新尝试。\n\n错误详情：{e}"


def _format_travel_response(
    destination: str,
    duration: str,
    budget: str,
    preferences: List[str],
    route_content: str,
) -> str:
    """格式化旅行响应输出"""

    try:
        # 使用模板管理器
        from ...templates.manager import TemplateManager

        template_manager = TemplateManager()

        # 准备模板数据
        template_data = {
            "destination": destination,
            "duration": duration,
            "budget": budget,
            "preferences": preferences,
            "route_content": route_content,
        }

        # 渲染响应模板
        formatted_response = template_manager.render_template(
            "unified_response_template.j2",
            format_level="full",  # 完整格式
            **template_data,
        )

        if formatted_response is None:
            logger.error("响应模板渲染失败，使用备用格式")
            return _format_travel_response_fallback(
                destination, duration, budget, preferences, route_content
            )

        return formatted_response

    except Exception as e:
        logger.error(f"响应模板渲染失败: {e}")
        return _format_travel_response_fallback(
            destination, duration, budget, preferences, route_content
        )


def _format_travel_response_fallback(
    destination: str,
    duration: str,
    budget: str,
    preferences: List[str],
    route_content: str,
) -> str:
    """响应格式化的备用方案"""

    try:
        # 使用备用响应模板
        from ...templates.manager import TemplateManager

        template_manager = TemplateManager()

        # 准备模板数据
        template_data = {
            "destination": destination,
            "duration": duration,
            "budget": budget,
            "preferences": preferences,
            "route_content": route_content,
        }

        # 渲染简化格式
        formatted_response = template_manager.render_template(
            "unified_response_template.j2",
            format_level="simple",  # 简化格式
            **template_data,
        )

        if formatted_response is None:
            logger.error("备用响应模板也失败了，使用最简单的字符串拼接")
            return _generate_simple_response(
                destination, duration, budget, preferences, route_content
            )

        return formatted_response

    except Exception as e:
        logger.error(f"备用响应模板失败: {e}")
        return _generate_simple_response(
            destination, duration, budget, preferences, route_content
        )


def _generate_simple_response(
    destination: str,
    duration: str,
    budget: str,
    preferences: List[str],
    route_content: str,
) -> str:
    """最简单的响应格式 - 最后的保障模板"""

    try:
        # 使用最简单响应模板
        from ...templates.manager import TemplateManager

        template_manager = TemplateManager()

        # 准备模板数据
        template_data = {
            "destination": destination,
            "duration": duration,
            "budget": budget,
            "preferences": preferences,
            "route_content": route_content,
        }

        # 渲染基础格式
        formatted_response = template_manager.render_template(
            "unified_response_template.j2",
            format_level="basic",  # 基础格式
            **template_data,
        )

        if formatted_response is None:
            logger.error("最简单响应模板也失败了，返回基础错误信息")
            return f"🎯 **{destination}{duration}天旅行路线**\n\n{route_content}\n\n⚠️ 格式化失败，但路线内容已生成"

        return formatted_response

    except Exception as e:
        logger.error(f"最简单响应模板失败: {e}")
        # 最后的保障 - 返回最基本的格式
        return f"🎯 **{destination}{duration}天旅行路线**\n\n{route_content}\n\n⚠️ 格式化失败，但路线内容已生成"
