"""Travel Planning Data Provider - 旅行规划数据提供工具"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, date, timedelta

logger = logging.getLogger(__name__)


class TravelPlanningDataProvider:
    """旅行规划数据提供器 - 专注于提供数据，不包含业务逻辑"""

    def __init__(self):
        pass

    def get_destination_info(self, destination: str) -> Dict[str, Any]:
        """获取目的地基本信息"""
        try:
            # 这里可以集成真实的地理数据API
            # 目前返回基础信息
            return {
                "name": destination,
                "type": "city",
                "country": self._detect_country(destination),
                "timezone": self._get_timezone(destination),
                "best_season": self._get_best_season(destination),
                "language": self._get_language(destination),
                "currency": self._get_currency(destination),
                "safety_level": "一般",
                "cost_level": "中等",
            }
        except Exception as e:
            logger.error(f"获取目的地信息失败: {e}")
            return {"name": destination, "error": str(e)}

    def get_travel_seasons(self, destination: str) -> Dict[str, Any]:
        """获取目的地旅行季节信息"""
        try:
            # 这里可以集成真实的季节数据
            seasons = {
                "spring": {"months": [3, 4, 5], "description": "春季，气候宜人"},
                "summer": {"months": [6, 7, 8], "description": "夏季，适合户外活动"},
                "autumn": {"months": [9, 10, 11], "description": "秋季，景色优美"},
                "winter": {"months": [12, 1, 2], "description": "冬季，适合室内活动"},
            }

            return {
                "destination": destination,
                "seasons": seasons,
                "current_season": self._get_current_season(),
                "recommendation": self._get_season_recommendation(destination),
            }
        except Exception as e:
            logger.error(f"获取季节信息失败: {e}")
            return {"destination": destination, "error": str(e)}

    def get_budget_recommendations(
        self, destination: str, duration_days: int, people_count: int
    ) -> Dict[str, Any]:
        """获取预算建议数据"""
        try:
            # 基于目的地和行程提供预算建议
            base_costs = self._get_base_costs(destination)

            total_budget = {
                "low": base_costs["daily"] * duration_days * people_count * 0.8,
                "medium": base_costs["daily"] * duration_days * people_count,
                "high": base_costs["daily"] * duration_days * people_count * 1.5,
            }

            return {
                "destination": destination,
                "duration_days": duration_days,
                "people_count": people_count,
                "base_daily_cost": base_costs["daily"],
                "budget_recommendations": total_budget,
                "cost_breakdown": base_costs["breakdown"],
                "money_saving_tips": self._get_money_saving_tips(destination),
            }
        except Exception as e:
            logger.error(f"获取预算建议失败: {e}")
            return {"destination": destination, "error": str(e)}

    def get_transport_options(
        self, from_city: str, to_city: str
    ) -> List[Dict[str, Any]]:
        """获取交通选项数据"""
        try:
            # 这里可以集成真实的交通数据API
            transport_options = [
                {
                    "type": "飞机",
                    "duration": "2-4小时",
                    "price_range": "500-2000元",
                    "frequency": "每日多班",
                    "advantages": ["快速", "舒适"],
                    "disadvantages": ["价格较高", "需要提前预订"],
                },
                {
                    "type": "高铁",
                    "duration": "4-8小时",
                    "price_range": "200-800元",
                    "frequency": "每日多班",
                    "advantages": ["准时", "经济"],
                    "disadvantages": ["时间较长", "座位可能紧张"],
                },
                {
                    "type": "汽车",
                    "duration": "8-12小时",
                    "price_range": "100-300元",
                    "frequency": "每日多班",
                    "advantages": ["灵活", "经济"],
                    "disadvantages": ["时间最长", "舒适度较低"],
                },
            ]

            return {
                "from_city": from_city,
                "to_city": to_city,
                "options": transport_options,
                "recommendation": self._get_transport_recommendation(
                    from_city, to_city
                ),
            }
        except Exception as e:
            logger.error(f"获取交通选项失败: {e}")
            return {"from_city": from_city, "to_city": to_city, "error": str(e)}

    def get_attraction_categories(self, destination: str) -> List[Dict[str, Any]]:
        """获取景点分类数据"""
        try:
            categories = [
                {"name": "历史文化", "description": "历史遗迹、博物馆、古迹"},
                {"name": "自然风光", "description": "山川、湖泊、海滩、公园"},
                {"name": "城市景观", "description": "现代建筑、城市地标、广场"},
                {"name": "娱乐休闲", "description": "游乐园、电影院、购物中心"},
                {"name": "美食体验", "description": "特色餐厅、美食街、当地小吃"},
            ]

            return {
                "destination": destination,
                "categories": categories,
                "popular_attractions": self._get_popular_attractions(destination),
                "seasonal_recommendations": self._get_seasonal_attractions(destination),
            }
        except Exception as e:
            logger.error(f"获取景点分类失败: {e}")
            return {"destination": destination, "error": str(e)}

    # 私有辅助方法
    def _detect_country(self, destination: str) -> str:
        """检测目的地所属国家"""
        # 简单的国家检测逻辑
        if "摩洛哥" in destination:
            return "摩洛哥"
        elif "日本" in destination or "东京" in destination:
            return "日本"
        elif "美国" in destination or "纽约" in destination:
            return "美国"
        else:
            return "未知"

    def _get_timezone(self, destination: str) -> str:
        """获取目的地时区"""
        # 简单的时区映射
        timezone_map = {"摩洛哥": "UTC+0", "日本": "UTC+9", "美国": "UTC-5"}
        return timezone_map.get(self._detect_country(destination), "UTC+8")

    def _get_best_season(self, destination: str) -> str:
        """获取最佳旅行季节"""
        # 基于目的地的季节建议
        season_map = {
            "摩洛哥": "春秋季（3-5月，9-11月）",
            "日本": "春季（3-5月）和秋季（9-11月）",
            "美国": "春秋季（3-5月，9-11月）",
        }
        return season_map.get(self._detect_country(destination), "全年")

    def _get_language(self, destination: str) -> str:
        """获取目的地语言"""
        language_map = {"摩洛哥": "阿拉伯语、法语", "日本": "日语", "美国": "英语"}
        return language_map.get(self._detect_country(destination), "当地语言")

    def _get_currency(self, destination: str) -> str:
        """获取目的地货币"""
        currency_map = {"摩洛哥": "MAD", "日本": "JPY", "美国": "USD"}
        return currency_map.get(self._detect_country(destination), "CNY")

    def _get_current_season(self) -> str:
        """获取当前季节"""
        month = datetime.now().month
        if month in [3, 4, 5]:
            return "spring"
        elif month in [6, 7, 8]:
            return "summer"
        elif month in [9, 10, 11]:
            return "autumn"
        else:
            return "winter"

    def _get_season_recommendation(self, destination: str) -> str:
        """获取季节建议"""
        return f"建议在最佳季节前往{destination}，以获得最佳旅行体验"

    def _get_base_costs(self, destination: str) -> Dict[str, Any]:
        """获取基础成本数据"""
        cost_map = {
            "摩洛哥": {
                "daily": 800,
                "breakdown": {
                    "住宿": 300,
                    "餐饮": 200,
                    "交通": 150,
                    "景点": 100,
                    "其他": 50,
                },
            },
            "日本": {
                "daily": 1500,
                "breakdown": {
                    "住宿": 600,
                    "餐饮": 400,
                    "交通": 300,
                    "景点": 150,
                    "其他": 50,
                },
            },
            "美国": {
                "daily": 2000,
                "breakdown": {
                    "住宿": 800,
                    "餐饮": 500,
                    "交通": 400,
                    "景点": 200,
                    "其他": 100,
                },
            },
        }
        return cost_map.get(
            self._detect_country(destination),
            {
                "daily": 1000,
                "breakdown": {
                    "住宿": 400,
                    "餐饮": 250,
                    "交通": 200,
                    "景点": 100,
                    "其他": 50,
                },
            },
        )

    def _get_money_saving_tips(self, destination: str) -> List[str]:
        """获取省钱建议"""
        return [
            "选择经济型住宿",
            "尝试当地小吃",
            "使用公共交通",
            "提前预订门票",
            "避开旅游旺季",
        ]

    def _get_transport_recommendation(self, from_city: str, to_city: str) -> str:
        """获取交通建议"""
        return f"从{from_city}到{to_city}，建议根据时间和预算选择合适的交通方式"

    def _get_popular_attractions(self, destination: str) -> List[str]:
        """获取热门景点"""
        attraction_map = {
            "摩洛哥": ["马拉喀什老城", "菲斯古城", "撒哈拉沙漠", "卡萨布兰卡"],
            "日本": ["东京塔", "富士山", "京都古寺", "大阪城"],
            "美国": ["自由女神像", "白宫", "大峡谷", "时代广场"],
        }
        return attraction_map.get(self._detect_country(destination), ["当地特色景点"])

    def _get_seasonal_attractions(self, destination: str) -> Dict[str, str]:
        """获取季节性景点建议"""
        return {
            "春季": "樱花、郁金香等春季花卉",
            "夏季": "海滩、避暑胜地",
            "秋季": "红叶、秋收体验",
            "冬季": "滑雪、温泉、节日活动",
        }


# 全局实例
travel_planning_data_provider = TravelPlanningDataProvider()
