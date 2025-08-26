"""预算相关模型"""

from dataclasses import dataclass


@dataclass
class BudgetBreakdown:
    hotel: float = 0.40  # 住宿40%
    transport: float = 0.25  # 交通25%
    attractions: float = 0.20  # 景点20%
    other: float = 0.15  # 其他15%
