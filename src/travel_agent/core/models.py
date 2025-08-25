"""Travel Agent Data Models - 精简版本"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime, date


@dataclass
class BudgetBreakdown:
    """预算分配"""

    hotel: float = 0.0
    restaurant: float = 0.0
    attractions: float = 0.0
    transport: float = 0.0
    other: float = 0.0

    @property
    def total(self) -> float:
        """总预算"""
        return sum(
            [self.hotel, self.restaurant, self.attractions, self.transport, self.other]
        )


@dataclass
class TravelPreferences:
    """旅行偏好"""

    origin_city: str
    preferred_attraction_categories: List[str] = field(default_factory=list)
    preferred_cuisines: List[str] = field(default_factory=list)
    max_restaurant_price: Optional[float] = None
    hotel_rating_min: Optional[float] = None
    transport_preference: Optional[str] = None
    special_requirements: List[str] = field(default_factory=list)


@dataclass
class DailyItinerary:
    """每日行程"""

    day: int
    date: date
    morning: Dict[str, Any] = field(default_factory=dict)
    afternoon: Dict[str, Any] = field(default_factory=dict)
    evening: Dict[str, Any] = field(default_factory=dict)
    notes: Optional[str] = None


@dataclass
class TransportOption:
    """交通选项"""

    id: str
    from_city: str
    to_city: str
    transport_type: str
    duration_hours: float
    price: float
    frequency: str
    departure_time: Optional[str] = None
    arrival_time: Optional[str] = None
    company: Optional[str] = None


@dataclass
class TravelPlan:
    """旅行计划"""

    id: str
    destination: str
    start_date: date
    end_date: date
    duration_days: int
    total_budget: float
    people_count: int
    preferences: TravelPreferences
    budget_breakdown: BudgetBreakdown
    daily_itineraries: List[DailyItinerary]
    transport_suggestions: List[TransportOption]
    status: str = "draft"
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def update_status(self, new_status: str):
        """更新状态"""
        self.status = new_status
        self.updated_at = datetime.now()

    def add_note(self, day: int, note: str):
        """添加备注"""
        for itinerary in self.daily_itineraries:
            if itinerary.day == day:
                itinerary.notes = note
                break

    def calculate_total_cost(self) -> float:
        """计算总成本"""
        return self.budget_breakdown.total

    def get_remaining_budget(self) -> float:
        """获取剩余预算"""
        return self.total_budget - self.calculate_total_cost()


@dataclass
class TravelRequest:
    """旅行请求"""

    destination: str
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    duration_days: Optional[int] = None
    budget: Optional[float] = None
    people_count: int = 1
    preferences: Optional[TravelPreferences] = None

    def is_complete(self) -> bool:
        """检查请求是否完整"""
        required_fields = ["destination"]
        return all(
            hasattr(self, field) and getattr(self, field) is not None
            for field in required_fields
        )

    def get_missing_fields(self) -> List[str]:
        """获取缺失的字段"""
        missing = []
        if not self.destination:
            missing.append("目的地")
        if not self.duration_days and not (self.start_date and self.end_date):
            missing.append("旅行天数")
        if not self.budget:
            missing.append("预算")
        if not self.people_count:
            missing.append("人数")
        return missing
