"""Travel Agent Configuration Settings"""

import os
from pathlib import Path
from typing import Dict, Any, List
from dataclasses import dataclass
from enum import Enum


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
    default_model: str = "gpt-4.1"
    temperature: float = 0.7
    max_tokens: int = 2000

    # 旅行配置
    default_origin_city: str = "北京"
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

    def get_budget_ratio(self, category: str) -> float:
        """获取预算分配比例"""
        return self.budget_ratios.get(category, 0.0)


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
