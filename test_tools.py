#!/usr/bin/env python3
"""工具功能测试脚本"""

import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from travel_agent.tools import (
    search_flights,
    search_hotels,
    search_attractions,
    convert_currency,
    get_current_weather,
    search_knowledge,
    get_travel_tips,
    get_visa_info,
)


def test_flights():
    """测试航班工具"""
    print("🛫 测试航班工具")
    print("=" * 50)

    # 搜索航班
    flights = search_flights("北京", "上海", "2025-01-27")
    print(f"找到 {len(flights)} 个航班")
    for flight in flights:
        print(
            f"  {flight['airline']} {flight['flight_number']}: {flight['departure_time']} - {flight['arrival_time']}"
        )


def test_hotels():
    """测试酒店工具"""
    print("\n🏨 测试酒店工具")
    print("=" * 50)

    # 搜索酒店
    hotels = search_hotels("北京", "2025-01-27", "2025-01-28")
    print(f"找到 {len(hotels)} 个酒店")
    for hotel in hotels:
        print(f"  {hotel['name']}: {hotel['price_per_night']} {hotel['currency']}/晚")


def test_attractions():
    """测试景点工具"""
    print("\n🏛️ 测试景点工具")
    print("=" * 50)

    # 搜索景点
    attractions = search_attractions("北京")
    print(f"找到 {len(attractions)} 个景点")
    for attr in attractions:
        print(
            f"  {attr['name']}: {attr['category']}, 门票 {attr['ticket_price']} {attr['currency']}"
        )


def test_currency():
    """测试汇率工具"""
    print("\n💱 测试汇率工具")
    print("=" * 50)

    # 货币转换
    usd_to_cny = convert_currency(100, "USD", "CNY")
    eur_to_cny = convert_currency(100, "EUR", "CNY")
    jpy_to_cny = convert_currency(10000, "JPY", "CNY")

    print(f"100 USD = {usd_to_cny} CNY")
    print(f"100 EUR = {eur_to_cny} CNY")
    print(f"10000 JPY = {jpy_to_cny} CNY")


def test_weather():
    """测试天气工具"""
    print("\n🌤️ 测试天气工具")
    print("=" * 50)

    # 获取天气
    weather = get_current_weather("北京")
    if weather:
        print(f"北京天气: {weather['weather_condition']}")
        print(f"温度: {weather['temperature_low']}°C - {weather['temperature_high']}°C")
        print(f"湿度: {weather['humidity']}%")


def test_rag():
    """测试知识库工具"""
    print("\n📚 测试知识库工具")
    print("=" * 50)

    # 搜索知识
    knowledge = search_knowledge("北京旅行")
    print(f"找到 {len(knowledge)} 条相关知识")
    for item in knowledge:
        print(f"  {item['title']}: {item['content'][:50]}...")

    # 获取旅行贴士
    tips = get_travel_tips("北京")
    print(f"\n北京旅行贴士:")
    for tip in tips:
        print(f"  {tip['title']}")

    # 获取签证信息
    visa = get_visa_info("日本")
    if visa:
        print(f"\n日本签证信息:")
        print(f"  类型: {visa['签证类型']}")
        print(f"  要求: {visa['申请要求'][:50]}...")


def main():
    """主函数"""
    print("🧳 旅行助手工具测试")
    print("=" * 60)

    try:
        test_flights()
        test_hotels()
        test_attractions()
        test_currency()
        test_weather()
        test_rag()

        print("\n✅ 所有工具测试完成！")

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
