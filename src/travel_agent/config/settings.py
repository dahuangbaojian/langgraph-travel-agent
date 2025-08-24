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
        """初始化城市信息 - 支持所有城市"""
        # 不再硬编码城市列表，而是动态支持所有城市
        return []

    def add_city(self, city_info: CityInfo) -> None:
        """动态添加城市"""
        self.supported_cities.append(city_info)

    def get_or_create_city(self, city_name: str, country: str = None) -> CityInfo:
        """获取或创建城市信息"""
        # 先查找现有城市
        for city in self.supported_cities:
            if city.name.lower() == city_name.lower():
                return city

        # 如果城市不存在，动态创建
        if country is None:
            # 如果没有指定国家，尝试智能识别
            country = self._detect_country(city_name)

        # 创建新的城市信息
        new_city = self._create_city_info(city_name, country)
        self.supported_cities.append(new_city)
        return new_city

    def _detect_country(self, city_name: str) -> str:
        """智能识别城市所属国家"""
        # 这里可以集成地理API来识别城市所属国家
        # 暂时使用简单的规则
        chinese_cities = [
            "北京",
            "上海",
            "广州",
            "深圳",
            "杭州",
            "成都",
            "西安",
            "南京",
            "苏州",
            "青岛",
            "厦门",
            "大连",
        ]
        if city_name in chinese_cities:
            return "中国"

        # 可以扩展更多规则或集成外部API
        return "未知"

    def _create_city_info(self, city_name: str, country: str) -> CityInfo:
        """根据城市和国家创建城市信息"""
        # 根据国家设置默认值
        if country == "中国":
            region = Region.DOMESTIC
            currency = Currency.CNY
            language = "中文"
            visa_required = False
            visa_type = ""
            timezone = "Asia/Shanghai"
        else:
            # 国际城市
            region = self._detect_region_by_country(country)
            currency = self._detect_currency_by_country(country)
            language = self._detect_language_by_country(country)
            visa_required = True
            visa_type = "旅游签证"
            timezone = self._detect_timezone_by_country(country)

        return CityInfo(
            name=city_name,
            region=region,
            country=country,
            currency=currency,
            timezone=timezone,
            language=language,
            visa_required=visa_required,
            visa_type=visa_type,
            popular_season=["春季", "秋季"],  # 默认最佳季节
            avg_temperature={"春季": 18, "夏季": 28, "秋季": 20, "冬季": 8},
        )

    def _detect_region_by_country(self, country: str) -> Region:
        """根据国家检测地区"""
        asia_countries = [
            "日本",
            "韩国",
            "新加坡",
            "泰国",
            "马来西亚",
            "越南",
            "印度",
            "印度尼西亚",
            "菲律宾",
        ]
        europe_countries = [
            "法国",
            "德国",
            "意大利",
            "英国",
            "荷兰",
            "西班牙",
            "葡萄牙",
            "瑞士",
            "奥地利",
            "比利时",
        ]
        north_america_countries = ["美国", "加拿大", "墨西哥"]
        south_america_countries = ["巴西", "阿根廷", "智利", "秘鲁", "哥伦比亚"]
        africa_countries = ["南非", "埃及", "摩洛哥", "肯尼亚", "坦桑尼亚"]
        oceania_countries = ["澳大利亚", "新西兰", "斐济"]

        if country in asia_countries:
            return Region.ASIA
        elif country in europe_countries:
            return Region.EUROPE
        elif country in north_america_countries:
            return Region.NORTH_AMERICA
        elif country in south_america_countries:
            return Region.SOUTH_AMERICA
        elif country in africa_countries:
            return Region.AFRICA
        elif country in oceania_countries:
            return Region.OCEANIA
        else:
            return Region.ASIA  # 默认亚洲

    def _detect_currency_by_country(self, country: str) -> Currency:
        """根据国家检测货币"""
        currency_map = {
            "日本": Currency.JPY,
            "韩国": Currency.KRW,
            "新加坡": Currency.USD,
            "泰国": Currency.USD,
            "马来西亚": Currency.USD,
            "法国": Currency.EUR,
            "德国": Currency.EUR,
            "意大利": Currency.EUR,
            "英国": Currency.GBP,
            "荷兰": Currency.EUR,
            "美国": Currency.USD,
            "加拿大": Currency.CAD,
            "澳大利亚": Currency.AUD,
            "新西兰": Currency.AUD,
        }
        return currency_map.get(country, Currency.USD)  # 默认美元

    def _detect_language_by_country(self, country: str) -> str:
        """根据国家检测语言"""
        language_map = {
            "日本": "日语",
            "韩国": "韩语",
            "新加坡": "英语",
            "泰国": "泰语",
            "马来西亚": "马来语",
            "法国": "法语",
            "德国": "德语",
            "意大利": "意大利语",
            "英国": "英语",
            "荷兰": "荷兰语",
            "美国": "英语",
            "加拿大": "英语",
            "澳大利亚": "英语",
            "新西兰": "英语",
        }
        return language_map.get(country, "英语")  # 默认英语

    def _detect_timezone_by_country(self, country: str) -> str:
        """根据国家检测时区"""
        timezone_map = {
            "日本": "Asia/Tokyo",
            "韩国": "Asia/Seoul",
            "新加坡": "Asia/Singapore",
            "泰国": "Asia/Bangkok",
            "马来西亚": "Asia/Kuala_Lumpur",
            "法国": "Europe/Paris",
            "德国": "Europe/Berlin",
            "意大利": "Europe/Rome",
            "英国": "Europe/London",
            "荷兰": "Europe/Amsterdam",
            "美国": "America/New_York",
            "加拿大": "America/Toronto",
            "澳大利亚": "Australia/Sydney",
            "新西兰": "Pacific/Auckland",
        }
        return timezone_map.get(country, "UTC")  # 默认UTC

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
        """验证城市是否支持 - 现在支持所有城市"""
        return True  # 支持所有城市

    def get_city_info(self, city: str) -> CityInfo:
        """获取城市详细信息 - 如果城市不存在会自动创建"""
        return self.get_or_create_city(city)

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
