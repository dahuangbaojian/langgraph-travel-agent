"""Travel Planner - 重构版"""

import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime, date, timedelta
import logging
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.travel_agent.core.models import (
    TravelPlan,
    TravelRequest,
    TravelPreferences,
    BudgetBreakdown,
    DailyItinerary,
)

# 数据管理器已移除，使用LLM + Tools方式
from src.travel_agent.config.settings import config

logger = logging.getLogger(__name__)


class TravelPlanner:
    """旅行规划器 - 重构版"""

    def __init__(self):
        pass  # 数据管理器已移除，使用LLM + Tools方式

    def create_travel_plan(self, request: TravelRequest) -> TravelPlan:
        """根据旅行请求创建完整的旅行计划"""
        try:
            # 验证请求
            if not request.is_complete():
                missing_fields = request.get_missing_fields()
                raise ValueError(f"旅行请求不完整，缺少: {', '.join(missing_fields)}")

            # 验证城市
            if not config.validate_city(request.destination):
                raise ValueError(f"不支持的目的地: {request.destination}")

            # 设置默认值
            self._set_defaults(request)

            # 创建偏好
            preferences = self._create_preferences(request)

            # 生成每日行程
            daily_itineraries = self._generate_daily_itineraries(request)

            # 计算预算分配
            budget_breakdown = self._calculate_budget_breakdown(request, preferences)

            # 生成交通建议
            transport_suggestions = self._generate_transport_suggestions(
                request, preferences
            )

            # 创建旅行计划
            plan = TravelPlan(
                id=str(uuid.uuid4()),
                destination=request.destination,
                start_date=request.start_date,
                end_date=request.end_date,
                duration_days=request.duration_days,
                total_budget=request.budget,
                people_count=request.people_count,
                preferences=preferences,
                budget_breakdown=budget_breakdown,
                daily_itineraries=daily_itineraries,
                transport_suggestions=transport_suggestions,
            )

            logger.info(f"成功创建旅行计划: {plan.id}")
            return plan

        except Exception as e:
            logger.error(f"创建旅行计划失败: {e}")
            raise

    def _set_defaults(self, request: TravelRequest):
        """设置默认值"""
        if not request.duration_days and request.start_date and request.end_date:
            request.duration_days = (request.end_date - request.start_date).days
        elif not request.duration_days:
            request.duration_days = 3

        if not request.start_date:
            request.start_date = date.today() + timedelta(days=7)

        if not request.end_date:
            request.end_date = request.start_date + timedelta(
                days=request.duration_days
            )

        if not request.budget:
            request.budget = 3000

        if not request.people_count:
            request.people_count = 2

    def _create_preferences(self, request: TravelRequest) -> TravelPreferences:
        """创建旅行偏好"""
        return TravelPreferences(
            origin_city=config.default_origin_city,
            preferred_attraction_categories=[
                AttractionCategory.HISTORICAL,
                AttractionCategory.URBAN,
            ],
            preferred_cuisines=[CuisineType.LOCAL],
            max_restaurant_price=request.budget
            / (request.duration_days * 3 * request.people_count),
            hotel_rating_min=4.0,
        )

    def _generate_daily_itineraries(
        self, request: TravelRequest
    ) -> List[DailyItinerary]:
        """生成每日行程"""
        itineraries = []

        # 获取景点和餐厅数据
        attractions = self.data_manager.search_attractions(request.destination)
        restaurants = self.data_manager.search_restaurants(request.destination)

        for day in range(request.duration_days):
            current_date = request.start_date + timedelta(days=day)

            # 选择每日景点和餐厅
            daily_attractions = self._select_daily_attractions(
                attractions, day, request
            )
            daily_restaurants = self._select_daily_restaurants(
                restaurants, day, request
            )

            itinerary = DailyItinerary(
                day=day + 1,
                date=current_date,
                morning={
                    "activity": daily_attractions[0] if daily_attractions else None,
                    "restaurant": daily_restaurants[0] if daily_restaurants else None,
                },
                afternoon={
                    "activity": (
                        daily_attractions[1] if len(daily_attractions) > 1 else None
                    ),
                    "restaurant": (
                        daily_restaurants[1] if len(daily_restaurants) > 1 else None
                    ),
                },
                evening={
                    "activity": (
                        daily_attractions[2] if len(daily_attractions) > 2 else None
                    ),
                    "restaurant": (
                        daily_restaurants[2] if len(daily_restaurants) > 2 else None
                    ),
                },
            )

            itineraries.append(itinerary)

        return itineraries

    def _select_daily_attractions(
        self, attractions: List, day: int, request: TravelRequest
    ) -> List:
        """选择每日景点"""
        if not attractions:
            return []

        # 根据天数分配景点类型
        if day == 0:  # 第一天：历史文化景点
            preferred_categories = [AttractionCategory.HISTORICAL]
        elif day == request.duration_days - 1:  # 最后一天：轻松景点
            preferred_categories = [
                AttractionCategory.ENTERTAINMENT,
                AttractionCategory.SHOPPING,
            ]
        else:  # 中间天：混合类型
            preferred_categories = [
                AttractionCategory.URBAN,
                AttractionCategory.NATURAL,
            ]

        # 按类别筛选
        selected = []
        for category in preferred_categories:
            category_attractions = [a for a in attractions if a.category == category]
            if category_attractions:
                # 按评分排序，选择评分最高的
                category_attractions.sort(key=lambda x: x.rating, reverse=True)
                selected.extend(category_attractions[:2])

        # 如果没有按类别选择到，选择评分最高的
        if not selected:
            attractions.sort(key=lambda x: x.rating, reverse=True)
            selected = attractions[:3]

        return selected[:3]  # 每天最多3个景点

    def _select_daily_restaurants(
        self, restaurants: List, day: int, request: TravelRequest
    ) -> List:
        """选择每日餐厅"""
        if not restaurants:
            return []

        # 根据天数分配餐厅类型
        if day == 0:  # 第一天：当地特色
            preferred_cuisines = [CuisineType.LOCAL]
        else:  # 其他天：多样化
            preferred_cuisines = [CuisineType.CHINESE, CuisineType.LOCAL]

        # 按菜系筛选
        filtered = []
        for cuisine in preferred_cuisines:
            cuisine_restaurants = [r for r in restaurants if r.cuisine == cuisine]
            if cuisine_restaurants:
                filtered.extend(cuisine_restaurants)

        # 如果没有按菜系选择到，选择所有餐厅
        if not filtered:
            filtered = restaurants

        # 按评分排序
        filtered.sort(key=lambda x: x.rating, reverse=True)

        return filtered[:3]  # 每天最多3个餐厅

    def _calculate_budget_breakdown(
        self, request: TravelRequest, preferences: TravelPreferences
    ) -> BudgetBreakdown:
        """计算预算分配"""
        total_budget = request.budget
        days = request.duration_days
        people_count = request.people_count

        # 获取城市信息
        city_info = self.data_manager.get_city_info(request.destination)

        # 按比例分配预算
        budget_breakdown = BudgetBreakdown()

        # 住宿预算
        budget_breakdown.hotel = total_budget * config.get_budget_ratio("hotel")

        # 餐饮预算
        budget_breakdown.restaurant = total_budget * config.get_budget_ratio(
            "restaurant"
        )

        # 景点预算
        budget_breakdown.attractions = total_budget * config.get_budget_ratio(
            "attractions"
        )

        # 交通预算
        budget_breakdown.transport = total_budget * config.get_budget_ratio("transport")

        # 其他费用
        budget_breakdown.other = total_budget * config.get_budget_ratio("other")

        # 验证预算是否合理
        if budget_breakdown.total > total_budget:
            # 按比例调整
            ratio = total_budget / budget_breakdown.total
            budget_breakdown.hotel *= ratio
            budget_breakdown.restaurant *= ratio
            budget_breakdown.attractions *= ratio
            budget_breakdown.transport *= ratio
            budget_breakdown.other *= ratio

        return budget_breakdown

    def _generate_transport_suggestions(
        self, request: TravelRequest, preferences: TravelPreferences
    ) -> List:
        """生成交通建议"""
        from_city = preferences.origin_city
        to_city = request.destination

        # 搜索交通选项
        transport_options = self.data_manager.search_transport(from_city, to_city)

        if not transport_options:
            # 如果没有找到交通数据，返回默认建议
            return [
                {
                    "type": "高铁",
                    "duration": "4-6小时",
                    "price_range": "300-800元",
                    "recommendation": "推荐高铁，舒适且准时",
                },
                {
                    "type": "飞机",
                    "duration": "1-2小时",
                    "price_range": "500-1500元",
                    "recommendation": "时间紧张时推荐飞机",
                },
            ]

        # 按价格排序
        transport_options.sort(key=lambda x: x.price)

        return transport_options[:3]  # 返回前3个选项

    def get_recommendations(
        self, city: str, budget: float, days: int
    ) -> Dict[str, Any]:
        """获取综合推荐"""
        try:
            hotels = self.data_manager.search_hotels(city, max_price=budget / days)
            attractions = self.data_manager.search_attractions(city)
            restaurants = self.data_manager.search_restaurants(
                city, max_price=budget / (days * 3)
            )

            return {
                "city": city,
                "recommended_hotels": hotels[:3],
                "must_see_attractions": attractions[:5],
                "local_restaurants": restaurants[:5],
                "budget_tips": self._generate_budget_tips(budget, days, city),
            }
        except Exception as e:
            logger.error(f"获取推荐失败: {e}")
            return {}

    def _generate_budget_tips(self, budget: float, days: int, city: str) -> List[str]:
        """生成预算建议"""
        tips = []
        daily_budget = budget / days

        if daily_budget < 200:
            tips.append("预算较低，建议选择经济型酒店和快餐")
            tips.append("可以寻找免费景点和公园")
            tips.append("使用公共交通，避免打车")
        elif daily_budget < 500:
            tips.append("中等预算，可以选择舒适型酒店和特色餐厅")
            tips.append("可以体验一些付费景点")
            tips.append("适当使用打车服务")
        else:
            tips.append("预算充足，可以选择高档酒店和精品餐厅")
            tips.append("可以体验更多特色活动和景点")
            tips.append("享受VIP服务和体验")

        return tips

    def optimize_plan(
        self, plan: TravelPlan, new_constraints: Dict[str, Any]
    ) -> TravelPlan:
        """优化旅行计划"""
        try:
            # 这里可以实现更复杂的优化逻辑
            # 比如根据新约束调整景点选择、餐厅选择等

            logger.info(f"优化旅行计划: {plan.id}")
            return plan

        except Exception as e:
            logger.error(f"优化旅行计划失败: {e}")
            raise


# 全局实例
travel_planner = TravelPlanner()
