"""Travel Agent Graph - 重构版"""

from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from typing import TypedDict, List, Dict, Any
import logging
import re
from datetime import date
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.travel_agent.core.models import (
    TravelRequest,
    TravelPreferences,
    AttractionCategory,
    CuisineType,
)
from src.travel_agent.tools.planner import travel_planner
from src.travel_agent.config.settings import config

# 配置日志
logger = logging.getLogger(__name__)


# 定义旅行状态类型
class TravelAgentState(TypedDict):
    """旅行代理状态"""

    messages: List
    current_plan: Dict[str, Any]
    user_preferences: Dict[str, Any]
    extracted_info: Dict[str, Any]
    travel_request: TravelRequest


# 创建LLM
llm = ChatOpenAI(
    model=config.default_model,
    temperature=config.temperature,
    max_tokens=config.max_tokens,
)

# 旅行规划系统提示词
TRAVEL_SYSTEM_PROMPT = f"""你是一个专业的旅行规划师，专门帮助用户制定个性化的旅行计划。

你的能力包括：
1. 路线规划：根据用户需求设计最优旅行路线
2. 行程安排：制定详细的每日行程计划
3. 住宿推荐：根据预算和偏好推荐合适的酒店
4. 餐饮建议：推荐当地特色美食和餐厅
5. 预算管理：帮助用户控制旅行成本
6. 时间优化：合理安排时间，避免浪费

支持的城市：{', '.join(config.supported_cities)}

工作流程：
1. 了解用户需求（目的地、时间、预算、人数等）
2. 制定初步旅行计划
3. 根据用户反馈调整优化
4. 提供最终详细行程

当用户提供旅行需求时，请：
- 提取关键信息（目的地、时间、预算、人数等）
- 使用可用的旅行工具生成具体计划
- 提供详细的行程安排和预算分配
- 给出实用的旅行建议

请始终以专业、友好的态度为用户服务，确保旅行计划既实用又有趣。"""


def travel_agent(state: TravelAgentState):
    """旅行代理主函数"""
    messages = state["messages"]

    # 如果是第一条消息，添加系统提示
    if len(messages) == 1 and isinstance(messages[0], HumanMessage):
        messages.insert(0, SystemMessage(content=TRAVEL_SYSTEM_PROMPT))

    # 分析用户消息，提取旅行信息
    user_message = messages[-1].content if messages else ""
    extracted_info = _extract_travel_info(user_message)

    if extracted_info:
        state["extracted_info"] = extracted_info

        # 创建旅行请求
        travel_request = _create_travel_request(extracted_info)
        state["travel_request"] = travel_request

        # 如果信息完整，生成旅行计划
        if travel_request.is_complete():
            try:
                travel_plan = travel_planner.create_travel_plan(travel_request)
                state["current_plan"] = _plan_to_dict(travel_plan)

                # 生成详细的回复
                response_content = _format_travel_plan_response(travel_plan)
            except Exception as e:
                logger.error(f"生成旅行计划失败: {e}")
                response_content = (
                    f"抱歉，生成旅行计划时遇到问题：{str(e)}。请稍后重试。"
                )
        else:
            # 信息不完整，询问缺失信息
            response_content = _ask_for_missing_info(travel_request)
    else:
        # 没有提取到旅行信息，正常对话
        response = llm.invoke(messages)
        response_content = response.content

    # 更新状态
    state["messages"].append(AIMessage(content=response_content))

    return state


def _extract_travel_info(message: str) -> Dict[str, Any]:
    """从用户消息中提取旅行信息"""
    info = {}
    message_lower = message.lower()

    # 提取目的地
    for dest in config.supported_cities:
        if dest in message:
            info["destination"] = dest
            break

    # 提取时间信息
    if "天" in message or "日" in message:
        days_match = re.search(r"(\d+)天", message)
        if days_match:
            info["duration_days"] = int(days_match.group(1))

    # 提取预算信息
    budget_match = re.search(r"(\d+)元", message)
    if budget_match:
        info["budget"] = float(budget_match.group(1))

    # 提取人数
    people_match = re.search(r"(\d+)人", message)
    if people_match:
        info["people_count"] = int(people_match.group(1))

    # 提取偏好
    if "酒店" in message or "住宿" in message:
        info["preferences"] = info.get("preferences", {})
        info["preferences"]["hotel"] = True

    if "美食" in message or "餐厅" in message:
        info["preferences"] = info.get("preferences", {})
        info["preferences"]["food"] = True

    # 提取景点类别偏好
    attraction_categories = {
        "历史文化": AttractionCategory.HISTORICAL,
        "自然风光": AttractionCategory.NATURAL,
        "城市景观": AttractionCategory.URBAN,
        "现代建筑": AttractionCategory.MODERN,
        "娱乐休闲": AttractionCategory.ENTERTAINMENT,
        "购物中心": AttractionCategory.SHOPPING,
    }

    for category_name, category_enum in attraction_categories.items():
        if category_name in message:
            info["preferences"] = info.get("preferences", {})
            info["preferences"]["attraction_categories"] = info["preferences"].get(
                "attraction_categories", []
            )
            info["preferences"]["attraction_categories"].append(category_enum)

    # 提取菜系偏好
    cuisine_types = {
        "中餐": CuisineType.CHINESE,
        "西餐": CuisineType.WESTERN,
        "日料": CuisineType.JAPANESE,
        "韩料": CuisineType.KOREAN,
        "泰餐": CuisineType.THAI,
        "当地特色": CuisineType.LOCAL,
    }

    for cuisine_name, cuisine_enum in cuisine_types.items():
        if cuisine_name in message:
            info["preferences"] = info.get("preferences", {})
            info["preferences"]["cuisine_preferences"] = info["preferences"].get(
                "cuisine_preferences", []
            )
            info["preferences"]["cuisine_preferences"].append(cuisine_enum)

    return info


def _create_travel_request(extracted_info: Dict[str, Any]) -> TravelRequest:
    """创建旅行请求"""
    preferences = None
    if "preferences" in extracted_info:
        pref_data = extracted_info["preferences"]
        preferences = TravelPreferences(
            origin_city=config.default_origin_city,
            preferred_attraction_categories=pref_data.get("attraction_categories", []),
            preferred_cuisines=pref_data.get("cuisine_preferences", []),
            max_restaurant_price=(
                extracted_info.get("budget")
                / (extracted_info.get("duration_days", 3) * 3)
                if extracted_info.get("budget")
                else None
            ),
        )

    return TravelRequest(
        destination=extracted_info.get("destination", ""),
        duration_days=extracted_info.get("duration_days"),
        budget=extracted_info.get("budget"),
        people_count=extracted_info.get("people_count", 1),
        preferences=preferences,
    )


def _plan_to_dict(plan) -> Dict[str, Any]:
    """将旅行计划转换为字典"""
    return {
        "id": plan.id,
        "destination": plan.destination,
        "start_date": plan.start_date.isoformat() if plan.start_date else None,
        "end_date": plan.end_date.isoformat() if plan.end_date else None,
        "duration_days": plan.duration_days,
        "total_budget": plan.total_budget,
        "people_count": plan.people_count,
        "budget_breakdown": {
            "hotel": plan.budget_breakdown.hotel,
            "restaurant": plan.budget_breakdown.restaurant,
            "attractions": plan.budget_breakdown.attractions,
            "transport": plan.budget_breakdown.transport,
            "other": plan.budget_breakdown.other,
            "total": plan.budget_breakdown.total,
        },
        "daily_itineraries": [
            {
                "day": it.day,
                "date": it.date.isoformat() if it.date else None,
                "morning": it.morning,
                "afternoon": it.afternoon,
                "evening": it.evening,
                "notes": it.notes,
            }
            for it in plan.daily_itineraries
        ],
        "transport_suggestions": [
            {
                "type": t.transport_type.value,
                "duration": f"{t.duration_hours}小时",
                "price": t.price,
                "frequency": t.frequency,
                "company": t.company,
            }
            for t in plan.transport_suggestions
        ],
        "status": plan.status.value,
        "created_at": plan.created_at.isoformat() if plan.created_at else None,
    }


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
        response += f"• {transport.transport_type.value}: {transport.duration_hours}小时, {transport.price}元 ({transport.company})\n"

    response += "\n📋 **每日行程**:\n"

    for day_plan in plan.daily_itineraries[:3]:  # 只显示前3天
        response += f"\n第{day_plan.day}天 ({day_plan.date.strftime('%m-%d')}):\n"

        if day_plan.morning["activity"]:
            response += f"• 上午: {day_plan.morning['activity'].name} ({day_plan.morning['activity'].category.value})\n"
        if day_plan.morning["restaurant"]:
            response += f"• 午餐: {day_plan.morning['restaurant'].name} ({day_plan.morning['restaurant'].cuisine.value})\n"

        if day_plan.afternoon["activity"]:
            response += f"• 下午: {day_plan.afternoon['activity'].name} ({day_plan.afternoon['activity'].category.value})\n"
        if day_plan.afternoon["restaurant"]:
            response += f"• 晚餐: {day_plan.afternoon['restaurant'].name} ({day_plan.afternoon['restaurant'].cuisine.value})\n"

    response += (
        "\n💡 **温馨提示**: 这是初步计划，您可以根据实际情况调整。需要修改任何部分吗？"
    )

    return response


def _ask_for_missing_info(travel_request: TravelRequest) -> str:
    """询问缺失的旅行信息"""
    missing_fields = travel_request.get_missing_fields()

    if missing_fields:
        return f"为了给您制定更好的旅行计划，请告诉我：{', '.join(missing_fields)}。\n\n例如：我想去北京玩3天，预算5000元，2个人。"
    else:
        return "请告诉我您的具体旅行需求，比如目的地、时间、预算等。"


# 构建图
graph = StateGraph(TravelAgentState)
graph.add_node("travel_agent", travel_agent)
graph.add_edge("travel_agent", END)
graph.set_entry_point("travel_agent")

# 编译图
graph = graph.compile()
