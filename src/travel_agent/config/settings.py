"""Travel Agent Configuration Settings"""

import os
from pathlib import Path
from typing import Dict, Any, List
from dataclasses import dataclass
from enum import Enum


class Region(Enum):
    """地区枚举"""

    DOMESTIC = "domestic"  # 国内
    ASIA = "asia"  # 亚洲
    EUROPE = "europe"  # 欧洲
    NORTH_AMERICA = "north_america"  # 北美
    SOUTH_AMERICA = "south_america"  # 南美
    AFRICA = "africa"  # 非洲
    OCEANIA = "oceania"  # 大洋洲


class Currency(Enum):
    """货币枚举"""

    CNY = "CNY"  # 人民币
    USD = "USD"  # 美元
    EUR = "EUR"  # 欧元
    JPY = "JPY"  # 日元
    KRW = "KRW"  # 韩元
    GBP = "GBP"  # 英镑
    AUD = "AUD"  # 澳元
    CAD = "CAD"  # 加元


@dataclass
class CityInfo:
    """城市信息"""

    name: str
    region: Region
    country: str
    currency: Currency
    timezone: str
    language: str
    visa_required: bool = False
    visa_type: str = ""
    popular_season: List[str] = None
    avg_temperature: Dict[str, float] = None


@dataclass
class TravelAgentConfig:
    """旅行代理配置类"""

    # 基础配置
    app_name: str = "智能旅行规划助手"
    version: str = "1.0.0"
    debug: bool = True

    # 数据配置
    data_dir: str = "travel_data"
    excel_files: Dict[str, str] = None

    # LLM配置
    default_model: str = "gpt-4o"
    temperature: float = 0.7
    max_tokens: int = 2000

    # 旅行配置
    default_origin_city: str = "北京"
    supported_cities: List[CityInfo] = None
    max_trip_days: int = 30
    min_budget: float = 500.0

    # 预算分配比例
    budget_ratios: Dict[str, float] = None

    # 国际化配置
    default_currency: Currency = Currency.CNY
    supported_currencies: List[Currency] = None
    exchange_rates: Dict[str, float] = None

    def __post_init__(self):
        """初始化后处理"""
        if self.excel_files is None:
            self.excel_files = {
                "hotels": "hotels.xlsx",
                "attractions": "attractions.xlsx",
                "restaurants": "restaurants.xlsx",
                "transport": "transport.xlsx",
            }

        if self.supported_cities is None:
            self.supported_cities = self._init_cities()

        if self.budget_ratios is None:
            self.budget_ratios = {
                "hotel": 0.4,  # 住宿40%
                "restaurant": 0.25,  # 餐饮25%
                "attractions": 0.15,  # 景点15%
                "transport": 0.15,  # 交通15%
                "other": 0.05,  # 其他5%
            }

        if self.supported_currencies is None:
            self.supported_currencies = [
                Currency.CNY,
                Currency.USD,
                Currency.EUR,
                Currency.JPY,
                Currency.KRW,
                Currency.GBP,
                Currency.AUD,
                Currency.CAD,
            ]

        if self.exchange_rates is None:
            self.exchange_rates = {
                "USD": 7.2,  # 1 USD = 7.2 CNY
                "EUR": 7.8,  # 1 EUR = 7.8 CNY
                "JPY": 0.048,  # 1 JPY = 0.048 CNY
                "KRW": 0.0054,  # 1 KRW = 0.0054 CNY
                "GBP": 9.1,  # 1 GBP = 9.1 CNY
                "AUD": 4.8,  # 1 AUD = 4.8 CNY
                "CAD": 5.3,  # 1 CAD = 5.3 CNY
            }

    def _init_cities(self) -> List[CityInfo]:
        """初始化城市信息"""
        cities = []

        # 国内城市
        domestic_cities = [
            ("北京", "中国", "Asia/Shanghai", ["春季", "秋季"]),
            ("上海", "中国", "Asia/Shanghai", ["春季", "秋季"]),
            ("广州", "中国", "Asia/Shanghai", ["秋季", "冬季"]),
            ("深圳", "中国", "Asia/Shanghai", ["秋季", "冬季"]),
            ("杭州", "中国", "Asia/Shanghai", ["春季", "秋季"]),
            ("成都", "中国", "Asia/Shanghai", ["春季", "秋季"]),
            ("西安", "中国", "Asia/Shanghai", ["春季", "秋季"]),
            ("南京", "中国", "Asia/Shanghai", ["春季", "秋季"]),
            ("苏州", "中国", "Asia/Shanghai", ["春季", "秋季"]),
            ("青岛", "中国", "Asia/Shanghai", ["夏季", "秋季"]),
            ("厦门", "中国", "Asia/Shanghai", ["春季", "秋季"]),
            ("大连", "中国", "Asia/Shanghai", ["夏季", "秋季"]),
        ]

        for name, country, timezone, seasons in domestic_cities:
            cities.append(
                CityInfo(
                    name=name,
                    region=Region.DOMESTIC,
                    country=country,
                    currency=Currency.CNY,
                    timezone=timezone,
                    language="中文",
                    visa_required=False,
                    popular_season=seasons,
                    avg_temperature={"春季": 15, "夏季": 25, "秋季": 18, "冬季": 5},
                )
            )

        # 国际城市
        international_cities = [
            # 亚洲
            (
                "东京",
                "日本",
                "Asia/Tokyo",
                ["春季", "秋季"],
                Currency.JPY,
                "日语",
                True,
                "旅游签证",
            ),
            (
                "首尔",
                "韩国",
                "Asia/Seoul",
                ["春季", "秋季"],
                Currency.KRW,
                "韩语",
                True,
                "旅游签证",
            ),
            (
                "新加坡",
                "新加坡",
                "Asia/Singapore",
                ["全年"],
                Currency.USD,
                "英语",
                True,
                "旅游签证",
            ),
            (
                "曼谷",
                "泰国",
                "Asia/Bangkok",
                ["11月-4月"],
                Currency.USD,
                "泰语",
                True,
                "落地签",
            ),
            (
                "吉隆坡",
                "马来西亚",
                "Asia/Kuala_Lumpur",
                ["全年"],
                Currency.USD,
                "马来语",
                True,
                "旅游签证",
            ),
            # 欧洲
            (
                "巴黎",
                "法国",
                "Europe/Paris",
                ["春季", "秋季"],
                Currency.EUR,
                "法语",
                True,
                "申根签证",
            ),
            (
                "伦敦",
                "英国",
                "Europe/London",
                ["春季", "夏季"],
                Currency.GBP,
                "英语",
                True,
                "旅游签证",
            ),
            (
                "罗马",
                "意大利",
                "Europe/Rome",
                ["春季", "秋季"],
                Currency.EUR,
                "意大利语",
                True,
                "申根签证",
            ),
            (
                "柏林",
                "德国",
                "Europe/Berlin",
                ["春季", "秋季"],
                Currency.EUR,
                "德语",
                True,
                "申根签证",
            ),
            (
                "阿姆斯特丹",
                "荷兰",
                "Europe/Amsterdam",
                ["春季", "夏季"],
                Currency.EUR,
                "荷兰语",
                True,
                "申根签证",
            ),
            # 北美
            (
                "纽约",
                "美国",
                "America/New_York",
                ["春季", "秋季"],
                Currency.USD,
                "英语",
                True,
                "B1/B2签证",
            ),
            (
                "洛杉矶",
                "美国",
                "America/Los_Angeles",
                ["全年"],
                Currency.USD,
                "英语",
                True,
                "B1/B2签证",
            ),
            (
                "多伦多",
                "加拿大",
                "America/Toronto",
                ["夏季", "秋季"],
                Currency.CAD,
                "英语",
                True,
                "旅游签证",
            ),
            (
                "温哥华",
                "加拿大",
                "America/Vancouver",
                ["夏季", "秋季"],
                Currency.CAD,
                "英语",
                True,
                "旅游签证",
            ),
            # 大洋洲
            (
                "悉尼",
                "澳大利亚",
                "Australia/Sydney",
                ["春季", "秋季"],
                Currency.AUD,
                "英语",
                True,
                "旅游签证",
            ),
            (
                "墨尔本",
                "澳大利亚",
                "Australia/Melbourne",
                ["春季", "秋季"],
                Currency.AUD,
                "英语",
                True,
                "旅游签证",
            ),
        ]

        for (
            name,
            country,
            timezone,
            seasons,
            currency,
            language,
            visa_required,
            visa_type,
        ) in international_cities:
            cities.append(
                CityInfo(
                    name=name,
                    region=(
                        Region.DOMESTIC
                        if country == "中国"
                        else (
                            Region.ASIA
                            if "Asia" in timezone
                            else (
                                Region.EUROPE
                                if "Europe" in timezone
                                else (
                                    Region.NORTH_AMERICA
                                    if "America" in timezone
                                    else Region.OCEANIA
                                )
                            )
                        )
                    ),
                    country=country,
                    currency=currency,
                    timezone=timezone,
                    language=language,
                    visa_required=visa_required,
                    visa_type=visa_type,
                    popular_season=seasons,
                    avg_temperature={"春季": 18, "夏季": 28, "秋季": 20, "冬季": 8},
                )
            )

        return cities

    @property
    def data_path(self) -> Path:
        """获取数据目录路径"""
        return Path(self.data_dir)

    def get_excel_path(self, file_type: str) -> Path:
        """获取Excel文件路径"""
        if file_type not in self.excel_files:
            raise ValueError(f"不支持的文件类型: {file_type}")
        return self.data_path / self.excel_files[file_type]

    def validate_city(self, city: str) -> bool:
        """验证城市是否支持"""
        return any(c.name == city for c in self.supported_cities)

    def get_city_info(self, city: str) -> CityInfo:
        """获取城市详细信息"""
        for city_info in self.supported_cities:
            if city_info.name == city:
                return city_info
        raise ValueError(f"不支持的城市: {city}")

    def get_cities_by_region(self, region: Region) -> List[CityInfo]:
        """根据地区获取城市列表"""
        return [city for city in self.supported_cities if city.region == region]

    def get_domestic_cities(self) -> List[CityInfo]:
        """获取国内城市列表"""
        return self.get_cities_by_region(Region.DOMESTIC)

    def get_international_cities(self) -> List[CityInfo]:
        """获取国际城市列表"""
        return [
            city for city in self.supported_cities if city.region != Region.DOMESTIC
        ]

    def get_budget_ratio(self, category: str) -> float:
        """获取预算分配比例"""
        return self.budget_ratios.get(category, 0.0)

    def convert_currency(
        self,
        amount: float,
        from_currency: Currency,
        to_currency: Currency = Currency.CNY,
    ) -> float:
        """货币转换"""
        if from_currency == to_currency:
            return amount

        if from_currency == Currency.CNY:
            # 从人民币转换到其他货币
            for currency, rate in self.exchange_rates.items():
                if currency == to_currency.value:
                    return amount / rate
        else:
            # 从其他货币转换到人民币
            for currency, rate in self.exchange_rates.items():
                if currency == from_currency.value:
                    return amount * rate

        return amount

    def get_visa_info(self, city: str) -> Dict[str, Any]:
        """获取签证信息"""
        city_info = self.get_city_info(city)
        return {
            "required": city_info.visa_required,
            "type": city_info.visa_type,
            "country": city_info.country,
            "language": city_info.language,
            "currency": city_info.currency.value,
        }


# 全局配置实例
config = TravelAgentConfig()


# 环境变量覆盖
def load_env_config():
    """从环境变量加载配置"""
    config.debug = os.getenv("TRAVEL_AGENT_DEBUG", "true").lower() == "true"
    config.default_model = os.getenv("TRAVEL_AGENT_MODEL", config.default_model)
    config.data_dir = os.getenv("TRAVEL_AGENT_DATA_DIR", config.data_dir)


# 加载环境配置
load_env_config()
