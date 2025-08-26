"""Travel Agent Configuration Settings - 智能化版本"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum
from datetime import datetime

# 导入LLM和Prompt
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage

from ..core.prompts import (
    BUDGET_RATIO_PROMPT,
    EXCHANGE_RATE_PROMPT,
    CITY_VALIDATION_PROMPT,
)

logger = logging.getLogger(__name__)


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
    """旅行代理配置类 - 智能化版本"""

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
    max_trip_days: int = 30
    min_budget: float = 500.0

    # 预算分配比例 - 动态生成
    budget_ratios: Optional[Dict[str, float]] = None

    # 国际化配置
    default_currency: Currency = Currency.CNY
    supported_currencies: List[Currency] = None
    exchange_rates: Optional[Dict[str, float]] = None

    # LLM实例
    llm: Optional[ChatOpenAI] = None

    def __post_init__(self):
        """初始化后处理"""
        # LLM实例将在需要时延迟创建
        # 基础文件配置 - 现在使用动态数据加载

        # 基础文件配置 - 现在使用动态数据加载
        if self.excel_files is None:
            self.excel_files = {}  # 动态加载真实数据文件

        # 支持货币列表
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

        # 预算分配和汇率将在需要时动态生成

    @property
    def llm_instance(self):
        """延迟创建LLM实例"""
        if self.llm is None:
            try:
                self.llm = ChatOpenAI(
                    model=self.default_model,
                    temperature=self.temperature,
                    max_tokens=self.max_tokens,
                    openai_api_base=os.getenv("OPENAI_BASE_URL"),
                )
            except Exception as e:
                logger.warning(f"创建LLM实例失败: {e}")
                return None
        return self.llm

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

    async def generate_budget_ratios(
        self, travel_info: Dict[str, Any]
    ) -> Dict[str, float]:
        """使用LLM智能生成预算分配比例"""
        try:
            prompt = BUDGET_RATIO_PROMPT.format(
                travel_info=travel_info,
                destination=travel_info.get("destination", "未知"),
                budget_level=travel_info.get("budget_level", "中等"),
                duration_days=travel_info.get("duration_days", 3),
                people_count=travel_info.get("people_count", 2),
            )

            llm = self.llm_instance
            if llm is None:
                raise Exception("LLM实例不可用")
            response = llm.invoke([HumanMessage(content=prompt)])
            budget_ratios = json.loads(response.content.strip())

            # 验证比例总和
            total_ratio = sum(
                budget_ratios.get(k, 0)
                for k in ["hotel", "restaurant", "attractions", "transport", "other"]
            )
            if abs(total_ratio - 1.0) > 0.01:
                logger.warning(f"预算比例总和不为1.0: {total_ratio}，进行标准化")
                # 标准化比例
                for key in ["hotel", "restaurant", "attractions", "transport", "other"]:
                    budget_ratios[key] = budget_ratios.get(key, 0) / total_ratio

            self.budget_ratios = budget_ratios
            logger.info(f"智能生成预算分配比例: {budget_ratios}")
            return budget_ratios

        except Exception as e:
            logger.error(f"智能生成预算比例失败: {e}，使用默认比例")
            # 回退到默认比例
            default_ratios = {
                "hotel": 0.4,
                "restaurant": 0.25,
                "attractions": 0.15,
                "transport": 0.15,
                "other": 0.05,
            }
            self.budget_ratios = default_ratios
            return default_ratios

    async def generate_exchange_rates(self) -> Dict[str, float]:
        """使用LLM智能生成汇率"""
        try:
            current_time = datetime.now().strftime("%Y年%m月%d日 %H:%M")

            exchange_rates = {}
            for currency in self.supported_currencies:
                if currency == Currency.CNY:
                    continue

                prompt = EXCHANGE_RATE_PROMPT.format(
                    currency=currency.value,
                    current_time=current_time,
                    market_trend="稳定",
                )

                llm = self.llm_instance
                if llm is None:
                    raise Exception("LLM实例不可用")
                response = llm.invoke([HumanMessage(content=prompt)])
                rate_info = json.loads(response.content.strip())

                exchange_rates[currency.value] = rate_info.get("estimated_rate", 0.0)
                logger.info(
                    f"智能生成汇率 {currency.value}: {rate_info.get('estimated_rate', 0.0)}"
                )

            self.exchange_rates = exchange_rates
            return exchange_rates

        except Exception as e:
            logger.error(f"智能生成汇率失败: {e}，使用默认汇率")
            # 回退到默认汇率
            default_rates = {
                "USD": 7.2,
                "EUR": 7.8,
                "JPY": 0.048,
                "KRW": 0.0054,
                "GBP": 9.1,
                "AUD": 4.8,
                "CAD": 5.3,
            }
            self.exchange_rates = default_rates
            return default_rates

    async def validate_city_intelligent(
        self, city_name: str, user_requirements: str = "", travel_type: str = "leisure"
    ) -> Dict[str, Any]:
        """使用LLM智能验证城市信息"""
        try:
            prompt = CITY_VALIDATION_PROMPT.format(
                city_name=city_name,
                user_requirements=user_requirements,
                travel_type=travel_type,
            )

            llm = self.llm_instance
            if llm is None:
                raise Exception("LLM实例不可用")
            response = llm.invoke([HumanMessage(content=prompt)])
            validation_result = json.loads(response.content.strip())

            logger.info(f"智能城市验证: {city_name} -> {validation_result}")
            return validation_result

        except Exception as e:
            logger.error(f"智能城市验证失败: {e}")
            return {
                "is_valid": True,
                "city_type": "unknown",
                "country": "未知",
                "region": "未知",
                "timezone": "未知",
                "best_season": "全年",
                "travel_tips": ["建议提前了解当地情况"],
                "safety_level": "一般",
                "cost_level": "中等",
            }

    def get_budget_ratio(self, category: str) -> float:
        """获取预算分配比例"""
        if self.budget_ratios is None:
            logger.warning("预算比例未初始化，请先调用 generate_budget_ratios")
            return 0.0
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
