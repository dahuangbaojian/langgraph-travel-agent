"""简化的核心节点模块 - 整合复杂业务逻辑"""

import json
import logging
from typing import Dict, Any, List, Optional
from langchain_core.messages import HumanMessage

from .utils import get_llm, _extract_travel_info_with_llm
from ..prompts.intent_analysis import INTENT_ANALYSIS_PROMPT
from ..prompts.budget_analysis import BUDGET_ANALYSIS_PROMPT
from ..prompts.duration_planning import DURATION_PLANNING_PROMPT
from ..prompts.route_generation import ROUTE_GENERATION_PROMPT
from ..models import TravelInfo, BudgetBreakdown

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


async def response_generator(state: Dict[str, Any]) -> Dict[str, Any]:
    """响应生成器 - 生成具体的旅行路线"""
    try:
        travel_plan = state.get("travel_plan", {})
        travel_info = state.get("travel_info", {})

        destination = travel_plan.get("destination", "旅行目的地")
        duration = travel_plan.get("duration", "未知")
        budget = travel_plan.get("budget", "未知")
        preferences = travel_info.preferences if travel_info else []

        # 生成具体的旅行路线
        route_content = _generate_travel_route(destination, duration, preferences)

        # 生成完整响应
        response_content = f"""🎯 **{destination}{duration}天最佳旅行路线**

{route_content}"""

        # 添加AI响应到状态
        state["messages"].append({"role": "assistant", "content": response_content})
        state["response"] = response_content
        state["current_step"] = "response_generated"

        logger.info("旅行路线生成完成")

    except Exception as e:
        logger.error(f"响应生成失败: {e}")
        # 生成错误响应
        error_response = (
            "抱歉，我在生成旅行路线时遇到了一些问题。请重新描述您的旅行需求。"
        )
        state["messages"].append({"role": "assistant", "content": error_response})
        state["response"] = error_response
        state["current_step"] = "response_generation_failed"

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

    # 使用BudgetBreakdown模型
    budget_breakdown = BudgetBreakdown(
        hotel=0.40,  # 住宿
        restaurant=0.25,  # 餐饮
        attractions=0.15,  # 景点
        transport=0.15,  # 交通
        other=0.05,  # 其他
    )

    return {
        "total_budget": budget,
        "daily_budget": budget // max(duration_days, 1),  # 防止除零错误
        "budget_breakdown": budget_breakdown.__dict__,  # 转换为字典
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
        logger.warning(f"LLM路线生成失败，使用基础模板: {e}")
        # 降级到基础模板
        return _generate_basic_route_template(destination, duration, preferences)


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

            # 验证输出格式 - 检查是否包含基本的表格结构
            if "|" in route_content:
                return route_content
            else:
                # 如果不是表格格式，尝试转换为表格格式
                logger.warning("LLM输出不是表格格式，尝试转换")
                return _convert_to_table_format(route_content, duration)
        else:
            raise Exception("LLM不可用")

    except Exception as e:
        logger.error(f"LLM路线生成失败: {e}")
        raise e


def _generate_basic_route_template(
    destination: str, duration: int, preferences: List[str]
) -> str:
    """生成基础路线模板（LLM失败时的降级方案）"""

    route_lines = []

    for day in range(1, duration + 1):
        if day == 1:
            day_title = f"**第{day}天：抵达探索**"
            morning = f"抵达{destination}，酒店入住，适应时差"
            afternoon = f"市中心地标游览，熟悉{destination}环境"
            evening = f"品尝{destination}当地特色晚餐，休息调整"
        elif day == duration:
            day_title = f"**第{day}天：告别之旅**"
            morning = f"游览{destination}最后的重要景点"
            afternoon = f"购买{destination}特色纪念品，告别晚餐"
            evening = f"整理行装，准备从{destination}返程"
        else:
            day_title = f"**第{day}天：深度体验**"
            morning = f"探索{destination}的标志性建筑和历史遗迹"
            afternoon = f"体验{destination}的当地文化和美食"
            evening = f"欣赏{destination}的夜景，体验夜生活"

        day_content = f"""{day_title}
• 上午：{morning}
• 下午：{afternoon}
• 晚上：{evening}"""

        route_lines.append(day_content)

    return "\n\n".join(route_lines)


def _convert_to_table_format(route_content: str, duration: int) -> str:
    """将非表格格式的路线转换为表格格式"""

    # 如果内容包含天数信息，尝试提取并转换
    if "第" in route_content and "天" in route_content:
        # 简单的转换逻辑
        table_lines = [
            "| 天数 | 日期 | 出发城市 → 到达城市 | 主要景点/活动 |",
            "|------|------|-------------------|---------------------------|",
        ]

        # 提取天数信息并转换为表格行
        for day in range(1, duration + 1):
            day_marker = f"第{day}天"
            if day_marker in route_content:
                # 提取该天的内容
                day_content = _extract_day_content(route_content, day)
                table_lines.append(f"| D{day} | {day_marker} | 待定 | {day_content} |")
            else:
                table_lines.append(f"| D{day} | 第{day}天 | 待定 | 待定 |")

        return "\n".join(table_lines)

    # 如果无法转换，返回基础表格模板
    return _generate_basic_table_template(duration)


def _extract_day_content(route_content: str, day: int) -> str:
    """提取指定天数的内容"""
    day_marker = f"第{day}天"
    try:
        # 简单的文本提取逻辑
        start_idx = route_content.find(day_marker)
        if start_idx != -1:
            # 找到下一个天数标记或结尾
            next_day = f"第{day + 1}天"
            end_idx = route_content.find(next_day, start_idx)
            if end_idx == -1:
                end_idx = len(route_content)

            day_content = route_content[start_idx:end_idx].strip()
            # 清理标记词
            day_content = day_content.replace(day_marker, "").replace("：", "").strip()
            return day_content if day_content else "待定"
    except:
        pass

    return "待定"


def _generate_basic_table_template(duration: int) -> str:
    """生成基础表格模板"""
    table_lines = [
        "| 天数 | 日期 | 出发城市 → 到达城市 | 主要景点/活动 |",
        "|------|------|-------------------|---------------------------|",
    ]

    for day in range(1, duration + 1):
        if day == 1:
            table_lines.append(
                f"| D{day} | 第{day}天 | 出发城市 → 出发城市市区 | 接机，酒店入住，市区游览 |"
            )
        elif day == duration:
            table_lines.append(
                f"| D{day} | 第{day}天 | 出发城市 → 出发城市机场 | 送机，结束行程 |"
            )
        else:
            table_lines.append(f"| D{day} | 第{day}天 | 待定 → 待定 | 待定 |")

    return "\n".join(table_lines)
