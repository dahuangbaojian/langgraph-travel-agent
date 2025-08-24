"""航班查询工具"""

import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class FlightInfo:
    """航班信息"""
    flight_number: str
    airline: str
    departure_city: str
    arrival_city: str
    departure_time: str
    arrival_time: str
    duration: str
    price: float
    currency: str
    stops: int
    aircraft: str
    cabin_class: str
    available_seats: int


class FlightSearchTool:
    """航班搜索工具"""
    
    def __init__(self):
        self.flight_database = self._init_flight_database()
    
    def _init_flight_database(self) -> Dict[str, List[FlightInfo]]:
        """初始化航班数据库"""
        return {
            "北京-上海": [
                FlightInfo("CA1234", "中国国航", "北京", "上海", "08:00", "10:30", "2小时30分", 800.0, "CNY", 0, "A330", "经济舱", 45),
                FlightInfo("MU5678", "东方航空", "北京", "上海", "10:00", "12:30", "2小时30分", 750.0, "CNY", 0, "B787", "经济舱", 32)
            ],
            "北京-东京": [
                FlightInfo("CA123", "中国国航", "北京", "东京", "09:00", "13:30", "4小时30分", 2800.0, "CNY", 0, "A330", "经济舱", 28)
            ]
        }
    
    def search_flights(self, departure: str, arrival: str, date: str, **kwargs) -> List[FlightInfo]:
        """搜索航班"""
        route_key = f"{departure}-{arrival}"
        if route_key in self.flight_database:
            return self.flight_database[route_key]
        return []
    
    def get_flight_details(self, flight_number: str) -> Optional[FlightInfo]:
        """获取航班详细信息"""
        for route_flights in self.flight_database.values():
            for flight in route_flights:
                if flight.flight_number == flight_number:
                    return flight
        return None
    
    def compare_prices(self, departure: str, arrival: str, date: str) -> Dict[str, Any]:
        """比较不同航空公司的价格"""
        flights = self.search_flights(departure, arrival, date)
        
        if not flights:
            return {"error": "未找到航班"}
        
        # 按航空公司分组
        airline_prices = {}
        for flight in flights:
            if flight.airline not in airline_prices:
                airline_prices[flight.airline] = []
            airline_prices[flight.airline].append(flight.price)
        
        # 计算每个航空公司的平均价格
        comparison = {}
        for airline, prices in airline_prices.items():
            comparison[airline] = {
                "最低价格": min(prices),
                "平均价格": sum(prices) / len(prices),
                "最高价格": max(prices),
                "航班数量": len(prices)
            }
        
        return comparison
    
    def get_route_suggestions(self, departure: str, budget: float) -> List[Dict[str, Any]]:
        """根据预算推荐航线"""
        suggestions = []
        
        for route, flights in self.flight_database.items():
            if departure in route:
                # 计算该航线的平均价格
                avg_price = sum(f.price for f in flights) / len(flights)
                
                if avg_price <= budget:
                    arrival = route.split("-")[1] if route.startswith(departure) else route.split("-")[0]
                    suggestions.append({
                        "目的地": arrival,
                        "平均价格": avg_price,
                        "可用航班": len(flights),
                        "推荐指数": self._calculate_recommendation_score(flights)
                    })
        
        # 按推荐指数排序
        suggestions.sort(key=lambda x: x["推荐指数"], reverse=True)
        return suggestions[:5]  # 返回前5个推荐
    
    def _calculate_recommendation_score(self, flights: List[FlightInfo]) -> float:
        """计算推荐指数"""
        if not flights:
            return 0.0
        
        # 基于价格、时长、准点率等因素计算
        avg_price = sum(f.price for f in flights) / len(flights)
        avg_duration = sum(self._parse_duration(f.duration) for f in flights) / len(flights)
        
        # 简单的推荐算法（可以优化）
        price_score = max(0, 100 - avg_price / 10)  # 价格越低分数越高
        duration_score = max(0, 100 - avg_duration / 60)  # 时长越短分数越高
        
        return (price_score + duration_score) / 2
    
    def _parse_duration(self, duration: str) -> int:
        """解析时长字符串为分钟数"""
        try:
            if "小时" in duration and "分" in duration:
                hours = int(duration.split("小时")[0])
                minutes = int(duration.split("小时")[1].split("分")[0])
                return hours * 60 + minutes
            elif "小时" in duration:
                hours = int(duration.split("小时")[0])
                return hours * 60
            elif "分" in duration:
                minutes = int(duration.split("分")[0])
                return minutes
            else:
                return 0
        except:
            return 0


# 全局实例
flight_tool = FlightSearchTool()


def search_flights(departure: str, arrival: str, date: str, **kwargs) -> List[Dict[str, Any]]:
    """搜索航班的便捷函数"""
    flights = flight_tool.search_flights(departure, arrival, date, **kwargs)
    return [flight.__dict__ for flight in flights]


def get_flight_price_comparison(departure: str, arrival: str, date: str) -> Dict[str, Any]:
    """获取航班价格比较"""
    return flight_tool.compare_prices(departure, arrival, date)


def get_route_recommendations(departure: str, budget: float) -> List[Dict[str, Any]]:
    """获取航线推荐"""
    return flight_tool.get_route_suggestions(departure, budget)
