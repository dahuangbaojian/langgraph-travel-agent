"""预算相关模型"""

from dataclasses import dataclass


@dataclass
class BudgetBreakdown:
    """预算分配"""

    hotel: float = 0.4  # 住宿40%
    restaurant: float = 0.25  # 餐饮25%
    attractions: float = 0.15  # 景点15%
    transport: float = 0.15  # 交通15%
    other: float = 0.05  # 其他5%
