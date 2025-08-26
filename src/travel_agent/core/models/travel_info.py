"""旅行信息模型"""

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class TravelInfo:
    """旅行信息模型"""

    # 目的地信息
    destination: str

    # 行程天数
    duration_days: int

    # 预算（元）
    budget: int

    # 人数
    people_count: int

    # 用户偏好
    preferences: List[str]

    # 预算等级（可选）
    budget_level: Optional[str] = None

    # 出发日期（可选）
    departure_date: Optional[str] = None

    # 返回日期（可选）
    return_date: Optional[str] = None

    # 交通方式（可选）
    transport_mode: Optional[str] = None

    # 住宿偏好（可选）
    accommodation_preference: Optional[str] = None

    # 特殊需求（可选）
    special_requirements: Optional[List[str]] = None

    def __post_init__(self):
        """设置默认值"""
        # 设置默认预算等级
        if not self.budget_level:
            if self.budget < 3000:
                self.budget_level = "经济"
            elif self.budget < 8000:
                self.budget_level = "中等"
            else:
                self.budget_level = "高端"

    @classmethod
    def from_dict(cls, data: dict) -> "TravelInfo":
        """从字典创建实例"""
        return cls(
            destination=data.get("destination") or "未知目的地",
            duration_days=max(data.get("duration_days", 0) or 0, 3),
            budget=max(data.get("budget", 0) or 0, 5000),
            people_count=max(data.get("people_count", 0) or 0, 2),
            preferences=data.get("preferences") or [],
            budget_level=data.get("budget_level"),
            departure_date=data.get("departure_date"),
            return_date=data.get("return_date"),
            transport_mode=data.get("transport_mode"),
            accommodation_preference=data.get("accommodation_preference"),
            special_requirements=data.get("special_requirements"),
        )

    @classmethod
    def create_default(cls) -> "TravelInfo":
        """创建默认实例"""
        return cls(
            destination="未知目的地",
            duration_days=3,
            budget=5000,
            people_count=2,
            preferences=[],
        )

    def to_dict(self) -> dict:
        """转换为字典格式"""
        return {
            "destination": self.destination,
            "duration_days": self.duration_days,
            "budget": self.budget,
            "people_count": self.people_count,
            "preferences": self.preferences,
            "budget_level": self.budget_level,
            "departure_date": self.departure_date,
            "return_date": self.return_date,
            "transport_mode": self.transport_mode,
            "accommodation_preference": self.accommodation_preference,
            "special_requirements": self.special_requirements,
        }
