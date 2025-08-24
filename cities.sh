#!/bin/bash

# 城市信息展示脚本
# 作者: 黄建
# 日期: 2025-01-27

echo "🌍 智能旅行规划助手 - 城市信息"
echo "=================================="

# 检查Python环境
if ! command -v python3 &> /dev/null; then
    echo "❌ 错误: 未找到Python3"
    exit 1
fi

# 检查虚拟环境
if [ -d "venv" ]; then
    source venv/bin/activate
fi

echo ""
echo "📊 城市支持信息:"
echo "----------------------------------------"

# 使用Python获取城市统计
python3 -c "
from src.travel_agent.config.settings import config

print('🌍 支持所有国家所有城市！')
print(f'🏠 已加载城市: {len(config.supported_cities)} 个')

if len(config.supported_cities) > 0:
    print('\n📈 地区分布:')
    regions = {}
    for city in config.supported_cities:
        region = city.region.value
        regions[region] = regions.get(region, 0) + 1

    for region, count in sorted(regions.items()):
        region_name = {
            'domestic': '🏠 国内',
            'asia': '🌏 亚洲',
            'europe': '🇪🇺 欧洲', 
            'north_america': '🇺🇸 北美',
            'south_america': '🇧🇷 南美',
            'africa': '🌍 非洲',
            'oceania': '🇦🇺 大洋洲'
        }.get(region, region)
        print(f'   {region_name}: {count} 个城市')
else:
    print('📝 城市信息会在使用时动态创建')
"

echo ""
echo "🏠 国内城市列表:"
echo "----------------------------------------"
python3 -c "
from src.travel_agent.config.settings import config

domestic = config.get_domestic_cities()
for city in domestic:
    print(f'   • {city.name} ({city.country})')
    print(f'     时区: {city.timezone} | 语言: {city.language}')
    print(f'     最佳季节: {", ".join(city.popular_season)}')
    print()
"

echo "🌏 国际城市列表:"
echo "----------------------------------------"
python3 -c "
from src.travel_agent.config.settings import config

international = config.get_international_cities()
for city in international:
    visa_info = '需要签证' if city.visa_required else '免签'
    print(f'   • {city.name} ({city.country})')
    print(f'     时区: {city.timezone} | 语言: {city.language}')
    print(f'     货币: {city.currency.value} | 签证: {visa_info}')
    if city.visa_required and city.visa_type:
        print(f'     签证类型: {city.visa_type}')
    print(f'     最佳季节: {", ".join(city.popular_season)}')
    print()
"

echo "💱 支持货币:"
echo "----------------------------------------"
python3 -c "
from src.travel_agent.config.settings import config

for currency in config.supported_currencies:
    print(f'   • {currency.value}')
"

echo ""
echo "💡 使用提示:"
echo "   • 查看特定城市信息: python3 -c \"from src.travel_agent.config.settings import config; city = config.get_city_info('东京'); print(f'城市: {city.name}, 国家: {city.country}, 货币: {city.currency.value}')\""
echo "   • 获取签证信息: python3 -c \"from src.travel_agent.config.settings import config; print(config.get_visa_info('巴黎'))\""
echo "   • 货币转换: python3 -c \"from src.travel_agent.config.settings import config; print(f'100 USD = {config.convert_currency(100, config.supported_currencies[1])} CNY')\""
