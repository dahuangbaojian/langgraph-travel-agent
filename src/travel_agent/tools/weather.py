"""天气查询工具"""

import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class WeatherInfo:
    """天气信息"""

    city: str
    date: str
    temperature_high: float
    temperature_low: float
    weather_condition: str
    humidity: int
    wind_speed: float


class WeatherTool:
    """天气查询工具"""

    def __init__(self):
        pass

    def get_current_weather(self, city: str) -> Optional[WeatherInfo]:
        """获取当前天气"""
        # 模拟天气数据
        weather = WeatherInfo(
            city=city,
            date=datetime.now().strftime("%Y-%m-%d"),
            temperature_high=25.0,
            temperature_low=15.0,
            weather_condition="晴朗",
            humidity=60,
            wind_speed=15.0,
        )
        return weather


# 全局实例
weather_tool = WeatherTool()


def get_current_weather(city: str) -> Optional[Dict[str, Any]]:
    """获取当前天气的便捷函数"""
    weather = weather_tool.get_current_weather(city)
    return weather.__dict__ if weather else None
