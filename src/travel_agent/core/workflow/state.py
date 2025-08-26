"""简化的状态类型定义"""

from typing import TypedDict, List, Dict, Any, Optional, Annotated
from ..models import TravelInfo


class TravelState(TypedDict):
    """旅行代理状态"""

    # 基础消息 - 只读字段，由系统管理
    messages: Annotated[List, "read_only"]

    # 用户输入
    user_input: str

    # 意图分析
    intent_analysis: Optional[Dict[str, Any]]

    # 旅行信息 - 使用强类型模型
    travel_info: Optional[TravelInfo]

    # 旅行计划
    travel_plan: Optional[Dict[str, Any]]

    # 预算分析
    budget_analysis: Optional[Dict[str, Any]]

    # 时长规划
    duration_plan: Optional[Dict[str, Any]]

    # 响应内容
    response: Optional[str]

    # 当前步骤
    current_step: Optional[str]
