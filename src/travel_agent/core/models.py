"""Travel Agent Data Models"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime, date
from enum import Enum


class TripStatus(Enum):
    """旅行状态枚举"""

    DRAFT = "draft"
    PLANNING = "planning"
    CONFIRMED = "confirmed"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class TransportType(Enum):
    """交通方式枚举"""

    HIGH_SPEED_RAIL = "高铁"
    AIRPLANE = "飞机"
    TRAIN = "火车"
    BUS = "大巴"
    CAR = "自驾"


class AttractionCategory(Enum):
    """景点类别枚举"""

    HISTORICAL = "历史文化"
    NATURAL = "自然风光"
    URBAN = "城市景观"
    MODERN = "现代建筑"
    ENTERTAINMENT = "娱乐休闲"
    SHOPPING = "购物中心"


class CuisineType(Enum):
    """菜系类型枚举"""

    CHINESE = "中餐"
    WESTERN = "西餐"
    JAPANESE = "日料"
    KOREAN = "韩料"
    THAI = "泰餐"
    LOCAL = "当地特色"


@dataclass
class Location:
    """位置信息"""

    city: str
    district: Optional[str] = None
    address: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None


@dataclass
class Hotel:
    """酒店信息"""

    id: str
    name: str
    location: Location
    price_per_night: float
    rating: float
    amenities: List[str] = field(default_factory=list)
    description: Optional[str] = None
    contact: Optional[str] = None
    website: Optional[str] = None


@dataclass
class Attraction:
    """景点信息"""

    id: str
    name: str
    location: Location
    category: AttractionCategory
    ticket_price: float
    duration_hours: float
    description: Optional[str] = None
    opening_hours: Optional[str] = None
    best_time: Optional[str] = None
    tips: Optional[str] = None


@dataclass
class Restaurant:
    """餐厅信息"""

    id: str
    name: str
    location: Location
    cuisine: CuisineType
    avg_price_per_person: float
    rating: float
    specialties: List[str] = field(default_factory=list)
    opening_hours: Optional[str] = None
    reservation_required: bool = False
    contact: Optional[str] = None


@dataclass
class TransportOption:
    """交通选项"""

    id: str
    from_city: str
    to_city: str
    transport_type: TransportType
    duration_hours: float
    price: float
    frequency: str
    departure_time: Optional[str] = None
    arrival_time: Optional[str] = None
    company: Optional[str] = None


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
    preferred_attraction_categories: List[AttractionCategory] = field(
        default_factory=list
    )
    preferred_cuisines: List[CuisineType] = field(default_factory=list)
    max_restaurant_price: Optional[float] = None
    hotel_rating_min: Optional[float] = None
    transport_preference: Optional[TransportType] = None
    special_requirements: List[str] = field(default_factory=list)


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
    status: TripStatus = TripStatus.DRAFT
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def update_status(self, new_status: TripStatus):
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
