"""Travel Data Manager - 重构版"""

import pandas as pd
import uuid
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime, date
import logging
import sys

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.travel_agent.core.models import (
    Hotel,
    Attraction,
    Restaurant,
    TransportOption,
    Location,
    AttractionCategory,
    CuisineType,
    TransportType,
)
from src.travel_agent.config.settings import config

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TravelDataManager:
    """旅行数据管理器 - 重构版"""

    def __init__(self):
        self.data_path = config.data_path
        self.data_path.mkdir(exist_ok=True)
        self._load_data()

    def _load_data(self):
        """加载所有数据"""
        try:
            self.hotels = self._load_hotels()
            self.attractions = self._load_attractions()
            self.restaurants = self._load_restaurants()
            self.transport = self._load_transport()
            logger.info("数据加载完成")
        except Exception as e:
            logger.error(f"数据加载失败: {e}")
            self._create_default_data()

    def _load_hotels(self) -> List[Hotel]:
        """加载酒店数据"""
        file_path = config.get_excel_path("hotels")
        if file_path.exists():
            try:
                df = pd.read_excel(file_path)
                return self._convert_hotels_df_to_models(df)
            except Exception as e:
                logger.error(f"加载酒店数据失败: {e}")
                return self._create_default_hotels()
        else:
            return self._create_default_hotels()

    def _load_attractions(self) -> List[Attraction]:
        """加载景点数据"""
        file_path = config.get_excel_path("attractions")
        if file_path.exists():
            try:
                df = pd.read_excel(file_path)
                return self._convert_attractions_df_to_models(df)
            except Exception as e:
                logger.error(f"加载景点数据失败: {e}")
                return self._create_default_attractions()
        else:
            return self._create_default_attractions()

    def _load_restaurants(self) -> List[Restaurant]:
        """加载餐厅数据"""
        file_path = config.get_excel_path("restaurants")
        if file_path.exists():
            try:
                df = pd.read_excel(file_path)
                return self._convert_restaurants_df_to_models(df)
            except Exception as e:
                logger.error(f"加载餐厅数据失败: {e}")
                return self._create_default_restaurants()
        else:
            return self._create_default_restaurants()

    def _load_transport(self) -> List[TransportOption]:
        """加载交通数据"""
        file_path = config.get_excel_path("transport")
        if file_path.exists():
            try:
                df = pd.read_excel(file_path)
                return self._convert_transport_df_to_models(df)
            except Exception as e:
                logger.error(f"加载交通数据失败: {e}")
                return self._create_default_transport()
        else:
            return self._create_default_transport()

    def _convert_hotels_df_to_models(self, df: pd.DataFrame) -> List[Hotel]:
        """将DataFrame转换为Hotel模型列表"""
        hotels = []
        for _, row in df.iterrows():
            try:
                location = Location(
                    city=row["city"],
                    district=row.get("district"),
                    address=row.get("address"),
                )

                hotel = Hotel(
                    id=str(uuid.uuid4()),
                    name=row["name"],
                    location=location,
                    price_per_night=float(row["price_per_night"]),
                    rating=float(row["rating"]),
                    amenities=(
                        row.get("amenities", "").split(",")
                        if pd.notna(row.get("amenities"))
                        else []
                    ),
                    description=row.get("description"),
                    contact=row.get("contact"),
                    website=row.get("website"),
                )
                hotels.append(hotel)
            except Exception as e:
                logger.warning(f"转换酒店数据失败: {e}")
                continue

        return hotels

    def _convert_attractions_df_to_models(self, df: pd.DataFrame) -> List[Attraction]:
        """将DataFrame转换为Attraction模型列表"""
        attractions = []
        for _, row in df.iterrows():
            try:
                location = Location(
                    city=row["city"],
                    district=row.get("district"),
                    address=row.get("address"),
                )

                # 解析景点类别
                category_str = row.get("category", "城市景观")
                category = self._parse_attraction_category(category_str)

                attraction = Attraction(
                    id=str(uuid.uuid4()),
                    name=row["name"],
                    location=location,
                    category=category,
                    ticket_price=float(row["ticket_price"]),
                    duration_hours=float(row["duration_hours"]),
                    description=row.get("description"),
                    opening_hours=row.get("opening_hours"),
                    best_time=row.get("best_time"),
                    tips=row.get("tips"),
                )
                attractions.append(attraction)
            except Exception as e:
                logger.warning(f"转换景点数据失败: {e}")
                continue

        return attractions

    def _convert_restaurants_df_to_models(self, df: pd.DataFrame) -> List[Restaurant]:
        """将DataFrame转换为Restaurant模型列表"""
        restaurants = []
        for _, row in df.iterrows():
            try:
                location = Location(
                    city=row["city"],
                    district=row.get("district"),
                    address=row.get("address"),
                )

                # 解析菜系类型
                cuisine_str = row.get("cuisine", "当地特色")
                cuisine = self._parse_cuisine_type(cuisine_str)

                restaurant = Restaurant(
                    id=str(uuid.uuid4()),
                    name=row["name"],
                    location=location,
                    cuisine=cuisine,
                    avg_price_per_person=float(row["avg_price_per_person"]),
                    rating=float(row["rating"]),
                    specialties=(
                        row.get("specialties", "").split(",")
                        if pd.notna(row.get("specialties"))
                        else []
                    ),
                    opening_hours=row.get("opening_hours"),
                    reservation_required=row.get("reservation_required", False),
                    contact=row.get("contact"),
                )
                restaurants.append(restaurant)
            except Exception as e:
                logger.warning(f"转换餐厅数据失败: {e}")
                continue

        return restaurants

    def _convert_transport_df_to_models(
        self, df: pd.DataFrame
    ) -> List[TransportOption]:
        """将DataFrame转换为TransportOption模型列表"""
        transport_options = []
        for _, row in df.iterrows():
            try:
                # 解析交通方式
                transport_str = row.get("transport_type", "高铁")
                transport_type = self._parse_transport_type(transport_str)

                transport = TransportOption(
                    id=str(uuid.uuid4()),
                    from_city=row["from_city"],
                    to_city=row["to_city"],
                    transport_type=transport_type,
                    duration_hours=float(row["duration_hours"]),
                    price=float(row["price"]),
                    frequency=row.get("frequency", "未知"),
                    departure_time=row.get("departure_time"),
                    arrival_time=row.get("arrival_time"),
                    company=row.get("company"),
                )
                transport_options.append(transport)
            except Exception as e:
                logger.warning(f"转换交通数据失败: {e}")
                continue

        return transport_options

    def _parse_attraction_category(self, category_str: str) -> AttractionCategory:
        """解析景点类别"""
        category_map = {
            "历史文化": AttractionCategory.HISTORICAL,
            "自然风光": AttractionCategory.NATURAL,
            "城市景观": AttractionCategory.URBAN,
            "现代建筑": AttractionCategory.MODERN,
            "娱乐休闲": AttractionCategory.ENTERTAINMENT,
            "购物中心": AttractionCategory.SHOPPING,
        }
        return category_map.get(category_str, AttractionCategory.URBAN)

    def _parse_cuisine_type(self, cuisine_str: str) -> CuisineType:
        """解析菜系类型"""
        cuisine_map = {
            "中餐": CuisineType.CHINESE,
            "西餐": CuisineType.WESTERN,
            "日料": CuisineType.JAPANESE,
            "韩料": CuisineType.KOREAN,
            "泰餐": CuisineType.THAI,
            "当地特色": CuisineType.LOCAL,
        }
        return cuisine_map.get(cuisine_str, CuisineType.LOCAL)

    def _parse_transport_type(self, transport_str: str) -> TransportType:
        """解析交通方式"""
        transport_map = {
            "高铁": TransportType.HIGH_SPEED_RAIL,
            "飞机": TransportType.AIRPLANE,
            "火车": TransportType.TRAIN,
            "大巴": TransportType.BUS,
            "自驾": TransportType.CAR,
        }
        return transport_map.get(transport_str, TransportType.HIGH_SPEED_RAIL)

    def _create_default_data(self):
        """创建默认数据"""
        logger.info("创建默认数据...")
        self.hotels = self._create_default_hotels()
        self.attractions = self._create_default_attractions()
        self.restaurants = self._create_default_restaurants()
        self.transport = self._create_default_transport()
        self._save_all_data()

    def _create_default_hotels(self) -> List[Hotel]:
        """创建默认酒店数据"""
        hotels = []
        default_data = [
            {
                "name": "北京王府井希尔顿酒店",
                "city": "北京",
                "district": "东城区",
                "address": "北京市东城区王府井金鱼胡同8号",
                "price_per_night": 800,
                "rating": 4.6,
                "amenities": ["WiFi", "健身房", "游泳池", "餐厅", "商务中心"],
                "description": "位于王府井商业区，交通便利",
            },
            {
                "name": "上海外滩华尔道夫酒店",
                "city": "上海",
                "district": "黄浦区",
                "address": "上海市黄浦区中山东一路2号",
                "price_per_night": 1200,
                "rating": 4.8,
                "amenities": ["WiFi", "健身房", "游泳池", "餐厅", "SPA"],
                "description": "外滩地标建筑，江景房视野绝佳",
            },
        ]

        for data in default_data:
            location = Location(
                city=data["city"], district=data["district"], address=data["address"]
            )

            hotel = Hotel(
                id=str(uuid.uuid4()),
                name=data["name"],
                location=location,
                price_per_night=data["price_per_night"],
                rating=data["rating"],
                amenities=data["amenities"],
                description=data["description"],
            )
            hotels.append(hotel)

        return hotels

    def _create_default_attractions(self) -> List[Attraction]:
        """创建默认景点数据"""
        attractions = []
        default_data = [
            {
                "name": "故宫博物院",
                "city": "北京",
                "district": "东城区",
                "category": AttractionCategory.HISTORICAL,
                "ticket_price": 60,
                "duration_hours": 4,
                "description": "明清两代皇宫，世界文化遗产",
                "opening_hours": "8:30-17:00",
                "best_time": "春秋季节",
                "tips": "建议提前预约，避开节假日",
            },
            {
                "name": "外滩",
                "city": "上海",
                "district": "黄浦区",
                "category": AttractionCategory.URBAN,
                "ticket_price": 0,
                "duration_hours": 2,
                "description": "黄浦江畔景观，万国建筑博览",
                "opening_hours": "全天开放",
                "best_time": "傍晚和夜晚",
                "tips": "建议傍晚前往，可以看日落和夜景",
            },
        ]

        for data in default_data:
            location = Location(city=data["city"], district=data["district"])

            attraction = Attraction(
                id=str(uuid.uuid4()),
                name=data["name"],
                location=location,
                category=data["category"],
                ticket_price=data["ticket_price"],
                duration_hours=data["duration_hours"],
                description=data["description"],
                opening_hours=data["opening_hours"],
                best_time=data["best_time"],
                tips=data["tips"],
            )
            attractions.append(attraction)

        return attractions

    def _create_default_restaurants(self) -> List[Restaurant]:
        """创建默认餐厅数据"""
        restaurants = []
        default_data = [
            {
                "name": "全聚德烤鸭店",
                "city": "北京",
                "district": "东城区",
                "cuisine": CuisineType.CHINESE,
                "avg_price_per_person": 150,
                "rating": 4.5,
                "specialties": ["北京烤鸭", "炸酱面", "宫保鸡丁"],
                "opening_hours": "10:00-22:00",
                "reservation_required": True,
            },
            {
                "name": "南翔小笼包",
                "city": "上海",
                "district": "黄浦区",
                "cuisine": CuisineType.LOCAL,
                "avg_price_per_person": 80,
                "rating": 4.3,
                "specialties": ["小笼包", "生煎包", "蟹粉包"],
                "opening_hours": "7:00-21:00",
                "reservation_required": False,
            },
        ]

        for data in default_data:
            location = Location(city=data["city"], district=data["district"])

            restaurant = Restaurant(
                id=str(uuid.uuid4()),
                name=data["name"],
                location=location,
                cuisine=data["cuisine"],
                avg_price_per_person=data["avg_price_per_person"],
                rating=data["rating"],
                specialties=data["specialties"],
                opening_hours=data["opening_hours"],
                reservation_required=data["reservation_required"],
            )
            restaurants.append(restaurant)

        return restaurants

    def _create_default_transport(self) -> List[TransportOption]:
        """创建默认交通数据"""
        transport_options = []
        default_data = [
            {
                "from_city": "北京",
                "to_city": "上海",
                "transport_type": TransportType.HIGH_SPEED_RAIL,
                "duration_hours": 4.5,
                "price": 553,
                "frequency": "每小时一班",
                "company": "中国铁路",
            },
            {
                "from_city": "北京",
                "to_city": "上海",
                "transport_type": TransportType.AIRPLANE,
                "duration_hours": 2,
                "price": 800,
                "frequency": "每天20班",
                "company": "国航/东航/南航",
            },
        ]

        for data in default_data:
            transport = TransportOption(
                id=str(uuid.uuid4()),
                from_city=data["from_city"],
                to_city=data["to_city"],
                transport_type=data["transport_type"],
                duration_hours=data["duration_hours"],
                price=data["price"],
                frequency=data["frequency"],
                company=data["company"],
            )
            transport_options.append(transport)

        return transport_options

    def _save_all_data(self):
        """保存所有数据到Excel"""
        try:
            self._save_hotels()
            self._save_attractions()
            self._save_restaurants()
            self._save_transport()
            logger.info("所有数据保存完成")
        except Exception as e:
            logger.error(f"保存数据失败: {e}")

    def _save_hotels(self):
        """保存酒店数据"""
        data = []
        for hotel in self.hotels:
            data.append(
                {
                    "name": hotel.name,
                    "city": hotel.location.city,
                    "district": hotel.location.district,
                    "address": hotel.location.address,
                    "price_per_night": hotel.price_per_night,
                    "rating": hotel.rating,
                    "amenities": ",".join(hotel.amenities),
                    "description": hotel.description,
                    "contact": hotel.contact,
                    "website": hotel.website,
                }
            )

        df = pd.DataFrame(data)
        file_path = config.get_excel_path("hotels")
        df.to_excel(file_path, index=False)
        logger.info(f"酒店数据已保存到: {file_path}")

    def _save_attractions(self):
        """保存景点数据"""
        data = []
        for attraction in self.attractions:
            data.append(
                {
                    "name": attraction.name,
                    "city": attraction.location.city,
                    "district": attraction.location.district,
                    "address": attraction.location.address,
                    "category": attraction.category.value,
                    "ticket_price": attraction.ticket_price,
                    "duration_hours": attraction.duration_hours,
                    "description": attraction.description,
                    "opening_hours": attraction.opening_hours,
                    "best_time": attraction.best_time,
                    "tips": attraction.tips,
                }
            )

        df = pd.DataFrame(data)
        file_path = config.get_excel_path("attractions")
        df.to_excel(file_path, index=False)
        logger.info(f"景点数据已保存到: {file_path}")

    def _save_restaurants(self):
        """保存餐厅数据"""
        data = []
        for restaurant in self.restaurants:
            data.append(
                {
                    "name": restaurant.name,
                    "city": restaurant.location.city,
                    "district": restaurant.location.district,
                    "address": restaurant.location.address,
                    "cuisine": restaurant.cuisine.value,
                    "avg_price_per_person": restaurant.avg_price_per_person,
                    "rating": restaurant.rating,
                    "specialties": ",".join(restaurant.specialties),
                    "opening_hours": restaurant.opening_hours,
                    "reservation_required": restaurant.reservation_required,
                    "contact": restaurant.contact,
                }
            )

        df = pd.DataFrame(data)
        file_path = config.get_excel_path("restaurants")
        df.to_excel(file_path, index=False)
        logger.info(f"餐厅数据已保存到: {file_path}")

    def _save_transport(self):
        """保存交通数据"""
        data = []
        for transport in self.transport:
            data.append(
                {
                    "from_city": transport.from_city,
                    "to_city": transport.to_city,
                    "transport_type": transport.transport_type.value,
                    "duration_hours": transport.duration_hours,
                    "price": transport.price,
                    "frequency": transport.frequency,
                    "departure_time": transport.departure_time,
                    "arrival_time": transport.arrival_time,
                    "company": transport.company,
                }
            )

        df = pd.DataFrame(data)
        file_path = config.get_excel_path("transport")
        df.to_excel(file_path, index=False)
        logger.info(f"交通数据已保存到: {file_path}")

    # 公共接口方法
    def search_hotels(self, city: str, **filters) -> List[Hotel]:
        """搜索酒店"""
        results = [h for h in self.hotels if h.location.city == city]

        if "max_price" in filters and filters["max_price"] is not None:
            results = [h for h in results if h.price_per_night <= filters["max_price"]]

        if "min_rating" in filters and filters["min_rating"] is not None:
            results = [h for h in results if h.rating >= filters["min_rating"]]

        return results

    def search_attractions(self, city: str, **filters) -> List[Attraction]:
        """搜索景点"""
        results = [a for a in self.attractions if a.location.city == city]

        if "category" in filters and filters["category"] is not None:
            results = [a for a in results if a.category == filters["category"]]

        return results

    def search_restaurants(self, city: str, **filters) -> List[Restaurant]:
        """搜索餐厅"""
        results = [r for r in self.restaurants if r.location.city == city]

        if "cuisine" in filters and filters["cuisine"] is not None:
            results = [r for r in results if r.cuisine == filters["cuisine"]]

        if "max_price" in filters and filters["max_price"] is not None:
            results = [
                r for r in results if r.avg_price_per_person <= filters["max_price"]
            ]

        return results

    def search_transport(self, from_city: str, to_city: str) -> List[TransportOption]:
        """搜索交通方式"""
        return [
            t
            for t in self.transport
            if t.from_city == from_city and t.to_city == to_city
        ]

    def get_city_info(self, city: str) -> Dict[str, Any]:
        """获取城市综合信息"""
        hotels = self.search_hotels(city)
        attractions = self.search_attractions(city)
        restaurants = self.search_restaurants(city)

        return {
            "city": city,
            "hotels_count": len(hotels),
            "attractions_count": len(attractions),
            "restaurants_count": len(restaurants),
            "avg_hotel_price": (
                sum(h.price_per_night for h in hotels) / len(hotels) if hotels else 0
            ),
            "avg_attraction_price": (
                sum(a.ticket_price for a in attractions) / len(attractions)
                if attractions
                else 0
            ),
            "avg_restaurant_price": (
                sum(r.avg_price_per_person for r in restaurants) / len(restaurants)
                if restaurants
                else 0
            ),
        }


# 全局实例
travel_data_manager = TravelDataManager()
