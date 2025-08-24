"""景点和路线规划工具"""

import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class AttractionInfo:
    """景点信息"""

    name: str
    city: str
    category: str
    ticket_price: float
    currency: str
    duration_hours: float
    description: str
    rating: float


class PlacesTool:
    """景点和路线工具"""

    def __init__(self):
        self.attractions_db = self._init_attractions()

    def _init_attractions(self) -> Dict[str, List[AttractionInfo]]:
        """初始化景点数据库"""
        return {
            "北京": [
                AttractionInfo(
                    "故宫博物院",
                    "北京",
                    "历史文化",
                    60.0,
                    "CNY",
                    4.0,
                    "明清两代皇宫，世界文化遗产",
                    4.8,
                ),
                AttractionInfo(
                    "天安门广场",
                    "北京",
                    "城市景观",
                    0.0,
                    "CNY",
                    1.5,
                    "世界上最大的城市广场",
                    4.6,
                ),
                AttractionInfo(
                    "颐和园",
                    "北京",
                    "自然风光",
                    30.0,
                    "CNY",
                    3.0,
                    "中国古典园林，世界文化遗产",
                    4.7,
                ),
            ],
            "上海": [
                AttractionInfo(
                    "外滩",
                    "上海",
                    "城市景观",
                    0.0,
                    "CNY",
                    2.0,
                    "黄浦江畔的万国建筑博览群",
                    4.8,
                ),
                AttractionInfo(
                    "豫园",
                    "上海",
                    "历史文化",
                    45.0,
                    "CNY",
                    2.5,
                    "明代古典园林，江南园林代表",
                    4.5,
                ),
            ],
        }

    def search_attractions(self, city: str, **kwargs) -> List[AttractionInfo]:
        """搜索景点"""
        if city not in self.attractions_db:
            return []
        return self.attractions_db[city]


# 全局实例
places_tool = PlacesTool()


def search_attractions(city: str, **kwargs) -> List[Dict[str, Any]]:
    """搜索景点的便捷函数"""
    attractions = places_tool.search_attractions(city, **kwargs)
    return [attr.__dict__ for attr in attractions]
