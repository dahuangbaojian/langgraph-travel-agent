"""酒店查询工具"""

import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class HotelInfo:
    """酒店信息"""
    name: str
    city: str
    district: str
    address: str
    price_per_night: float
    currency: str
    rating: float
    amenities: List[str]
    description: str
    hotel_type: str  # 经济型、商务型、豪华型、度假村等
    stars: int  # 星级
    available_rooms: int


class HotelSearchTool:
    """酒店搜索工具"""
    
    def __init__(self):
        self.hotel_database = self._init_hotel_database()
    
    def _init_hotel_database(self) -> Dict[str, List[HotelInfo]]:
        """初始化酒店数据库"""
        return {
            "北京": [
                HotelInfo(
                    "北京王府井希尔顿酒店",
                    "北京",
                    "东城区",
                    "北京市东城区王府井金鱼胡同8号",
                    1200.0,
                    "CNY",
                    4.6,
                    ["WiFi", "健身房", "游泳池", "餐厅", "商务中心"],
                    "位于王府井商业区，交通便利，设施完善",
                    "豪华型",
                    5,
                    15
                ),
                HotelInfo(
                    "北京如家酒店(天安门广场店)",
                    "北京",
                    "东城区",
                    "北京市东城区东华门大街",
                    300.0,
                    "CNY",
                    4.2,
                    ["WiFi", "24小时前台", "行李寄存"],
                    "经济实惠，位置优越",
                    "经济型",
                    2,
                    25
                )
            ],
            "上海": [
                HotelInfo(
                    "上海外滩华尔道夫酒店",
                    "上海",
                    "黄浦区",
                    "上海市黄浦区中山东一路2号",
                    2800.0,
                    "CNY",
                    4.8,
                    ["WiFi", "健身房", "游泳池", "餐厅", "SPA", "酒吧"],
                    "外滩地标建筑，奢华体验",
                    "豪华型",
                    5,
                    8
                )
            ]
        }
    
    def search_hotels(
        self,
        city: str,
        check_in: str,
        check_out: str,
        guests: int = 2,
        max_price: Optional[float] = None,
        min_rating: float = 0.0,
        hotel_type: Optional[str] = None
    ) -> List[HotelInfo]:
        """搜索酒店"""
        if city not in self.hotel_database:
            return []
        
        hotels = self.hotel_database[city]
        filtered_hotels = []
        
        for hotel in hotels:
            if max_price and hotel.price_per_night > max_price:
                continue
            if hotel.rating < min_rating:
                continue
            if hotel_type and hotel.hotel_type != hotel_type:
                continue
            if hotel.available_rooms < guests:
                continue
            
            filtered_hotels.append(hotel)
        
        # 按评分排序
        filtered_hotels.sort(key=lambda x: x.rating, reverse=True)
        return filtered_hotels
    
    def get_hotel_details(self, hotel_name: str, city: str) -> Optional[HotelInfo]:
        """获取酒店详细信息"""
        if city not in self.hotel_database:
            return None
        
        for hotel in self.hotel_database[city]:
            if hotel.name == hotel_name:
                return hotel
        return None
    
    def get_hotel_recommendations(
        self,
        city: str,
        budget: float,
        preferences: List[str] = None
    ) -> List[Dict[str, Any]]:
        """根据预算和偏好推荐酒店"""
        hotels = self.search_hotels(city, "2025-01-27", "2025-01-28", max_price=budget)
        
        recommendations = []
        for hotel in hotels:
            score = self._calculate_recommendation_score(hotel, budget, preferences or [])
            recommendations.append({
                "酒店": hotel.name,
                "价格": f"{hotel.price_per_night} {hotel.currency}",
                "评分": hotel.rating,
                "类型": hotel.hotel_type,
                "推荐指数": score,
                "设施": ", ".join(hotel.amenities[:3])  # 显示前3个设施
            })
        
        # 按推荐指数排序
        recommendations.sort(key=lambda x: x["推荐指数"], reverse=True)
        return recommendations[:5]  # 返回前5个推荐
    
    def _calculate_recommendation_score(
        self,
        hotel: HotelInfo,
        budget: float,
        preferences: List[str]
    ) -> float:
        """计算推荐指数"""
        score = 0.0
        
        # 价格评分 (价格越低分数越高)
        price_ratio = hotel.price_per_night / budget
        if price_ratio <= 0.7:
            score += 30  # 价格很优惠
        elif price_ratio <= 1.0:
            score += 20  # 价格合理
        else:
            score += 10  # 价格偏高
        
        # 评分
        score += hotel.rating * 10
        
        # 设施匹配
        if preferences:
            matched_amenities = sum(1 for pref in preferences if pref in hotel.amenities)
            score += matched_amenities * 5
        
        # 星级加分
        score += hotel.stars * 2
        
        return min(100, score)  # 最高100分


# 全局实例
hotel_tool = HotelSearchTool()


def search_hotels(city: str, check_in: str, check_out: str, **kwargs) -> List[Dict[str, Any]]:
    """搜索酒店的便捷函数"""
    hotels = hotel_tool.search_hotels(city, check_in, check_out, **kwargs)
    return [hotel.__dict__ for hotel in hotels]


def get_hotel_recommendations(city: str, budget: float, preferences: List[str] = None) -> List[Dict[str, Any]]:
    """获取酒店推荐的便捷函数"""
    return hotel_tool.get_hotel_recommendations(city, budget, preferences)
