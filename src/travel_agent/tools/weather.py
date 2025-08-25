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


async def get_weather_info(city: str) -> Optional[str]:
    """获取格式化的天气信息字符串"""
    try:
        weather = weather_tool.get_current_weather(city)
        if weather:
            weather_str = (
                f"📍 {weather.city}\n"
                f"🌡️ 温度: {weather.temperature_low:.1f}°C - {weather.temperature_high:.1f}°C\n"
                f"☁️ 天气: {weather.weather_condition}\n"
                f"💧 湿度: {weather.humidity}%\n"
                f"💨 风速: {weather.wind_speed} km/h"
            )
            return weather_str
        return None
    except Exception as e:
        logger.error(f"获取天气信息失败: {e}")
        return None
